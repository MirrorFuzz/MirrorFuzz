
import jittor as jt
from jittor import nn

# Set up the environment
data_format = "channels_last"
# Create the MaxPool3d layer with the appropriate parameters
pool_size = (2, 2, 2)
stride = (2, 2, 2)
padding = (0, 0, 0)
pool_func = nn.MaxPool3d(kernel_size=pool_size, stride=stride, padding=padding, data_format=data_format)

# Create an input tensor with the correct shape
input_tensor = jt.random([1, 5, 5, 5, 3])  # This should work with data_format="channels_last"

# Run the code
output_tensor = pool_func(input_tensor)

print(output_tensor.shape)
