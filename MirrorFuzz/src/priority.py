import ast


def extract_api_calls(code_str, frameworks=("torch.", "tensorflow.", "jittor.","oneflow.","tf.","jt.","flow.")):
    tree = ast.parse(code_str)
    api_calls = set()

    def is_framework_api(name):
        return any(name.startswith(fw) for fw in frameworks)

    def get_full_api_name(node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{get_full_api_name(node.value)}.{node.attr}"
        return ""

    for node in ast.walk(tree):
        # 处理直接调用情况，如 torch.tensor()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                api_name = get_full_api_name(node.func)
                if is_framework_api(api_name):
                    api_calls.add(api_name)
            elif isinstance(node.func, ast.Name):
                api_name = node.func.id
                if is_framework_api(api_name):
                    api_calls.add(api_name)

        # 处理类实例化情况，如 torch.nn.ReLU()
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)):
            api_name = get_full_api_name(node.func)
            if is_framework_api(api_name):
                api_calls.add(api_name)

        # 处理属性访问情况，如 .to()
        if isinstance(node, ast.Attribute):
            api_name = get_full_api_name(node)
            if is_framework_api(api_name):
                api_calls.add(api_name)

    return api_calls, len(api_calls)


# test_code
code_str = """
import oneflow as flow
m = flow.nn.AdaptiveAvgPool1d(-5)
input = flow.Tensor(np.random.randn(1, 64, 8))
m(input)
"""

def standardize_api_prefix(api_calls):
    framework_mapping = {
        "oneflow": "oneflow",
        "flow": "oneflow",
        "tf": "tf",
        "tensorflow": "tf",
        "torch": "torch",
        "jittor": "jittor",
        "jt": "jittor"
    }

    standardized_apis = set()
    for api in api_calls:
        parts = api.split(".")
        if parts[0] in framework_mapping:
            parts[0] = framework_mapping[parts[0]]  # 替换前缀
        standardized_apis.add(".".join(parts))

    return standardized_apis


def Priority(test_api, exec_time, test_case, test_dlf):
    prefix_dlf = ()
    G = False
    max_api_count = 30
    max_exec_time = 45

    if test_dlf == "tensorflow":
        prefix_dlf = ("tf.", "tensorflow.")
    elif test_dlf == "torch":
        prefix_dlf = ("torch.",)
    elif test_dlf == "jittor":
        prefix_dlf = ("jittor.", "jt.")
    elif test_dlf == "oneflow":
        prefix_dlf = ("oneflow.", "flow.")


    api_call_list, api_count = extract_api_calls(test_case, prefix_dlf)
    standardized_apis = standardize_api_prefix(api_call_list)
    if test_api in standardized_apis:
        G = True


    U = api_count / max_api_count
    C = exec_time / max_exec_time


    score = G * (U - C)
    return score