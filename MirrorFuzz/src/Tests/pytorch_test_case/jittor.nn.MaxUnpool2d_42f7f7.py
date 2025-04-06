
import torch
import torch.nn.functional as F

# Example 1: Positive kernel size
try:
    input_tensor = torch.randn(1, 3, 5, 5)
    unfolded = F.unfold(input_tensor, kernel_size=2, stride=1)
    print("Example 1: Success")
except ValueError as e:
    print(f"Caught an error: {e}")

# Example 2: Positive stride
try:
    input_tensor = torch.randn(1, 3, 5, 5)
    unfolded = F.unfold(input_tensor, kernel_size=2, stride=2)
    print("Example 2: Success")
except ValueError as e:
    print(f"Caught an error: {e}")

# Example 3: Matching kernel size and stride dimensions
try:
    input_tensor = torch.randn(1, 3, 5, 5)
    unfolded = F.unfold(input_tensor, kernel_size=[2, 3], stride=[2, 1])
    print("Example 3: Success")
except ValueError as e:
    print(f"Caught an error: {e}")
