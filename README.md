# Check Users Against ActiveDirectory

This is actually several different scripts but they all share code to check users against ActiveDirectory.

## Installation

All script dependencies are handled by [Pipenv](https://docs.pipenv.org). To install see [Pipenv & Virtual Environments](https://docs.pipenv.org/en/latest/install/).

To install the dependencies for the scripts type:

```bash
pipenv install
```

## CheckAWSUsers.py

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
