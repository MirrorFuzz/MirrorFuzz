import oneflow as flow

def test_oneflow():
    # Check OneFlow version
    print(f"OneFlow Version: {flow.__version__}")

    # Check if GPU is available
    gpu_available = flow.cuda.is_available()
    if gpu_available:
        print("GPU is available")
        print(f"GPU Device: {flow.cuda.get_device_name(0)}")
    else:
        print("GPU is not available")

    # Run a simple OneFlow computation
    print("\nRunning a simple OneFlow operation...")
    try:
        a = flow.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=flow.float32)
        b = flow.tensor([[5.0, 6.0], [7.0, 8.0]], dtype=flow.float32)
        c = flow.matmul(a, b)  # Matrix multiplication
        print("Matrix multiplication result:")
        print(c.numpy())
        print("OneFlow is working correctly!")
    except Exception as e:
        print(f"OneFlow operation failed: {e}")

if __name__ == "__main__":
    test_oneflow()
