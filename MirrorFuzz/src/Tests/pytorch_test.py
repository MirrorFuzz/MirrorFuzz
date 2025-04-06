import torch

def test_pytorch():
    # Check PyTorch version
    print(f"PyTorch Version: {torch.__version__}")

    # Check if GPU is available
    gpu_available = torch.cuda.is_available()
    if gpu_available:
        print("GPU is available")
        print(f"GPU Device: {torch.cuda.get_device_name(0)}")
    else:
        print("GPU is not available")

    # Run a simple PyTorch computation
    print("\nRunning a simple PyTorch operation...")
    try:
        a = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
        b = torch.tensor([[5.0, 6.0], [7.0, 8.0]])
        c = torch.mm(a, b)  # Matrix multiplication
        print("Matrix multiplication result:")
        print(c.numpy())
        print("PyTorch is working correctly!")
    except Exception as e:
        print(f"PyTorch operation failed: {e}")

if __name__ == "__main__":
    test_pytorch()
