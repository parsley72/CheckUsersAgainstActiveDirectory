#! /usr/bin/python3

import argparse
from helpers import device_flow_session, api_endpoint
import pprint
import requests

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
    argparser = argparse.ArgumentParser(description='Check Keen users against ActiveDirectory.')
    argparser.add_argument('-o', '--organisation', help='Keen organisation', required=True)
    argparser.add_argument('-a', '--authorization', help='Token for Keen', required=True)
    argparser.add_argument('-v', '--verbose', type=str2bool, help='Verbose')
    return argparser


if __name__ == "__main__":
    argparser = build_argparser()
    args = argparser.parse_args()

    GRAPH_SESSION = device_flow_session(config.CLIENT_ID, True)
    user_profile = GRAPH_SESSION.get(api_endpoint('me'))
    # print(28*' ' + f'<Response [{user_profile.status_code}]>', f'bytes returned: {len(user_profile.text)}\n')
    if not user_profile.ok:
        pprint.pprint(user_profile.json()) # display error
        exit()

    headers = {'Content-Type': 'application/json', 'Authorization': args.authorization}
    response = requests.get('https://api.keen.io/3.0/organizations/' + args.organisation + '/projects', json={}, headers = headers)
    projects = response.json()
    for project in projects:
        print('Project: ' + project['name'])
        if 'users' in project:
            for user in project['users']:
                # print(user['email'])
                user_email = user['email']

                search_response = GRAPH_SESSION.get(api_endpoint('me/people/?$search="' + user_email + '"'))
                search_data = search_response.json()
                if not search_response.ok:
                    pprint.pprint(search_data) # display error
                elif len(search_data['value']) == 0:
                        if args.verbose:
                            print('NOT FOUND: ' + user_email)
                        else:
                            print(user_email)
                else:
                    for person in search_data['value']:
                        if 'userPrincipalName' in person:
                            user_principal_name = person['userPrincipalName'] or ''
                            if user_principal_name != '':
                                # pprint.pprint(person)
                                job_title = person['jobTitle'] or 'None'
                                office_location = person['officeLocation'] or 'None'
                                print('FOUND: ' + person['userPrincipalName'] + ', ' + job_title + ', ' + office_location)
                        else:
                            print('userPrincipalName not found for ' + user_email)
