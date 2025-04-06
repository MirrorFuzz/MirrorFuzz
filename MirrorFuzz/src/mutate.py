

torch_dtypes = [
    "torch.bfloat16",
    "torch.bit",
    "torch.bits16",
    "torch.bits1x8",
    "torch.bits2x4",
    "torch.bits4x2",
    "torch.bits8",
    "torch.bool",
    "torch.cdouble",
    "torch.cfloat",
    "torch.chalf",
    "torch.complex128",
    "torch.complex32",
    "torch.complex64",
    "torch.double",
    "torch.float",
    "torch.float16",
    "torch.float32",
    "torch.float64",
    "torch.float8_e4m3fn",
    "torch.float8_e4m3fnuz",
    "torch.float8_e5m2",
    "torch.float8_e5m2fnuz",
    "torch.half",
    "torch.int",
    "torch.int1",
    "torch.int16",
    "torch.int2",
    "torch.int3",
    "torch.int32",
    "torch.int4",
    "torch.int5",
    "torch.int6",
    "torch.int64",
    "torch.int7",
    "torch.int8",
    "torch.long",
    "torch.qint32",
    "torch.qint8",
    "torch.quint2x4",
    "torch.quint4x2",
    "torch.quint8",
    "torch.short",
    "torch.uint1",
    "torch.uint16",
    "torch.uint2",
    "torch.uint3",
    "torch.uint32",
    "torch.uint4",
    "torch.uint5",
    "torch.uint6",
    "torch.uint64",
    "torch.uint7",
    "torch.uint8"
]

tf_dtypes = [
    "tf.float32",
    "tf.float64",
    "tf.int32",
    "tf.int64",
    "tf.bool",
    "tf.string",
    "tf.complex64",
    "tf.complex128",
    "tf.uint8",
    "tf.int8",
    "tf.uint16",
    "tf.int16",
    "tf.uint32",
    "tf.uint64"
]

oneflow_dtypes = [
    "oneflow.bool",
    "oneflow.int8",
    "oneflow.uint8",
    "oneflow.float64",
    "oneflow.double",
    "oneflow.float32",
    "oneflow.float",
    "oneflow.float16",
    "oneflow.half",
    "oneflow.int32",
    "oneflow.int",
    "oneflow.int64",
    "oneflow.long"
]

jittor_dtypes = [
"float32", "float64", "float16","float","double",
"int8", "int16", "int32", "int64",
"uint8", "uint16", "uint32", "uint64", "bool","half"
]

int_values = [
    -2**63, -2**31, -2**16, -2**8, -1, 0, 1, 2**8-1, 2**16-1, 2**31-1, 2**63-1
]

float_values = [
    -1.7976931348623157e+308,
    -3.4028235e+38,
    -1e+10, -1.0, -1e-10,
    0.0,
    1e-10, 1.0, 1e+10,
    3.4028235e+38,
    1.7976931348623157e+308
]

float_special_values = [
    float("inf"),
    float("-inf"),
    float("nan")
]

uint8_values = [0, 1, 127, 128, 255]
int8_values = [-128, -1, 0, 1, 127]
int16_values = [-32768, -1, 0, 1, 32767]
int32_values = [-2147483648, -1, 0, 1, 2147483647]
int64_values = [-9223372036854775808, -1, 0, 1, 9223372036854775807]

bool_values = [False, True]



import random

def get_supported_dtypes(framework):
    if framework == "pytorch":
        return torch_dtypes
    elif framework == "tensorflow":
        return tf_dtypes
    elif framework == "jittor":
        return jittor_dtypes
    elif framework == "oneflow":
        return oneflow_dtypes
    else:
        return []

def generate_mutation_prompt(test_case, test_api, test_dlf, mutation_type):
    supported_dtypes = get_supported_dtypes(test_dlf)
    mutate_dtype = random.choice(supported_dtypes)
    prompt_templates = {
        "boundary_value": f"""
You are an expert in generating mutated test cases for deep learning APIs.
Please apply boundary value mutation on the specified API in the code below.

Insert edge-case values into inputs, such as:
- Special floats: `float('inf')`, `float('-inf')`, `float('nan')`
- Extremely large/small integers or floats: `-2**31`, `2**63-1`
- Typical edge constants: `-1`, `0`, `1`

Framework: {test_dlf}
API: {test_api}
Original test case:
{test_case}

Return a mutated version of this test case.
Respond in the following JSON format:
{{"code": "<mutated code here>"}}
""",

        "type_mutation": f"""
You are a test case mutation expert for deep learning frameworks.
Please perform type mutation on the specified API in the code below.

Your job:
- Randomly change the data types of one or more parameters (e.g., int32 → float16, float → bool)
- Use only types supported by: {test_dlf}
Supported dtypes: {mutate_dtype}

API: {test_api}
Original test case:
{test_case}

Return ONLY the mutated test case with type changes.
Respond in the following JSON format:
{{"code": "<mutated code here>"}}
""",
        "shape_dimension": f"""
You are a test assistant focused on shape and dimension mutations.
Please apply shape/dimension mutations on the specified API in the code below.

Modify tensor shapes by:
- Adding/removing dimensions
- Reshaping tensors with the same total elements
- Injecting empty shapes, scalars, or large shapes like `[1024, 1024]`

Framework: {test_dlf}
API: {test_api}
Original test case:
{test_case}

Return a shape-mutated version of this test case.
Respond in the following JSON format:
{{"code": "<mutated code here>"}}
"""
    }

    return prompt_templates[mutation_type]

def mutate_test_cases(test_case, test_api, test_dlf):
    """
    test_case: The original code snippet or function call (as a string)
    test_api: Targeted API name (e.g., torch.matmul)
    test_dlf: Deep learning framework name (e.g., torch, tensorflow, etc.)
    llm_interface: Function that takes a prompt string and returns LLM-generated result
    num_mutations: Number of mutated test cases to generate
    """
    mutation_types = ["boundary_value", "type_mutation", "shape_dimension"]

    mutation_type = random.choice(mutation_types)
    prompt = generate_mutation_prompt(test_case, test_api, test_dlf, mutation_type)


    return prompt

code_str = """
import oneflow as flow
m = flow.nn.AdaptiveAvgPool1d(-5)
input = flow.Tensor(np.random.randn(1, 64, 8))
m(input)
"""

print(mutate_test_cases(code_str, "flow.nn.AdaptiveAvgPool1d", "oneflow"))
