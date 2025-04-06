
import json
import os
import re
from configparser import ConfigParser

import black
from src.utils.log import setup_logging
from src.utils.utils import query_llm, list_files, list_subdirectories, file_exists, folder_exists, create_directory


def extract_api_name(text):
    # 正则表达式模式，使用捕获组
    pattern = r"<BUGGY>(.*?)</BUGGY>"
    # < BUGGY > < / BUGGY >
    # < PARA > < / PARA >

    # 使用re.search进行匹配
    match = re.search(pattern, text)
    # 返回提取的内容
    if match:
        return match.group(1)
    else:
        return None

def extract_para_name(text):
    # 正则表达式模式，使用捕获组
    pattern = r"<PARA>(.*?)</PARA>"
    # 使用re.search进行匹配
    match = re.search(pattern, text)
    # 返回提取的内容
    if match:
        return match.group(1)
    else:
        return None


def remove_python_lines(text):
    # 使用正则表达式匹配单独以 "python" 为一行的内容
    pattern = r'^\s*python\s*$'
    cleaned_text = re.sub(pattern, '', text, flags=re.MULTILINE)
    return cleaned_text


if __name__ == '__main__':

    config = ConfigParser()

    config.read('../config.ini', encoding="utf-8")


    # identify_model = config.get('run', 'identify_model')
    identify_model = "Qwen2.5-Coder-7B-Instruct-AWQ"

    issues_directory = list_subdirectories('../ExtractIssues/issues/filter/')
    logger = setup_logging(f'./log/identify_api.log')
    query_long_mode = False
    if identify_model != 'Qwen2-7B-Instruct-AWQ':
        query_long_mode = True
    for issues_direct in issues_directory:
        dlf_issue_files = list_files(f"../ExtractIssues/issues/filter/{issues_direct}")
        if dlf_issue_files == []:
            continue
        for file_path in dlf_issue_files:
            logger.info("now handing file: " + file_path)
            # './result/' + issues_direct + '/' + identify_model + '/'
            if file_exists(f'./result/' + issues_direct + '/' + identify_model + '/', os.path.basename(file_path)):
                logger.info(os.path.splitext(os.path.basename(file_path))[0] + " already exists")
                continue
            with open(file_path, 'r') as file:

                issues = json.load(file)

                for issue in issues:
                    if issue.get('annotation', []) != []:
                        logger.info('annotation is not empty, continue')
                        continue
                    issue['annotation'] = []
                    # logger.info(issue['code'])
                    for code in issue['code']:
                        query_count = 0
                        code = remove_python_lines(code)
                        mode = black.Mode()
                        try:
                            code = black.format_str(code, mode=mode)
                        except Exception as e:
                            logger.info(e)
                            pass
                        while query_count <= 5:
                            # prompt = f"""
                            # Example:
                            # Issues Code Snippet:
                            # ```
                            # m = flow.nn.AdaptiveMaxPool2d((-5, 7))
                            # input = flow.Tensor(np.random.randn(1, 64, 8, 2))
                            # output = m(input)
                            # ```
                            # Issue Title:
                            #
                            # flow.nn.AdaptiveMaxPool2d with negative output size causes crash
                            #
                            # Task:
                            #
                            # 1. Please identify the API call in the code snippet that is causing the issue described in the Issue Title.
                            # 2. Please provide a detailed explanation of why this API call is causing a bug.
                            # 3. Please provide the API name enclosed within <API_NAME></API_NAME>. This will help me programmatically parse your response.
                            #
                            # Example output:
                            # 1. The API call in the code snippet that is causing the issue described in the Issue Title is: m = flow.nn.AdaptiveMaxPool2d((-5, 7))
                            # 2. Explanation:
                            # The flow.nn.AdaptiveMaxPool2d API is used to perform adaptive max pooling on a 2D input. The parameter passed to this API is output_size, which specifies the target output size of the pooling layer. In this case, the output_size is set to (-5, 7).
                            # The negative value -5 in the output_size is problematic. According to the API documentation, output_size should be a tuple of two positive integers or a single positive integer. Negative values for the output size are not valid and can cause the underlying implementation to crash because the pooling operation cannot produce an output with a negative dimension.
                            # The error occurs because the API does not handle negative values for the output_size parameter properly, resulting in an invalid operation and subsequent crash.
                            # 3. API Name:
                            # <API_NAME>flow.nn.AdaptiveMaxPool2d</API_NAME>
                            # Additional Check:
                            #
                            # Please ensure that the API name provided is the full and correct API name as used in the code snippet. If there are multiple similar API names (e.g., ReplicationPad2d/ReplicationPad1d), provide the exact one used in the code snippet.
                            #
                            # Now Your Turn:
                            # Issues Code Snippet:
                            # ```
                            # {code}
                            # ```
                            # Issue Title:
                            # {issue['title']}
                            # Task:
                            # 1. Please identify the API call in the code snippet that is causing the issue described in the Issue Title.
                            # 2. Please provide a detailed explanation of why this API call is causing an error.
                            # 3. Please provide the API name enclosed within <API_NAME></API_NAME>.
                            # """


                            try:
                                if len(issue['desc']) > 20000:
                                    issue['desc'] = issue['desc'][:2000]
                                    logger.info(f"issue['desc'] is too long, truncate it to 2000")
                            except Exception as e:
                                issue['desc'] = "no desc"

                            prompt =f"""You are a helpful and honest code assistant expert in Deep Learning Frameworks. You will analyze a code snippet to identify a buggy API call and explain the associated issue. Think step-by-step as below examples.
Example:
Issue Title: Segmentation fault (core dumped) in torch.nn.functional.max_pool1d
Issue Desc: torch.nn.functional.max_pool1d triggered a crash when stride and kernel_size are too large…
Issues Code Snippet:
```
import torch
kernel_size = 9223372036854775807
stride = 9223372036854775807
input_params = torch.randn(2, 10, 4)
output = torch.nn.functional.max_pool1d(input_params, kernel_size, stride)
```
Task 1: Please identify the buggy API call in the code snippet that is causing the described issue.
Task 2: Please provide a explanation of why this API call is causing a bug.
Task 3: Please provide the buggy API name enclosed within <BUGGY></ BUGGY > tags.
Task 4: Please provide the list of bug-triggering parameters enclosed within the <PARA></PARA> tags.
Example Answer:
1. The API call in the code snippet that is causing the issue is: torch.nn.functional.max_pool1d(input_params, kernel_size, stride).
2. The issue arises because torch.nn.functional.max_pool1d is called with excessively large kernel_size and stride values, leading to a segmentation fault...
3. Buggy API name: <BUGGY>torch.nn.functional.max_pool1d</BUGGY>
4.The list of bug-triggering parameters is <PARA>kernel_size, stride</PARA>

Now, please deal with the following content:
Issue Title:{issue['title']}
Issue Desc:{issue['desc']}
Issues Code Snippet:{code}
Task 1: Please identify the buggy API call in the code snippet that is causing the described issue.
Task 2: Please provide a explanation of why this API call is causing a bug.
Task 3: Please provide the buggy API name enclosed within <BUGGY></BUGGY> tags.
Task 4: Please provide the list of bug-triggering parameters enclosed within the <PARA></PARA> tags."""

                            messages = [
                                {
                                    "role": "system",
                                    "content": "You are a helpful and honest code assistant expert in Python."
                                },
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                            # logger.info(prompt)
                            logger.info(issue['title'])
                            logger.info(issue['url'])
                            result, time,status = query_llm(messages, model=identify_model, ip='192.168.9.2',
                                                     port='9999')
                            # 2024-10-21
                            # if len(prompt) <= 5500 and query_long_mode == True:
                            #     result, time, status = query_llm(messages, model='CodeLlama-34B-Instruct-AWQ', ip='192.168.9.2',
                            #                              port='8000')
                            #     logger.info('query CodeLlama-34B-Instruct-AWQ')
                            # elif len(prompt) > 5500 and query_long_mode == True:
                            #     result, time, status = query_llm(messages, model='CodeLlama-13B-Instruct-AWQ',
                            #                              ip='192.168.9.2',
                            #                              port='9999')
                            #     logger.info('query CodeLlama-13B-Instruct-AWQ')
                            # logger.info(result)
                            if status == 'FAILED':
                                query_content = "query llm failed"
                            else:
                                query_content = result['choices'][0]['message']['content']
                            # logger.info(query_content)
                            logger.info(f"query time: {time}")
                            # extract_api_name(query_content) in code 不要这个条件了
                            extract_api = extract_api_name(query_content)
                            if extract_api != '' and extract_api is not None:
                                issue['annotation'].append(
                                    {
                                        'code': code,
                                        'api': extract_api,
                                        'para': extract_para_name(query_content),
                                        'query_count': query_count,
                                        'query_content': query_content
                                    },
                                )
                                print("buggy api: ", extract_api)
                                print("buggy para: ", extract_para_name(query_content))
                                # logger.info(f"query count: {query_count}")
                                break
                            query_count += 1
                        if issue['annotation'] == []:
                            logger.info("llms not given any result")
                            issue['annotation'] = []
            save_folder = './result/' + issues_direct + '/' + identify_model + '/'
            if not folder_exists(save_folder):
                create_directory(save_folder)
            with open(save_folder + os.path.basename(file_path), 'w') as file:
                json.dump(issues, file, indent=4)
            print('handled ' + file_path)
