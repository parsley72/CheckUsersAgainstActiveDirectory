# Check Users Against ActiveDirectory

This is actually several different scripts but they all share code to check users against ActiveDirectory.

## Installation

All script dependencies are handled by [Pipenv](https://docs.pipenv.org). To install see [Pipenv & Virtual Environments](https://docs.pipenv.org/en/latest/install/).

To install the dependencies for the scripts type:

```bash
pipenv install
```

## CheckAWSUsers.py

Our AWS IAM accounts predate our use of AWS Federated Authentication with ActiveDirectory so we want to remove them. Unfortunately the account names didn't follow any particular format so can't be matched up easily to ActiveDirectory accounts. The formats that can be recognised are:

- Email address
- firstname.lastname (e.g. bob.jones)
- FirstnameLastname (e.g. BobJones)
- admin.FirstnameLastname (e.g. admin.BobJones)
- admin.firstname (e.g. admin.bob)

So the algorithm works as follows:

1. Check to see if the IAM account has a metadata tag "Email". If so lookup this value in ActiveDirectory.
2. Look up the IAM username in ActiveDirectory.
3. If this fails:
    1. Remove 'admin.' from the start of the username, e.g. "admin.bob" -> "bob".
    2. If no '.' left in the username try adding a space before capitals, e.g. "BobJones" -> "Bob Jones".
    3. Look up this modifed username in ActiveDirectory.
4. If this fails:
    1. If the modified username contains '.' or ' ' then split the username using this character, e.g. "bob.jones" -> ["bob", "jones"].
    2. Look up the second name (probably the surname) in ActiveDirectory.
5. If this fails:
    1. Look up the first name (probably the first/Christian name) in ActiveDirectory.

This won't find every user but it does get most of them. If you have usernames that can't be identified you can add metadata tag "Email" to specify the email address for that user that can be used in the future.

Before running you need to get an AWS key by logging in to your account.

```bash
python CheckAWSUsers.py --profile myprofile --region us-east-1
```

| Short | Long | Description | Required |
| ----- | ---- | ----------- | -------- |
| `-p` | `--profile` | AWS profile to use | No |
| `-r` | `--region` | AWS region to use | No |
| `-v` | `--verbose` | Verbose | No |

## CheckJiraUsers.py

```bash
python CheckJiraUsers.py --server=https://jira.mycompany.com --username bob.jones --password NOTMYPASSWORD --company=@mycompany.com
```

| Short | Long | Description | Required |
| ----- | ---- | ----------- | -------- |
| `-s` | `--server` | | Jira server URL | Yes |
| `-u` | `--username` | Jira username (not email) | Yes |
| `-p` | `--password` | Jira password | Yes |
| `-c` | `--companyemail` | Company name to filter email address on | No |
| `-v` | `--verbose`  | Verbose | No |

## CheckSlackUsers.py

```bash
python CheckSlackUsers.py --token=xxxx-0000000000-0000000000-000000000000-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx --companyemail=@mycompany.com
```

| Short | Long | Description | Required |
| ----- | ---- | ----------- | -------- |
| `-t` | `--token` | Token for Slack | Yes |
| `-c` | `--companyemail` | Company name for email address | Yes |
| `-v` | `--verbose`  | Verbose | No |

## CheckTestRailUsers.py

```bash
python CheckTestRailUsers.py --username bob.jones --password NOTMYPASSWORD
```

| Short | Long | Description | Required |
| ----- | ---- | ----------- | -------- |
| `-s` | `--server` | | TestRail server URL | Yes |
| `-u` | `--username` | TestRail username (not email) | Yes |
| `-p` | `--password` | TestRail password | Yes |
| `-v` | `--verbose`  | Verbose | No |

## CheckKeenUsers.py

```bash
python CheckKeenUsers.py --organisation=000000000000000000000000 --authorization=0000000000000000000000000000000000000000000000000000000000000000
```

| Short | Long | Description | Required |
| ----- | ---- | ----------- | -------- |
| `-o` | `--organisation` | Keen.io organisation | Yes |
| `-c` | `--authorization` | Keen.io authorization | Yes |
| `-v` | `--verbose`  | Verbose | No |
