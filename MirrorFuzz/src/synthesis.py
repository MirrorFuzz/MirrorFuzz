import ast
import glob
import json
import os
import re
import shutil
import time

import json5

from utils.utils import list_files, query_llm, run_cmd, get_uuid, create_directory

from enum import IntEnum, auto




class ExecutionStatus(IntEnum):
    SUCCESS = auto()
    EXCEPTION = auto()
    CRASH = auto()
    NOTCALL = auto()
    TIMEOUT = auto()


def get_first_sentence(paragraph):
    match = re.search(r'[^。.!?]*[。.!?]', paragraph)
    if match:
        return match.group(0)
    else:
        return ""



def query_api_doc(target_api, dlf):

    with open(f'./CrawlerAPIs/{dlf}/{dlf}_api_list_jsons.json', mode='r', encoding='utf-8') as jsons:
        api_info_json = json.load(jsons)
        for api_info in api_info_json:
            if api_info['api_name'] == target_api:
                try:
                    # 只取描述的第一句
                    api_info['api_description'] = get_first_sentence(api_info['api_description'])
                except Exception as e:
                    pass
                # print(type(api_info))
                keys_to_remove = {"api_url", "notes"}
                for key in keys_to_remove:
                    api_info.pop(key, None)
                return api_info
    return ''


def extract_code_blocks(text, code_type="markdown"):
    code_blocks = "FAIL"
    try:
        if code_type == "markdown":

            code_blocks = re.findall(r'```(.*?)```', text, re.DOTALL)
        elif code_type == "json":
            if "```json" in text:

                json_data = re.findall(r'```json(.*?)```', text, re.DOTALL)
                if json_data:
                    json_data = json5.loads(json_data[0].strip())
                    code_blocks = json_data["code"]
            else:
                json_data = json5.loads(text.strip())
                code_blocks = json_data["code"]
    except Exception as e:
        code_blocks = "FAIL"
    return code_blocks


def save_crash_cause(test_api, test_dlf, sim_api, code, sim_api_dlf, llm_result, save_folder, query_count,
                     crash_sim_type):
    with open(
            f'{save_folder}/crash_pool/{test_dlf}/{test_api}_{sim_api_dlf}_{sim_api}_{crash_sim_type}_{get_uuid()}.py',
            mode='w',
            encoding='utf-8') as file:
        file.write(code)
        comments = f"""\n'''
# test_api: {test_api}
# test_dlf: {test_dlf}
# sim_api: {sim_api}
# sim_api_dlf: {sim_api_dlf}
# llm result: {llm_result}
# crash_sim_type: {crash_sim_type}
'''"""
        file.write(comments)

    file.close()
    with open(f'{save_folder}/crash/{test_dlf}/{test_api}_{sim_api_dlf}_{sim_api}_{crash_sim_type}_{get_uuid()}.txt',
              mode='w',
              encoding='utf-8') as file:
        file.write("test_api: " + test_api + '\n')
        file.write("test_dlf: " + test_dlf + '\n')
        file.write("sim_api: " + sim_api + '\n')
        file.write("sim_api_dlf: " + sim_api_dlf + '\n')
        file.write("crash code: " + code + '\n')
        file.write("llm result: " + llm_result)
        file.write("crash_sim_type: " + crash_sim_type)
    file.close()

    # update bug record
    file_path = f'../IdentifyAPIs/result/{test_dlf}/Qwen2-7B-Instruct-AWQ-leven-tf-relocate/new_bug.json'
    new_bug = {
        "id": get_uuid(),
        "title": f"TensorFlow {test_api} API in {test_dlf} framework crashes with {sim_api} API in {sim_api_dlf} framework",
        "url": "",
        "code": [code],
        "created_at": "",
        "updated_at": "",
        "closed_at": "",
        "annotation": [
            {
                "code": code,
                "api": test_api,
                "query_count": 0,
                "query_content": llm_result
            }
        ]
    }

    existing_data = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []


    existing_data.append(new_bug)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, indent=2, ensure_ascii=False)

def exception_query_llm(test_api, test_dlf, sim_api, sim_api_dlf, code, llm_content, exception_msg, llm_model,
                        llm_model_ip, llm_model_port):
    prompt = f"""
    The LLM generated code snippet is designed for the {test_api} API in the {test_dlf} framework to simulate a crash scenario similar to the {sim_api} API in the {sim_api_dlf} framework. However, when executed, the generated code raises an exception instead of crashing:
    {code}
    The LLM provided the following content:
    {llm_content}
    The exception message is:
    {exception_msg}
    Expected Output Format (Strict JSON):
    {{
    "code": "here is code"
    }}
    Now, process the following input and return only JSON output:
    Task: Based on the provided exception message and the LLM's content, please modify the generated code for the {test_api} API in the {test_dlf} framework to ensure it runs without exceptions.
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

    if len(prompt) >= 11000:
        print('llm query failed, prompt too long in exception_query_llm ')
        return None
    try:
        result, time, status = query_llm(messages, model=llm_model, ip=llm_model_ip,
                                         port=llm_model_port)
        if status == "FAILED":
            print('llm query failed ', result)
            return result
        llm_content = result['choices'][0]['message']['content']
        # save_code(f'../LLM_fix_{get_uuid()}.txt',
        #           llm_content)
    except Exception as e:
        print(e)
        llm_content = "LLM Error"

    return llm_content


def save_code(file_path, code):
    with open(file_path, mode='w', encoding='utf-8') as file:
        file.write(code)


def process_code(codes, codes_file, cmd_args, test_dlf, test_api, sim_api, source_crash_framework, save_folder,
                 query_count, timeout, llm_content, llm_model, llm_model_ip, llm_model_port, crash_sim_type,
                 flag='normal'):
    # for index, code in enumerate(codes):
    try:
        filter_code = re.sub(r'^\s*python\s*$', '', codes, flags=re.MULTILINE)
    except Exception as e:
        filter_code = codes
    save_code(codes_file, filter_code)

    exec_start_time = time.time()
    run_status, error_msg = run_cmd(cmd_args, timeout=timeout, verbose=False, shell=True)
    exec_end_time = time.time()
    print('test case exec time: ' + str(exec_end_time - exec_start_time))

    if not os.path.exists(f'{save_folder}/seed_pool/{test_dlf}/{test_api}'):
        create_directory(f'{save_folder}/seed_pool/{test_dlf}/{test_api}')

    save_code(f'{save_folder}/seed_pool/{test_dlf}/{test_api}/{sim_api}_{crash_sim_type}_{get_uuid()}.py',
              filter_code)


    if run_status == ExecutionStatus.SUCCESS:
        print('code snippet '  + ' success with sim api ' + sim_api)
    elif run_status == ExecutionStatus.CRASH or "please report a bug to PyTorch" in error_msg or "report a bug" in error_msg:
        print('code snippet ' + ' crash with sim api ' + sim_api)
        save_crash_cause(test_api, test_dlf, sim_api, filter_code, source_crash_framework, llm_content, save_folder,
                         query_count, crash_sim_type)
    elif run_status == ExecutionStatus.EXCEPTION and flag == 'normal':
        print('code snippet ' + ' exception with sim api ' + sim_api)
        # continue
        exception_query_start_time = time.time()

        llm_content = exception_query_llm(test_api, test_dlf, sim_api, source_crash_framework, filter_code,
                                          llm_content, error_msg, llm_model, llm_model_ip, llm_model_port)
        exception_query_end_time = time.time()
        print('llm fix query time: ' + str(exception_query_end_time - exception_query_start_time))
        if llm_content is None:
            return
        codes = extract_code_blocks(llm_content, "json")
        if codes == "FAIL":
            exception_query_start_time = time.time()

            llm_content = exception_query_llm(test_api, test_dlf, sim_api, source_crash_framework, filter_code,
                                              llm_content, error_msg, llm_model, llm_model_ip, llm_model_port)
            exception_query_end_time = time.time()
            print('llm fix query time: ' + str(exception_query_end_time - exception_query_start_time))
            codes = extract_code_blocks(llm_content, "json")
            if codes == "FAIL":
                print("JSON FAIL")
                return

        process_code(codes, codes_file, cmd_args, test_dlf, test_api, sim_api, source_crash_framework, save_folder,
                     query_count, timeout, llm_content, llm_model, llm_model_ip, llm_model_port, crash_sim_type,
                     'exception')
    elif run_status == ExecutionStatus.TIMEOUT:
        save_code(f'{save_folder}/hang/{test_dlf}/{test_api}_{source_crash_framework}_{sim_api}_{query_count}.py',
                  filter_code)


def synthesis(test_dlf, test_api, source_api_crash_list, crash_sim_type, generation_number, timeout, save_folder,
              llm_model, llm_model_ip, llm_model_port):
    print(f'-----test api: {test_api}-----')
    no_clash_data = 0
    for source_crash_framework, source_crash_api in source_api_crash_list.items():
        if source_crash_api == []:
            no_clash_data += 1

    if no_clash_data == len(source_api_crash_list):
        query_count = 0

        prompt_en = f"""Question:
        You are a helpful and honest code assistant expert in Deep Learning Frameworks. Please generate code that can trigger bugs for the specified API.
        Expected Output Format (Strict JSON): {{"code": "here is code"}}
        API: {test_api},
        Deep Learning Framework: {test_dlf},
        API description: {query_api_doc(test_api, test_dlf)}
        Eexample Output:
        {{"code": "here is code"}}
         Now,  please generate code and return only JSON output:
"""
        messages = [
            {"role": "system",
             "content": "You are a helpful and honest code assistant expert in Deep Learning Frameworks."},
            {"role": "user", "content": prompt_en}
        ]
        while query_count < generation_number:
            # print('prompt_en_len:', len(prompt_en))
            print("no crash data, random generation, query count: " + str(query_count))
            if len(prompt_en) >= 25000:
                break
            result, time, status = query_llm(messages, model=llm_model, ip=llm_model_ip,
                                             port=llm_model_port)
            if status == "FAILED":
                exit(0)
                break
            llm_content = result['choices'][0]['message']['content']
            codes = extract_code_blocks(llm_content, "json")

            if codes == "FAIL":
                result, time, status = query_llm(messages, model=llm_model, ip=llm_model_ip,
                                                 port=llm_model_port)
                llm_content = result['choices'][0]['message']['content']
                codes = extract_code_blocks(llm_content, "json")
                if codes == "FAIL":
                    print("JSON FAIL")
                    continue

            codes_file = f'{save_folder}/runtime/temp.py'
            cmd_args = f"cd {save_folder}/runtime/ && /root/miniconda3/envs/{test_dlf}/bin/python3 temp.py"
            print("llm no crash data generate time: " + str(time))
            print(cmd_args)
            process_code(codes, codes_file, cmd_args, test_dlf, test_api, "no_sim_api", source_crash_framework,
                         save_folder,
                         query_count, timeout, llm_content, llm_model, llm_model_ip, llm_model_port, crash_sim_type)

            query_count += 1

    for source_crash_framework, source_crash_api in source_api_crash_list.items():
        for source_crash in source_crash_api:

            for source_crash_info in source_crash['annotation']:
                sim_api = source_crash_info['api']
                print(f'>>> handing sim api: {sim_api} ')
                query_count = 0

                prompt_en = f"""
Question:You are a helpful and honest code assistant expert in Deep Learning Frameworks. Please generate code that can trigger similar bugs for the specified API, utilizing the bug data from the similar API. Think step-by-step as below examples.
Example Input:
Source Deep Learning Framework: OneFlow
Source API: flow.nn.ReflectionPad1d
Source API Documention: This operator pads the input tensor using the reflection of the input boundary. Parameters : padding
(Union[int,tuple]) – The size or bundary of padding, if is int uses the same padding in all dimension …
The source API has a similar API torch.nn.ReflectionPad2d in PyTorch.
The similar API Documention: Pads the input tensor using the reflection of the input boundary. For N-dimensional padding, use
torch.nn.functional.pad(). Parameters: padding (int, tuple) – the size of the padding. If is int, uses the same padding in all boundaries…
The similar API’s buggy code:
```
import torch
torch.nn.ReflectionPad2d(padding=-8353862602220610428)(torch.ones((15,5,5,1)))
```
Root cause of the bug: torch.nn.ReflectionPad2d throws segmentation fault when padding is negative and large.
List of parameters causing the bug: [padding]
Task 1: Please generate code for flow.nn.ReflectionPad1d that triggers similar bugs based on the root cause of torch.nn.ReflectionPad2d
Task 2: Return only JSON format with no extra text.
Expected Output Format (Strict JSON):
{{
                "code": "import oneflow as flow\nflow.nn.ReflectionPad1d(padding=-8353862602220610428)(oneflow.ones((15,5)))"
}}

Now, process the following input and return only JSON output:
Source Deep Learning Framework: {test_dlf}
Source API: {test_api}
Source API Documention: {query_api_doc(test_api, test_dlf)}
The source API has a similar API {source_crash_info['api']} in {source_crash_framework}.
The similar API Documention: {query_api_doc(source_crash_info['api'], source_crash_framework)}
The similar API’s buggy code:
```
{''.join(source_crash['code'])}
```
Task : Please generate code for {test_api} that triggers similar bugs based on the root cause of {source_crash_info['api']} in {source_crash_framework}.
"""
                messages = [
                    {"role": "system",
                     "content": "You are a helpful and honest code assistant expert in Deep Learning Frameworks."},
                    {"role": "user", "content": prompt_en}
                ]

                while query_count < generation_number:
                    print('prompt_en_len:', len(prompt_en))
                    if len(prompt_en) >= 25000:
                        break

                    result, time, status = query_llm(messages, model=llm_model, ip=llm_model_ip, port=llm_model_port)

                    if status == "FAILED":
                        exit(0)
                        break

                    llm_content = result['choices'][0]['message']['content']
                    codes = extract_code_blocks(llm_content, "json")
                    codes_file = f'{save_folder}/runtime/temp.py'
                    cmd_args = f"cd {save_folder}/runtime/ && /root/miniconda3/envs/{test_dlf}/bin/python3 temp.py"

                    process_code(codes, codes_file, cmd_args, test_dlf, test_api, sim_api, source_crash_framework,
                                 save_folder, query_count, timeout, llm_content, llm_model, llm_model_ip,
                                 llm_model_port, crash_sim_type)
                    query_count += 1

