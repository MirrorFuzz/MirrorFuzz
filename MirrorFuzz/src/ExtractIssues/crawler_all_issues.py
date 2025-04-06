import json
import os
import re
from datetime import datetime
from time import sleep
from configparser import ConfigParser
from src.utils.log import setup_logging
from src.utils.utils import ensure_directory_exists
import requests
from threading import Lock


def get_owner_repo_from_url(url):
    pattern = r"https://github.com/([^/]+)/([^/]+)"
    match = re.match(pattern, url)
    if match:
        owner = match.group(1)
        repo = match.group(2)
        return owner, repo
    return None, None


def request_to_github(url, github_token):
    response = requests.get(url,
                            headers={
                                'X-GitHub-Api-Version': '2022-11-28',
                                'Authorization': f"token {github_token}"
                            })

    return response.json()


# Whitelist, filter through API lists and other methods as much as possible, and use code detection to check if it is code, because not everyone submits according to the criteria of the issue
def fetch_issues(total_issues, start_date, owner, repo, github_token):
    handing_direct = './issues/origin'
    if total_issues == 0:
        total_issues = get_issue_num()
    logger.info("starting to fetch issues")
    ensure_directory_exists(f'{handing_direct}/{repo}')
    if is_directory_empty(f'{handing_direct}/{repo}'):
        pass
    else:
        file_name, create_date, now_page = get_oldest_date_latest_number_file(f"./{repo}")
        start_date = create_date

    while True:
        for page in range(1, 11):  # Each group can obtain a maximum of 10 pages (1000 issues)
            base_url = f"https://api.github.com/search/issues?q=repo:{owner}/{repo}+is:issue+created:<={start_date}&page={page}&per_page=100"
            logger.info(f"fetching page(*100) {page} with {total_issues} issues from {start_date} ... {base_url}")
            while True:
                try:
                    issues = request_to_github(base_url, github_token)
                    break
                except Exception as e:
                    sleep(5)  # Wait for 5 seconds and retry

            if issues.get('status', 200) == 403:
                logger.info("API rate limit exceeded. Please wait and try again later.")
                sleep(60)
                continue

            file_name = f"{owner}_{repo}_{start_date}_{page}"
            with open(f'{handing_direct}/{repo}/{file_name}.json', 'w') as file:
                json.dump(issues, file, indent=4)
            logger.info("saving to file: " + file_name)

            if page == 10:
                # with open(f"{owner}_{repo}_{start_date}_{page}" + ".json", 'r') as file:
                #     data = json.load(file)
                try:
                    time = issues['items'][-1]['created_at']
                except Exception as e:
                    print(issues)

                dt = datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ')
                #  yyyy-mm-dd
                formatted_date = dt.strftime('%Y-%m-%d')
                start_date = formatted_date
                logger.info(f"Updating start_time to {start_date}")
            sleep(2)
            try:
                if len(issues['items']) < 100:  # If items are less than 100, it means it has reached the last page
                    logger.info("finished fetching issues")
                    return
            except:
                continue


def get_issue_num():
    page = 1
    url = f"https://api.github.com/search/issues?q=repo:{owner}/{repo}+is:issue+updated:<={start_date}&per_page={page}"
    logger.info("get issue num from url: " + url)
    response = requests.get(url,
                            headers={
                                'X-GitHub-Api-Version': '2022-11-28',
                                'Authorization': 'Bearer '
                            }, auth=(github_username, github_token))

    if response.status_code == 200:
        issues = response.json()
    else:
        issues = []

    if not issues:
        return None
    else:
        return issues['total_count']


def extract_date_and_number(file_name):
    pattern = owner + "_" + repo + r"_(\d{4}-\d{2}-\d{2})_(\d+)"
    match = re.match(pattern, file_name)
    if match:
        date_str, number = match.groups()
        return date_str, int(number)
    return None, None


def get_oldest_date_latest_number_file(directory):
    # Retrieve all files in the directory
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    # Extract dates and numbers from files
    files_with_date_and_number = []
    for file in files:
        date_str, number = extract_date_and_number(file)
        if date_str and number is not None:
            files_with_date_and_number.append((file, date_str, number))

    # Sort by date, then by number
    if files_with_date_and_number:
        files_with_date_and_number.sort(key=lambda x: (x[1], -x[2]))

        # Find the file with the largest number in the earliest date
        oldest_date_latest_number_file = files_with_date_and_number[0][0]
        oldest_date = files_with_date_and_number[0][1]
        latest_number = files_with_date_and_number[0][2]

        return oldest_date_latest_number_file, oldest_date, latest_number
    else:
        return None, None, None


def is_directory_empty(directory):
    # Check if the directory exists
    if not os.path.isdir(directory):
        raise ValueError(f"The path {directory} is not a valid directory.")

    # Check if the directory is empty
    if not os.listdir(directory):
        return True
    else:
        return False


if __name__ == '__main__':
    # Create parser object
    config = ConfigParser()
    # Read configuration file
    config.read('../config.ini', encoding="utf-8")
    github_username = config.get('github', 'username')
    github_token = config.get('github', 'token')
    test_deep_learning_framework_url = config.get('run', 'test_deep_learning_framework_url').split(',')
    start_date = "2024-10-30"  # ISO 8601
    for deep_learning_framework_url in test_deep_learning_framework_url:
        print('now processing: ', deep_learning_framework_url)
        # Page parameters
        owner, repo = get_owner_repo_from_url(deep_learning_framework_url)
        total_issues = 0  # Need to run for the first time, check the total
        logger = setup_logging(f'./log/issues/issues_extract_{repo}.log')
        # total_issues, owner, repo, github_token
        fetch_issues(total_issues, start_date, owner, repo, github_token)

    # import subprocess
    # get_crash_code_filter_lock = Lock()
    # get_code_colab_lock = Lock()
    # with get_crash_code_filter_lock:
    #     subprocess.run(['python', 'get_crash_code_filter.py'])
    # with get_code_colab_lock:
    #     subprocess.run(['python', 'get_code_colab.py'])
