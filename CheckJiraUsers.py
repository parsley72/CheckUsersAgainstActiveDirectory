#! /usr/bin/python3

import argparse
from helpers import device_flow_session, api_endpoint
import pprint
from jira import JIRA
import httplib2
import xml.etree.ElementTree as ET
import datetime
import dateutil.parser
from dateutil.tz import tzutc
from humanize import naturaltime
import requests
import json

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
    argparser = argparse.ArgumentParser(description='Check Jira users against ActiveDirectory.')
    argparser.add_argument('-s', '--server', help='Jira server', required=True)
    argparser.add_argument('-u', '--username', help='Jira username (not email)', required=True)
    argparser.add_argument('-p', '--password', help='Jira password', required=True)
    argparser.add_argument('-o', '--company', help='Only show company email addresses')
    argparser.add_argument('-v', '--verbose', type=str2bool, help='Verbose')
    return argparser


# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()


if __name__ == "__main__":
    argparser = build_argparser()
    args = argparser.parse_args()

    jira_client = JIRA(auth=(args.username, args.password), server=args.server)

    GRAPH_SESSION = device_flow_session(config.CLIENT_ID, True)
    user_profile = GRAPH_SESSION.get(api_endpoint('me'))
    # print(28*' ' + f'<Response [{user_profile.status_code}]>', f'bytes returned: {len(user_profile.text)}\n')
    if not user_profile.ok:
        pprint.pprint(user_profile.json()) # display error
        exit()

    not_found_list = []
    start_at = 0
    while True:
        users = jira_client.search_users(user='.', includeInactive=True, startAt=start_at, maxResults=100)
        number_of_users = len(users)
        if number_of_users == 0:
            break
        if not args.verbose:
            suffix_str = 'Checking next {} users, {} completed'.format(number_of_users, start_at - 100)
            printProgressBar(0, number_of_users, prefix = 'Progress:', suffix = suffix_str, length = 80)
        start_at = start_at + 100

        number_of_user = 0
        for user in users:
            # print(format(user))
            if not args.verbose:
                suffix_str = 'Checking next {} users, {} completed'.format(number_of_users, start_at - 100)
                printProgressBar(number_of_user, number_of_users, prefix = 'Progress:', suffix = suffix_str, length = 80)
            number_of_user = number_of_user + 1

            user_name = user.name
            user_displayname = user.displayName
            user_email = user.emailAddress

            if user.active == False:
                if args.verbose:
                    print('INACTIVE: ' + user_email)
                continue

            if args.company:
                if args.company not in user_email:
                    if args.verbose:
                        print('NOT COMPANY: ' + user_email)
                    continue

            search_response = GRAPH_SESSION.get(api_endpoint('users/' + user_email))
            person = search_response.json()
            if not search_response.ok:
                if person['error']['code'] == 'Request_ResourceNotFound':
                    not_found = {
                        'user_name': user_name,
                        'user_displayname': user_displayname,
                        'user_email': user_email
                    }
                    not_found_list.append(not_found)

                    if args.verbose:
                        print('NOT FOUND: {} ({}), {}'.format(user_name, user_displayname, user_email))
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

    jira_client.close()

    c = httplib2.Http()
    c.add_credentials(args.username, args.password)

    now = datetime.datetime.now(tzutc())

    for not_found in not_found_list:
        user_name = not_found['user_name']
        user_displayname = not_found['user_displayname']
        user_email = not_found['user_email']

        latest_date = now
        user_request = args.server + '/activity?maxResults=1&os_authType=basic&streams=user+IS+' + user_name
        response, content = c.request(user_request, 'GET')
        root = ET.fromstring(content)
        ns = {'entry': 'http://www.w3.org/2005/Atom'}
        for actor in root.findall('entry:entry', ns):
            published = actor.find('entry:published', ns).text
            updated = actor.find('entry:updated', ns).text
            published_date = dateutil.parser.parse(published)
            updated_date = dateutil.parser.parse(updated)
            if published_date > updated_date:
                latest_date = published_date
            else:
                latest_date = updated_date

        output = '{} ({}), {}'.format(user_name, user_displayname, user_email)
        if latest_date != now:
            output += ', {} ({})'.format(latest_date, naturaltime(now - latest_date))
        if args.company:
            if args.company not in user_email:
                response = requests.get('https://emailrep.io/' + user_email, json={}, headers = {'Accept': 'application/json'})
                emailrep = response.json()
                if emailrep['suspicious'] == True:
                    output += ', SUSPICIOUS'
        print(output)
