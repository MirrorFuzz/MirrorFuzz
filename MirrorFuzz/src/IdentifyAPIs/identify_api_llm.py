
import json
import json5
import os
import re
from configparser import ConfigParser

import black
from src.utils.log import setup_logging
from src.utils.utils import query_llm, list_files, list_subdirectories, file_exists, folder_exists, create_directory


# def extract_api_name(text):
#
#     pattern = r"<API_NAME>(.*?)</API_NAME>"
#
#     match = re.search(pattern, text)
#
#     if match:
#         return match.group(1)
#     else:
#         return None


def extract_json(text):
    if "```json" in text:

        json_data = re.findall(r'```json(.*?)```', text, re.DOTALL)
        if json_data:
            try:
                json_data = json5.loads(json_data[0].strip())

                return json_data
            except json5.JSONDecodeError as e:
                return {"error": f"JSON Decode Error: {str(e)}"}
    else:

        try:
            json_data = json5.loads(text.strip())
            return json_data
        except json5.JSONDecodeError as e:
            return {"error": f"JSON Decode Error: {str(e)}"}

def remove_python_lines(text):

    pattern = r'^\s*python\s*$'
    cleaned_text = re.sub(pattern, '', text, flags=re.MULTILINE)
    return cleaned_text


if __name__ == '__main__':

    config = ConfigParser()

    config.read('../config.ini')

    # 2024-10-1
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
                            prompt = f"""
                   
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
                            Task 1: Please give a brief explanation of the root cause of this bug based on the bug report.
                            Task 2: Please identify the buggy API name in the code snippet that is causing the described issue.
                            Task 3: Please provide the list of bug-triggering parameters.
                            Please return the answer in strict JSON format.

                            LLM Example Answer as JSON Format: {{
                            "explanation": "The root cause of the bug is that the kernel_size and stride values provided to torch.nn.functional.max_pool1d are
                            excessively large. These values exceed the dimensions of the input tensor, leading to invalid memory access.",
                            "buggy_api": "torch.nn.functional.max_pool1d",
                            "parameters": ["kernel_size", "stride"] }}
                            Additional Check:

                            Please ensure that the API name provided is the full and correct API name as used in the code snippet. If there are multiple similar API names (e.g., ReplicationPad2d/ReplicationPad1d), provide the exact one used in the code snippet.

                            Now Your Turn:
                            Issues Code Snippet:
                            ```
                            {code}
                            ```
                            Issue Title:
                            {issue['title']}
                            Task:
                            Task 1: Please give a brief explanation of the root cause of this bug based on the bug report.
                            Task 2: Please identify the buggy API name in the code snippet that is causing the described issue.
                            Task 3: Please provide the list of bug-triggering parameters.
                            Please return the answer in strict JSON format
                            """
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
                            if extract_json(query_content) != '' and extract_json(
                                    query_content) is not None:
                                issue['annotation'].append(
                                    {
                                        'code': code,
                                        'api': extract_json(query_content)["buggy_api"],
                                        'query_count': query_count,
                                        'query_content': query_content
                                    },
                                )
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
