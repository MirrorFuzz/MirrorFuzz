
import torch
import torch.nn.functional as F

def safe_unfold(input, kernel_size, stride):
    if kernel_size <= 0 or stride <= 0:
        raise ValueError("kernel_size and stride must be greater than zero")
    return F.unfold(input, kernel_size, stride)

# Trigger bug for unfold
try:
    unfold = safe_unfold(torch.randn(1, 3, 5, 5), kernel_size=-1, stride=-1)
    print(unfold)
except ValueError as e:
    print(e)

# Trigger bug for unfold
try:
    unfold = safe_unfold(torch.randn(1, 3, 5, 5, 5), kernel_size=-1, stride=1)
    print(unfold)
except ValueError as e:
    print(e)
