import json
import os
from time import sleep

from src.utils.log import setup_logging
from src.utils.utils import list_files, file_exists, contains_bug_keywords, list_subdirectories
from src.utils.get_from_colab import get_from_colab
import re
from threading import Lock


def extract_code_blocks(text):
    pattern = r'https://colab\.research\.google\.com/drive/[a-zA-Z0-9_-]+'
    # Search for matching patterns
    re_colab_links = re.findall(pattern, text)
    return re_colab_links


if __name__ == '__main__':
    # Create a global lock object
    file_lock = Lock()
    colab_lock = Lock()

    issues_directory = list_subdirectories('./issues/origin/')
    for issues_direct in issues_directory:
        dlf_issue_files = list_files(f"./issues/origin/{issues_direct}")
        logger = setup_logging(f'./log/colab/{issues_direct}_issues_code_colab_filter.log')
        count = 0
        for file_path in dlf_issue_files:
            logger.info("now handing file: " + file_path)

            with open(file_path, 'r') as file:
                # Load a single JSON file
                dlf_issues_json = json.load(file)
                if dlf_issues_json == {} or dlf_issues_json['items'] == []:
                    print('json is empty')
                    continue

                save_data = []
                for issue in dlf_issues_json['items']:
                    save_item = {}
                    save_code_blocks = []
                    if not contains_bug_keywords(issue['title']) and not contains_bug_keywords(issue['body']):
                        continue
                    content = issue['body']
                    # Determine whether there is content in the issue
                    if not content:
                        continue
                        # Extract ```code```
                    colab_links = extract_code_blocks(content)
                    if colab_links != []:
                        count += 1
                        # print(issue['title'])
                        print(issue['id'])
                        print(issue['html_url'])
                        logger.info(colab_links)
                        code = []
                        with colab_lock:
                            for link in colab_links:
                                try:
                                    code.extend(get_from_colab(link))
                                except Exception as e:
                                    logger.info(e)
                                    continue

                        with open("./issues/filter/" + issues_direct + "/" + os.path.basename(file_path),
                                  'r') as f:
                            json_data = json.load(f)
                            not_in_file = True
                            save_item = []
                            for item in json_data:
                                if item['id'] == issue['id']:
                                    item['code'].extend(code)
                                    with open("./issues/filter/" + issues_direct + "/" + os.path.basename(
                                            file_path), 'w') as f:
                                        json.dump(json_data, f, indent=4)
                                    print("add colab code successfully")
                                    f.close()
                                    not_in_file = False
                                else:
                                    pass
                                    # print("id is not equal")
                            # If the extracted file is not available, add a new one
                            if not_in_file:
                                save_item = {
                                    "id": issue['id'],
                                    "title": issue['title'],
                                    "url": issue['html_url'],
                                    "code": code,
                                    "created_at": issue['created_at'],
                                    "updated_at": issue['updated_at'],
                                    "closed_at": issue['closed_at'],
                                }
                                with open("./issues/filter/" + issues_direct + "/" + os.path.basename(file_path),
                                          'w') as f:
                                    json_data.append(save_item)
                                    json.dump(json_data, f, indent=4)
                                    f.close()
                                logger.info("new add colab code successfully")
                        print("---------------------------------")
                        sleep(1)
    print(count)
