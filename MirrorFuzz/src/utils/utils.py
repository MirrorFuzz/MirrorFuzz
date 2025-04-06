import os
import shutil
import signal

import subprocess

import time
from datetime import datetime

import requests
import json

from enum import IntEnum, auto
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Levenshtein import distance as levenshtein_distance


def ensure_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory {directory_path} created.")
    else:
        pass
        print(f"Directory {directory_path} already exists.")


# Example usage
class ExecutionStatus(IntEnum):
    SUCCESS = auto()
    EXCEPTION = auto()
    CRASH = auto()
    NOTCALL = auto()
    TIMEOUT = auto()


def run_cmd(
        cmd_args,
        timeout=10,
        verbose=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,

) -> (ExecutionStatus, str):
    try:
        output = subprocess.run(
            cmd_args, stdout=stdout, stderr=stderr, timeout=timeout, shell=shell
        )
    except subprocess.TimeoutExpired as te:
        if verbose:
            print("Timed out")
        return ExecutionStatus.TIMEOUT, ""
    else:
        if verbose:
            print("output.returncode: ", output.returncode)
            print("---------------------------------")
            print(output.stdout)
        if output.returncode != 0:

            if output.stdout is not None:
                stdout_msg = output.stdout.decode("utf-8")
                stderr_msg = output.stderr.decode("utf-8")
                if verbose:
                    print("stdout> ", stdout_msg)
                if verbose:
                    print("stderr> ", stderr_msg)
                stdout_msg = stdout_msg[:30]
                error_msg = "---- returncode={} ----\nstdout> {}\nstderr> {}\n".format(
                    output.returncode, stdout_msg, stderr_msg
                )

            if output.returncode == 134:
                return ExecutionStatus.CRASH, "SIGABRT Triggered\n" + error_msg
            elif output.returncode == 132:
                return ExecutionStatus.CRASH, "SIGILL\n" + error_msg
            elif output.returncode == 133:
                return ExecutionStatus.CRASH, "SIGTRAP\n" + error_msg
            elif output.returncode == 136:
                return ExecutionStatus.CRASH, "SIGFPE\n" + error_msg
            elif output.returncode == 137:
                return ExecutionStatus.CRASH, "OOM\n" + error_msg
            elif output.returncode == 138:
                return ExecutionStatus.CRASH, "SIGBUS Triggered\n" + error_msg
            elif output.returncode == 139:
                return (
                    ExecutionStatus.CRASH,
                    "Segmentation Fault Triggered\n" + error_msg,
                )
            else:
                if output.returncode != 1:

                    print("output.returncode: ", output.returncode)
                    print(cmd_args)
                    print("stdout> ", stdout_msg)
                    print("stderr> ", stderr_msg)
                    return ExecutionStatus.CRASH, error_msg
                else:
                    return ExecutionStatus.EXCEPTION, error_msg
        else:
            if verbose:
                stdout_msg = output.stdout.decode("utf-8")
                print("stdout> ", stdout_msg)
            return ExecutionStatus.SUCCESS, ""


def query_llm(messages, model="CodeLlama-7B-Instruct-AWQ", api="openai", ip='192.168.1.1', port='8000'):
    if api == "openai":
        url = f"http://{ip}:{port}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": messages
        }
    elif api == "vllm":
        url = f"http://{ip}:{port}/generate"
        data = {
            "prompt": messages,
            # "logprobs": 1,
            # "max_tokens": 256,
            # "temperature": 1,
            # "use_beam_search": False,
            # "top_p": 0,
            # "top_k": 1,
            # "stop": "<eod>",
        }
        data = json.dumps(data)
        headers = {
            "Content-Type": "application/json",
        }

    start_time = time.time()
    status = 'SUCCESS'
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
    except Exception as e:
        return "LLM Error"
    end_time = time.time()
    elapsed_time = end_time - start_time
    if response.status_code == 200:
        result = response.json()

    else:

        print(response.content)
        status = 'FAILED'

        result = response.content
        return result, elapsed_time, status

    return result, elapsed_time, status


def list_files(directory):
    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            yield file_path


def file_exists(directory, filename):
    return os.path.isfile(os.path.join(directory, filename))


def check_code(script_name):
    cmd_args = ["python", script_name]

    try:

        result = subprocess.Popen(
            cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            stdout_output, stderr_output = result.communicate(timeout=60)
            stdout_output = stdout_output.decode('utf-8', errors='ignore')
            stderr_output = stderr_output.decode('utf-8', errors='ignore')

        except subprocess.TimeoutExpired:
            # os.kill(result.pid, signal.SIGKILL)
            return "TimeOut", ""

    except Exception as e:
        print(e)
        return "Pass", ""

    if "SyntaxError" in stderr_output or "IndentationError" in stderr_output:
        return "SyntaxError", (stdout_output, stderr_output)
    else:
        return "No SyntaxError", (stdout_output, stderr_output)


def contains_bug_keywords(text):
    bug_keywords = [
        "crash", "aborted (core dumped)", "assertion failure", "segmentation fault (core dumped)", "segment fault",
        "segfault", "segment faults", "segfault", "(core dumped)", "core dumped", "core dump", "segfault", "abort",
        "aborted", "floating point exception", "floating point exception (core dumped)", "overflow", 'ASSERT FAILED',
        "aborted (core dumped)", "core dumped", "cve", "out of memory", "漏洞", "最小复现", "异常", "错误",

        # "buffer","overflow", "integer overflow", "integer underflow", "heap buffer", "stack overflow", "null pointer dereference",
        # "wrong result", "unexpected output", "incorrect calculation", "inconsistent behavior", "unexpected behavior", "incorrect logic", "wrong calculation",
        #  "race condition", "memory leak"

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


def folder_exists(path):
    """
    Check if the given path is an existing directory.

    :param path: The path to check.
    :return: True if the path exists and is a directory, False otherwise.
    """
    return os.path.exists(path) and os.path.isdir(path)


def get_now_time():
    now = datetime.now()
    # 输出当前日期和时间
    formatted_now = now.strftime("%Y%m%d%H%M%S")
    return formatted_now


def create_directory(path):
    """
    Create a new directory at the specified path.

    :param path: The path of the directory to create.
    :return: None
    """
    try:

        os.makedirs(path, exist_ok=True)
    except OSError as e:
        print(f"Failed to create directory '{path}': {e}")


def clear_folder(folder_path):
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
    else:
        print(f"路径 {folder_path} 不存在或不是一个文件夹！")


def list_subdirectories(directory):
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"{directory} is not a directory")

    subdirectories = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

    return subdirectories


def calculate_levenshtein_similarity(target_api, api_list):
    levenshtein_distances = [levenshtein_distance(target_api, api) for api in api_list]
    max_distance = max(levenshtein_distances) if levenshtein_distances else 1
    levenshtein_similarities = [1 - (dist / max_distance) for dist in levenshtein_distances]
    return levenshtein_similarities


def calculate_tfidf_similarity(target_api, api_list):
    documents = [target_api] + api_list
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    return cosine_similarities


def calculate_weighted_similarity(target_api, api_list, levenshtein_weight=0.5, tfidf_weight=0.5):
    levenshtein_similarities = calculate_levenshtein_similarity(target_api, api_list)
    tfidf_similarities = calculate_tfidf_similarity(target_api, api_list)
    weighted_similarities = (np.array(levenshtein_similarities) * levenshtein_weight +
                             np.array(tfidf_similarities) * tfidf_weight)
    return weighted_similarities


def get_top_k_similar_apis(target_api, api_list, similarities, K=1):
    top_k_indices = np.argsort(similarities)[-K:][::-1]
    top_k_similar_apis = [api_list[i] for i in top_k_indices]
    top_k_similarities = [similarities[i] for i in top_k_indices]
    return top_k_similar_apis, top_k_similarities


def get_uuid(size=6):
    import uuid

    unique_id = uuid.uuid4()
    uuid_str = str(unique_id)
    short_uuid = uuid_str[:size]
    return short_uuid
