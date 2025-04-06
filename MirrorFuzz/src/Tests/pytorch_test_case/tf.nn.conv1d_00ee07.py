
import torch
import torch.nn.functional as F

def trigger_unfold_bug1():
    # Create a random input tensor with shape (1, 10, 1)
    ipt = torch.randn(1, 10, 1)
    
    # Set a filter size larger than the input size
    kernel_size = 20
    
    # Try to unfold the input tensor
    try:
        unfolded = F.unfold(ipt, kernel_size)
    except RuntimeError as e:
        print(f"Caught error: {e}")
    else:
        print("No error caught.")

def trigger_unfold_bug2():
    # Create a random input tensor with shape (1, 10, 1)
    ipt = torch.randn(1, 10, 1)
    
    # Set a stride too large
    stride = 100
    
    # Try to unfold the input tensor
    try:
        unfolded = F.unfold(ipt, kernel_size=2, stride=stride)
    except RuntimeError as e:
        print(f"Caught error: {e}")
    else:
        print("No error caught.")

# Trigger the bugs
trigger_unfold_bug1()
trigger_unfold_bug2()
