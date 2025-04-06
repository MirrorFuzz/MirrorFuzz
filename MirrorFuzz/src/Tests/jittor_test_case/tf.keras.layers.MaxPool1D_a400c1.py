
import jittor as jt
from jittor import nn

# Set up the environment
data_format = "channels_first"
# This will cause a bug because MaxPool3d does not support data_format="channels_first" with 3D tensors
# jittor.nn.MaxPool3d does not support this configuration
# pool_size = (2, 2, 2)
# stride = (2, 2, 2)
# padding = (0, 0, 0)
# pool_func = nn.MaxPool3d(kernel_size=pool_size, stride=stride, padding=padding, data_format=data_format)

# Instead, let's use the correct data format and dimensions
data_format = "channels_last"
pool_size = (2, 2, 2)
stride = (2, 2, 2)
padding = (0, 0, 0)
pool_func = nn.MaxPool3d(kernel_size=pool_size, stride=stride, padding=padding, data_format=data_format)

# Create an input tensor with incorrect dimensions
input_tensor = jt.random([1, 3, 5, 5, 5])  # This should work with data_format="channels_last"
# input_tensor = jt.random([1, 5, 3, 5, 5])  # This should fail with data_format="channels_last"

# Run the code
output_tensor = pool_func(input_tensor)

print(output_tensor.shape)
