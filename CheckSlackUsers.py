#! /usr/bin/python3

import argparse
from helpers import device_flow_session, api_endpoint
import pprint
import slack

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
    argparser = argparse.ArgumentParser(description='Check Slack users against ActiveDirectory.')
    argparser.add_argument('-t', '--token', help='Slack token', required=True)
    argparser.add_argument('-c', '--companyemail', help='Filter company email addresses', required=True)
    argparser.add_argument('-v', '--verbose', type=str2bool, help='Verbose')
    return argparser


if __name__ == "__main__":
    argparser = build_argparser()
    args = argparser.parse_args()

    slack_client = slack.WebClient(token=args.token)

    GRAPH_SESSION = device_flow_session(config.CLIENT_ID, True)
    user_profile = GRAPH_SESSION.get(api_endpoint('me'))
    # print(28*' ' + f'<Response [{user_profile.status_code}]>', f'bytes returned: {len(user_profile.text)}\n')
    if not user_profile.ok:
        pprint.pprint(user_profile.json()) # display error
        exit()

    response = slack_client.users_list()
    # print(format(response))
    for member in response['members']:
        # print(format(member))

        if 'email' not in member['profile']:
            if args.verbose:
                print('SKIP: ' + member['name'])
            continue

        member_email = member['profile']['email']

        if member['deleted']:
            if args.verbose:
                print('DELETED: ' + member_email)
            continue

        search_response = GRAPH_SESSION.get(api_endpoint('users/' + member_email))
        person = search_response.json()
        if not search_response.ok:
            if person['error']['code'] == 'Request_ResourceNotFound':
                member_name = member_email.replace(args.companyemail, '')
                member_name = member_name.replace('.', ' ')
                search_response = GRAPH_SESSION.get(api_endpoint('me/people/?$search="' + member_name + '"'))
                search_data = search_response.json()
                if not search_response.ok:
                    pprint.pprint(search_data) # display error
                elif len(search_data['value']) == 0:
                        if args.verbose:
                            print('NOT FOUND: ' + member_email)
                        else:
                            print(member_email)
                else:
                    for person in search_data['value']:
                        if 'userPrincipalName' in person:
                            if args.verbose:
                                user_principal_name = person['userPrincipalName'] or ''
                                if user_principal_name != '':
                                    # pprint.pprint(person)
                                    job_title = person['jobTitle'] or 'None'
                                    office_location = person['officeLocation'] or 'None'
                                    print('FOUND: ' + person['userPrincipalName'] + ', ' + job_title + ', ' + office_location)
                        else:
                            print('INCOMPLETE: userPrincipalName not found for ' + member_email)
            else:
                pprint.pprint(person) # display error
        else:
            if 'userPrincipalName' in person:
                if args.verbose:
                    user_principal_name = person['userPrincipalName'] or ''
                    if user_principal_name != '':
                        # pprint.pprint(person)
                        job_title = person['jobTitle'] or 'None'
                        office_location = person['officeLocation'] or 'None'
                        print('FOUND: ' + person['userPrincipalName'] + ', ' + job_title + ', ' + office_location)
            else:
                print('INCOMPLETE: userPrincipalName not found for ' + member_email)
