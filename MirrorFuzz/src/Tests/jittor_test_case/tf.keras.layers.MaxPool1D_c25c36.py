
import jittor as jt
from jittor import nn

# Set the data format to "channels_first" manually
data_format = "channels_first"

# Create an input tensor with the correct shape (N, C, D, H, W)
N = 1
C = 3
D = 5
H = 5
W = 5
input_tensor = jt.random([N, C, D, H, W])

# Define the MaxPool3d parameters
kernel_size = 2
stride = 2
padding = 1
dilation = None
return_indices = False
ceil_mode = False

# Create the MaxPool3d layer
pool_func = nn.MaxPool3d(kernel_size=kernel_size, stride=stride, padding=padding, dilation=dilation, return_indices=return_indices, ceil_mode=ceil_mode)

# Apply the pooling operation
output_tensor = pool_func(input_tensor)

# Print the output shape
print(output_tensor.shape)
