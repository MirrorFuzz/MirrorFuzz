import jittor as jt

def test_jittor():
    # Set Jittor computation mode (automatically select GPU or CPU)
    jt.flags.use_cuda = jt.has_cuda

    # Check Jittor version
    print(f"Jittor Version: {jt.__version__}")

    # Check if GPU is available
    if jt.has_cuda:
        print("GPU is available")
    else:
        print("GPU is not available, running on CPU")

    # Run a simple Jittor computation
    print("\nRunning a simple Jittor operation...")
    try:
        a = jt.array([[1.0, 2.0], [3.0, 4.0]])
        b = jt.array([[5.0, 6.0], [7.0, 8.0]])
        c = jt.matmul(a, b)  # Matrix multiplication
        print("Matrix multiplication result:")
        print(c.numpy())
        print("Jittor is working correctly!")
    except Exception as e:
        print(f"Jittor operation failed: {e}")

if __name__ == "__main__":
    test_jittor()
