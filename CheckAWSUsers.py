#! /usr/bin/python3

import argparse
import boto3
import datetime
from dateutil.tz import tzutc
from helpers import device_flow_session, api_endpoint
import pprint
import re
from humanize import naturaltime

import config


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def build_argparser():
    argparser = argparse.ArgumentParser(description='Check AWS users against ActiveDirectory.')
    argparser.add_argument('-p', '--profile', help='Profile to use')
    argparser.add_argument('-v', '--verbose', type=str2bool, help='Verbose')
    return argparser


def search_activedirectory(session, search_string, results_array):
    search_response = session.get(api_endpoint(search_string))
    search_data = search_response.json()
    if not search_response.ok:
        pprint.pprint(search_data) # display error
        return False

    bMatch = False
    for person in search_data['value']:
        if 'userPrincipalName' in person:
            user_principal_name = person['userPrincipalName'] or ''
            if user_principal_name != '':
                bMatch = True
                # pprint.pprint(person)
                job_title = person['jobTitle'] or 'None'
                office_location = person['officeLocation'] or 'None'
                result = '    ' + person['userPrincipalName'] + ', ' + job_title + ', ' + office_location
                results_array.append(result)
    return bMatch


if __name__ == "__main__":
    argparser = build_argparser()
    args = argparser.parse_args()

    if args.profile == None:
        iam = boto3.client('iam')
    else:
        profile = boto3.session.Session(profile_name=args.profile)
        iam = profile.client('iam')

    GRAPH_SESSION = device_flow_session(config.CLIENT_ID, True)
    user_profile = GRAPH_SESSION.get(api_endpoint('me'))
    # print(28*' ' + f'<Response [{user_profile.status_code}]>', f'bytes returned: {len(user_profile.text)}\n')
    if not user_profile.ok:
        pprint.pprint(user_profile.json()) # display error
        exit()

    now = datetime.datetime.now(tzutc())

    paginator = iam.get_paginator('list_users')
    page_iterator = paginator.paginate()
    for users in page_iterator:
        for user in users['Users']:
            # print('{}'.format(user))
            user_name = user['UserName']
            create_date = user['CreateDate']
            print('UserName = ' + user_name)
            print('  CreateDate = {0} ({1})'.format(create_date, naturaltime(now - create_date)))

            if 'PasswordLastUsed' in user:
                password_last_used = user['PasswordLastUsed']
                print('  PasswordLastUsed = {0} ({1})'.format(password_last_used, naturaltime(now - password_last_used)))

            response = iam.generate_service_last_accessed_details(Arn=user['Arn'])
            job_id = response['JobId']
            response = iam.get_service_last_accessed_details(JobId=job_id)
            # print('generate_service_last_accessed_details(' + user['UserName'] + ') = {}'.format(response))

            last_activity = datetime.datetime(1900, 1, 1, 0, 0, tzinfo = tzutc())
            last_service = ''
            if 'ServicesLastAccessed' in response:
                for service in response['ServicesLastAccessed']:
                    if 'LastAuthenticated' in service:
                        service_name = service['ServiceName']
                        last_authenticated = service['LastAuthenticated']
                        # print('    ServiceName = ' + service_name)
                        # print('    LastAuthenticated = {}'.format(last_authenticated))
                        if last_authenticated > last_activity:
                            last_activity = last_authenticated
                            last_service = service_name

            if last_service != '':
                print('  Last activity = {0} ({1}) - {2}'.format(last_activity, naturaltime(now - last_activity), last_service))
            else:
                print('  Last activity = None')

            print('  Access keys:')
            keys = iam.list_access_keys(UserName=user_name)
            # print(keys)
            if 'AccessKeyMetadata' in keys:
                for key in keys['AccessKeyMetadata']:
                    if key['Status'] == 'Active':
                        key_id = key['AccessKeyId']
                        key_create_date = key['CreateDate']
                        response_key_last_used = iam.get_access_key_last_used(AccessKeyId=key_id)
                        # print('get_access_key_last_used() = {}'.format(response))
                        if 'AccessKeyLastUsed' in response_key_last_used:
                            if 'LastUsedDate' in response_key_last_used['AccessKeyLastUsed']:
                                key_last_used = response_key_last_used['AccessKeyLastUsed']['LastUsedDate']
                                print('    Key = {0}, {1} ({2}) - {3}'.format(key_id, key_last_used, naturaltime(now - key_last_used), response_key_last_used['AccessKeyLastUsed']['ServiceName']))
                            else:
                                print('    Key = {0} never used'.format(key_id))

            user_email = ''
            response_tags = iam.list_user_tags(UserName=user_name)
            if 'Tags' in response_tags:
                for tag in response_tags['Tags']:
                    if tag['Key'] == 'Email':
                        user_email = tag['Value']
                        break

            print('  AD matches:')
            if user_email != '':
                search_response = GRAPH_SESSION.get(api_endpoint('users/' + user_email))
                person = search_response.json()
                if not search_response.ok:
                    if person['error']['code'] == 'Request_ResourceNotFound':
                        print('    NOT FOUND: {}, {}'.format(user_name, user_email))
                    else:
                        pprint.pprint(person) # display error
                else:
                    if 'userPrincipalName' in person:
                        user_principal_name = person['userPrincipalName'] or ''
                        if user_principal_name != '':
                            # pprint.pprint(person)
                            job_title = person['jobTitle'] or 'None'
                            office_location = person['officeLocation'] or 'None'
                            print('    FOUND: ' + person['userPrincipalName'] + ', ' + job_title + ', ' + office_location)
            else:
                if 'admin.' in user_name or 'Admin.' in user_name:
                    search_string = user_name[6:]
                else:
                    search_string = user_name
                if '.' not in search_string:
                    # Insert space before capitals
                    search_string = re.sub(r"([A-Z])", r" \1", search_string).strip()

                results_array = []
                bMatch = search_activedirectory(GRAPH_SESSION, 'me/people/?$search="' + search_string + '"', results_array)
                if bMatch:
                    for result in results_array:
                        print(result)
                else:
                    if '.' in search_string or ' ' in search_string:
                        if '.' in search_string:
                            user_names = search_string.split('.')
                        else:
                            user_names = search_string.split(' ')
                        
                        if len(user_names[1]) > 1:
                            # Try surname (second name)
                            first_search_string = search_string
                            search_string = user_names[1]
                            bMatch = search_activedirectory(GRAPH_SESSION, 'me/people/?$search="' + search_string + '"', results_array)

                            if bMatch:
                                for result in results_array:
                                    print(result)
                            else:
                                if len(user_names[0]) > 1:
                                    # Try first name
                                    second_search_string = search_string
                                    search_string = user_names[0]
                                    bMatch = search_activedirectory(GRAPH_SESSION, 'me/people/?$search="' + search_string + '"', results_array)

                                    if bMatch:
                                        for result in results_array:
                                            print(result)
                                    else:
                                        print('    NO MATCHES for "' + first_search_string + '" or "' + second_search_string + '" or "' + search_string + '"')
                                else:
                                    print('    NO MATCHES for "' + first_search_string + '" or "' + search_string + '"')
                        else:
                            print('    NO MATCHES for "' + search_string + '"')
                    else:
                        print('    NO MATCHES for "' + search_string + '"')
