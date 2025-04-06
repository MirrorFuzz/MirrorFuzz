import tensorflow as tf

def test_tensorflow():
    # Check TensorFlow version
    print(f"TensorFlow Version: {tf.__version__}")

    # Check if GPU is available
    gpu_available = tf.config.list_physical_devices('GPU')
    if gpu_available:
        print("GPU is available")
        print("List of GPU devices:")
        for gpu in gpu_available:
            print(f" - {gpu}")
    else:
        print("GPU is not available")

    # Run a simple TensorFlow operation to verify functionality
    print("\nRunning a simple TensorFlow operation...")
    try:
        a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
        b = tf.constant([[5.0, 6.0], [7.0, 8.0]])
        c = tf.matmul(a, b)
        print("Matrix multiplication result:")
        print(c.numpy())
        print("TensorFlow is working correctly!")
    except Exception as e:
        print(f"TensorFlow operation failed: {e}")

if __name__ == "__main__":
    test_tensorflow()