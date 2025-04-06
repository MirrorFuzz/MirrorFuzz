
import torch
import torch.nn.functional as F

# Example 1: Negative kernel size
try:
    input_tensor = torch.randn(1, 3, 5, 5)
    unfolded = F.unfold(input_tensor, kernel_size=-1, stride=1)
except ValueError as e:
    print(f"Caught an error: {e}")

# Example 2: Negative stride
try:
    input_tensor = torch.randn(1, 3, 5, 5)
    unfolded = F.unfold(input_tensor, kernel_size=2, stride=-1)
except ValueError as e:
    print(f"Caught an error: {e}")

# Example 3: Non-matching kernel size and stride dimensions
try:
    input_tensor = torch.randn(1, 3, 5, 5)
    unfolded = F.unfold(input_tensor, kernel_size=[2, 3], stride=[2, 1, 1])
except ValueError as e:
    print(f"Caught an error: {e}")
