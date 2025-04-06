import re

import requests
import json
import time
import json5
import demjson3

def query_llm(messages, model="Qwen2.5-Coder-7B-Instruct-AWQ", api="openai", ip='127.0.0.1', port='9999'):
    """
    Sends a request to the LLM and retrieves the response.

    :param messages: List of input messages (OpenAI format) or a string (vLLM format).
    :param model: Model name.
    :param api: API type, supports "openai" or "vllm".
    :param ip: Server IP address.
    :param port: Server port.
    :return: Response result, request time, and status.
    """
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
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "prompt": messages,
            # Additional parameters like max_tokens, temperature, etc., can be added if needed
        }

    start_time = time.time()
    status = 'SUCCESS'
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
    except Exception as e:
        print(f"Request failed: {e}")
        return "LLM Error", 0, 'FAILED'

    end_time = time.time()
    elapsed_time = end_time - start_time

    if response.status_code == 200:
        result = response.json()
    else:
        print(f"Request failed, status code: {response.status_code}")
        print(f"Response content: {response.text}")
        status = 'FAILED'
        result = response.text

    return result, elapsed_time, status


def test_model_n_times(n=10, api="openai",prompt="hello", ip='127.0.0.1', port='9999'):
    """
    Tests whether the LLM is running properly and sends requests n times to calculate the average response time.

    :param n: Number of requests.
    :param api: API type, supports "openai" or "vllm".
    """
    total_time = 0
    success_count = 0
    fail_count = 0

    for i in range(n):
        print(f"Request {i + 1}...")

        if api == "openai":
            messages = [
                {"role": "system",
                 "content": "You are a helpful and honest code assistant expert in Python."},
                {"role": "user", "content": prompt}
            ]
        elif api == "vllm":
            messages = "Hello, how are you?"

        result, elapsed_time, status = query_llm(messages, api=api, ip=ip, port=port)

        print(f"Response: {result['choices'][0]['message']['content']}")
        code = extract_code_blocks(result['choices'][0]['message']['content'], code_type="json")
        print(f"Code: {code}")
        try:
            exec(code)
        except Exception as e:
            print(e)
        if status == 'SUCCESS':
            success_count += 1
            total_time += elapsed_time
            print(f"Request successful, time taken: {elapsed_time:.2f} seconds")
        else:
            fail_count += 1
            print("Request failed")

        print("-" * 50)

    if success_count > 0:
        avg_time = total_time / success_count
        print(f"Requests completed, successes: {success_count}, failures: {fail_count}")
        print(f"Average response time: {avg_time:.2f} seconds")
    else:
        print("All requests failed, unable to calculate average response time.")


def extract_code_blocks(text, code_type="markdown"):
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




if __name__ == "__main__":

    print("Testing OpenAI-style API...")
    ip = '192.168.9.2'
    port = '9999'
    prompt = """

Question:You are a helpful and honest code assistant expert in Deep Learning Frameworks. Please generate code that can trigger similar bugs for the specified API, utilizing the bug data from the similar API. Think step-by-step as below examples.
Example Input:
Source Deep Learning Framework: OneFlow
Source API: flow.nn.ReflectionPad1d
Source API Documention: This operator pads the input tensor using the reflection of the input boundary. Parameters : padding
(Union[int,tuple]) – The size or bundary of padding, if is int uses the same padding in all dimension …
The source API has a similar API torch.nn.ReflectionPad2d in PyTorch.
They are operation-similar API pairs, performing the same operations and sharing similar parameters.
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
{
"code": "import oneflow as flow
flow.nn.ReflectionPad1d(padding=-8353862602220610428)(oneflow.ones((15,5)))"
}

Now, process the following input and return only JSON output:
Source Deep Learning Framework: pytorch
Source API: torch.ao.nn.quantized.dynamic.LSTMCell
Source API Documention: {'api_name': 'torch.ao.nn.quantized.dynamic.LSTMCell', 'api_signature': 'torch.ao.nn.quantized.dynamic.LSTMCell(*args, **kwargs)', 'api_description': 'A long short-term memory (LSTM) cell.', 'return_value': '', 'parameters': '', 'input_shape': '', 'code_example': ''}
The source API has a similar API torch.ao.nn.quantized.dynamic.GRUCell in pytorch.
They are operation-similar API pairs, performing the same operations and sharing similar parameters.
The similar API Documention: {'api_name': 'torch.ao.nn.quantized.dynamic.GRUCell', 'api_signature': 'torch.ao.nn.quantized.dynamic.GRUCell(input_size, hidden_size, bias=True, dtype=torch.qint8)', 'api_description': '', 'return_value': '', 'parameters': '', 'input_shape': '', 'code_example': ''}
The similar API’s buggy code:
```
import torch
from torch.ao.nn.quantized.dynamic import GRUCell

sequence_length = 10
batch_size = 1
input_features = 1
hidden_features = 1

input = torch.randn(sequence_length, batch_size, input_features)
hidden = torch.randn(sequence_length, batch_size, hidden_features)
gru_cell = GRUCell(input_features, hidden_features)
gru_cell(input, hidden)
```
Root cause of the bug: hidden state should have shape (batch_size, hidden_features) but got (sequence_length, batch_size, hidden_features).
List of parameters causing the bug: [hidden]
Task : Please generate code for torch.ao.nn.quantized.dynamic.LSTMCell that triggers similar bugs based on the root cause of torch.ao.nn.quantized.dynamic.GRUCell in pytorch.
"""
    test_model_n_times(n=10, api="openai",prompt=prompt,ip=ip,port=port)
