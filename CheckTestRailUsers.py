#! /usr/bin/python3

import argparse
from helpers import device_flow_session, api_endpoint
import pprint
from testrail_api import TestRailAPI

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
    argparser = argparse.ArgumentParser(description='Check TestRail users against ActiveDirectory.')
    argparser.add_argument('-s', '--server', help='TestRail server', required=True)
    argparser.add_argument('-u', '--username', help='TestRail username (not email)', required=True)
    argparser.add_argument('-p', '--password', help='TestRail password', required=True)
    argparser.add_argument('-v', '--verbose', type=str2bool, help='Verbose')
    return argparser


if __name__ == "__main__":
    argparser = build_argparser()
    args = argparser.parse_args()

    testrail_client = TestRailAPI(args.server, args.username, args.password)

    GRAPH_SESSION = device_flow_session(config.CLIENT_ID, True)
    user_profile = GRAPH_SESSION.get(api_endpoint('me'))
    if not user_profile.ok:
        pprint.pprint(user_profile.json()) # display error
        exit()

    users = testrail_client.users.get_users()
    # print(format(users))
    for user in users:
        if 'email' not in user:
            if args.verbose:
                print('SKIP: ' + user['name'])
            continue

        user_email = user['email']

        if user['is_active'] == False:
            if args.verbose:
                print('INACTIVE: ' + user_email)
            continue

        search_response = GRAPH_SESSION.get(api_endpoint('users/' + user_email))
        person = search_response.json()
        if not search_response.ok:
            if person['error']['code'] == 'Request_ResourceNotFound':
                if args.verbose:
                    print('NOT FOUND: ' + user_email)
                else:
                    print(user_email)
            else:
                pprint.pprint(person) # display error
        else:
            if 'userPrincipalName' in person:
                user_principal_name = person['userPrincipalName'] or ''
                if user_principal_name != '':
                    # pprint.pprint(person)
                    job_title = person['jobTitle'] or 'None'
                    office_location = person['officeLocation'] or 'None'
                    if args.verbose:
                        print('FOUND: ' + person['userPrincipalName'] + ', ' + job_title + ', ' + office_location)
