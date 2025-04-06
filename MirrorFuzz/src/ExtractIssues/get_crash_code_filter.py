import json
import os
from src.utils.log import setup_logging
from src.utils.utils import list_files, file_exists, list_subdirectories
from src.utils.utils import run_cmd, check_code, contains_bug_keywords
import re
from threading import Lock


def extract_code_blocks(text):
    # Match code blocks enclosed with ``` ```
    code_blocks = re.findall(r'```(.*?)```', text, re.DOTALL)
    return code_blocks


def re_filter_code_blocks(code_block):
    import_pattern = re.compile(r'\bimport\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\s+as\s+[a-zA-Z_][a-zA-Z0-9_]*)?')
    # Match from ... import
    from_import_pattern = re.compile(
        r'\bfrom\s+[a-zA-Z_][a-zA-Z0-9_]*\s+import\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\s+as\s+[a-zA-Z_][a-zA-Z0-9_]*)?')
    assignment_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^=]')
    function_call_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\(([^)]*)\)')
    traceback_pattern = re.compile(r'Traceback \(most recent call last\):', re.IGNORECASE)
    import_matches = import_pattern.findall(code_block)
    from_import_matches = from_import_pattern.findall(code_block)
    assignment_matches = assignment_pattern.findall(code_block)
    function_call_matches = function_call_pattern.findall(code_block)
    complete_error_matches = traceback_pattern.findall(code_block)
    return import_matches, from_import_matches, assignment_matches, function_call_matches, complete_error_matches


if __name__ == '__main__':
    file_lock = Lock()
    colab_lock = Lock()
    issues_directory = list_subdirectories('./issues/origin/')
    for issues_direct in issues_directory:
        dlf_issue_files = list_files(f"./issues/origin/{issues_direct}")
        logger = setup_logging(f'./log/filter/issues_code_filter.log')
        count = 0
        for file_path in dlf_issue_files:
            logger.info("now handing file: " + file_path)
            # if file_exists(f"./issues/filter/{issues_direct}", os.path.basename(file_path)):
            #     logger.info(os.path.splitext(os.path.basename(file_path))[0] + " already exists")
            #     continue
            with open(file_path, 'r') as file:
                dlf_issues_json = json.load(file)
                # Determine if the JSON content is empty
                if dlf_issues_json == {} or dlf_issues_json['items'] == []:
                    print('json is empty')
                    continue

                filter_save_data = []
                for issue in dlf_issues_json['items']:
                    filter_save_item = {}
                    logger.info(issue['html_url'])
                    save_code_blocks = []

                    if not contains_bug_keywords(issue['title']) and not contains_bug_keywords(issue['body']):
                        continue
                    content = issue['body']
                    # Determine whether there is content in the issue
                    if not content:
                        continue
                    # Extract code
                    code_blocks = extract_code_blocks(content)
                    for code_block in code_blocks:
                        if not code_block:
                            continue
                        # Regular matching filtering
                        import_matches, from_import_matches, assignment_matches, function_call_matches, complete_error_matches = re_filter_code_blocks(
                            code_block)
                        if (import_matches is not []
                            or from_import_matches is not []
                            or assignment_matches is not []
                            or function_call_matches is not []) and complete_error_matches == []:
                            function_call_matches_string = json.dumps(function_call_matches)
                            # Filter again
                            with file_lock:
                                with open(r"./log/filter/temp/temp.py", "w", encoding="utf-8") as f:
                                    f.write(code_block)
                                f.close()
                            # If not compiled, discard
                            flag, output = check_code("./log/filter/temp/temp.py")
                            if flag == "SyntaxError":
                                continue
                            elif flag == "No SyntaxError":
                                logger.info(issue['html_url'] + ', No SyntaxError')
                                save_code_blocks.append(code_block)
                                count += 1
                            else:
                                continue
                        logger.info("------------------------------------")
                    if save_code_blocks != []:
                        filter_save_item = {
                            "id": issue['id'],
                            "title": issue['title'],
                            "url": issue['html_url'],
                            "code": save_code_blocks,
                            "desc": issue['body'],
                            "created_at": issue['created_at'],
                            "updated_at": issue['updated_at'],
                            "closed_at": issue['closed_at'],
                        }
                    if filter_save_item != {}:
                        filter_save_data.append(filter_save_item)
                with open(f"./issues/filter/{issues_direct}/{os.path.splitext(os.path.basename(file_path))[0]}.json",
                          'w') as f:
                    json.dump(filter_save_data, f, indent=4)

        logger.info("count: " + str(count))
