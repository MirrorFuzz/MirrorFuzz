import json
import os
from collections import Counter

from utils.log import setup_logging
from utils.utils import list_files
from utils.utils import run_cmd, check_code
from utils.get_from_colab import get_from_colab
import re
from threading import Lock

logger = setup_logging(f'./log/pytorch_test_issues_extract.log')
# 创建一个全局锁对象
file_lock = Lock()
colab_lock = Lock()

# 匹配 import 语句
import_pattern = re.compile(r'\bimport\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\s+as\s+[a-zA-Z_][a-zA-Z0-9_]*)?')

# 匹配 from ... import 语句
from_import_pattern = re.compile(
    r'\bfrom\s+[a-zA-Z_][a-zA-Z0-9_]*\s+import\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\s+as\s+[a-zA-Z_][a-zA-Z0-9_]*)?')
assignment_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^=]')
function_call_pattern = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\(([^)]*)\)')
# complete_error_pattern = re.compile(r'Traceback \(most recent call last\):\n(?:  .+\n)+\b\w+Error\b: .+')
traceback_pattern = re.compile(r'Traceback \(most recent call last\):', re.IGNORECASE)

keyword = ['most recent call last', 'error']

torch_files = list_files(r".\issues\torch")
count = 0
all_user = []

def speical_keywords(text):
    for key in keyword:
        if text:
            if key in text.lower():
                return False
            else:
                continue
    return True


def extract_code_blocks(text):
    """
    提取文本中用 ``` 包围的代码块。

    参数:
    text (str): 输入文本

    返回:
    List[str]: 提取的代码块列表
    """
    # 匹配用 ``` 包围的代码块
    code_blocks = re.findall(r'```(.*?)```', text, re.DOTALL)
    pattern = r'https://colab\.research\.google\.com/drive/[a-zA-Z0-9_-]+'
    # 搜索匹配的模式
    colab_links = re.findall(pattern, text)

    return colab_links


def contains_bug_keywords(text):
    bug_keywords = [
        "crash", "aborted (core dumped)", "assertion failure", "segmentation fault (core dumped)", "segment fault",
        "segfault", "segment faults", "segfault",
        "aborted", "floating point exception", "floating point exception (core dumped)", "overflow",
        "aborted (core dumped)", "core dumped", "cve", "out of memory", "漏洞", "最小复现", "异常"
    ]
    # pattern = re.compile('|'.join(bug_keywords), re.IGNORECASE)
    for keys in bug_keywords:
        if text:
            if keys in text.lower():
                return True
            else:
                continue
    else:
        return False


for file_path in torch_files:
    logger.info("now handing file: " + file_path)

    with open(file_path, 'r') as file:
        # 加载单个json
        torch_json = json.load(file)
        # 判断json内容是否为空
        if torch_json is not {} and torch_json['items'] is not []:
            # 遍历json里面的issue
            for issue in torch_json['items']:
                # 在这这里过滤title和body
                # print(issue['html_url'])


                if contains_bug_keywords(issue['title']) or contains_bug_keywords(issue['body']):
                    usernames = issue['user']['login']
                    all_user.append(usernames)
                    content = issue['body']
                    # 判断issue里面是否存在内容
                    if content:
                        # 提取```code```
                        code_blocks = extract_code_blocks(content)
                        for code_block in code_blocks:
                            if code_block:
                                print(code_blocks)
                                count+=1
                                # 正则匹配过滤
                                # import_matches = import_pattern.findall(code_block)
                                # from_import_matches = from_import_pattern.findall(code_block)
                                # assignment_matches = assignment_pattern.findall(code_block)
                                # function_call_matches = function_call_pattern.findall(code_block)
                                # complete_error_matches = traceback_pattern.findall(code_block)

                                # if (import_matches is not []
                                #     or from_import_matches is not []
                                #     or assignment_matches is not []
                                #     or function_call_matches is not []) and complete_error_matches == []:
                                #
                                #     function_call_matches_string = json.dumps(function_call_matches)
                                #     # 再次过滤
                                #     with file_lock:
                                #         with open(r".\temp.py", "w", encoding="utf-8") as f:
                                #             f.write(code_block)
                                #         # 如果未通过编译，则丢弃
                                #         f.close()
                                #
                                #     flag, output = check_code("temp.py")
                                #
                                #     if flag == "SyntaxError":
                                #         pass
                                #
                                #     elif flag == "No SyntaxError":
                                #         logger.info(issue['html_url'])
                                #         logger.info("```")
                                #         logger.info(code_block)
                                #         logger.info("```")
                                #         count += 1
                                #         # logger.info("##############")
                                #
                                # logger.info("------------------------------------")

logger.info("count: " + str(count))
username_counts = Counter(all_user)

k = 100
top_k_usernames = username_counts.most_common(k)


for username, count in top_k_usernames:
    print(f'{username}: {count}')