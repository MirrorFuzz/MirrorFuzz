
import tensorflow as tf

# Ensure both tensors have the same shape and type
x = tf.constant([[1, 2], [3, 4]], dtype=tf.complex64)
y = tf.constant([[1, 2]], dtype=tf.complex64)  # Adjust the shape of y to match x

# Define the fft_length parameter as a tensor of integers
fft_length = tf.constant([2, 2], dtype=tf.int32)  # Assuming 2D transformation

# Call the ifftnd function with the two tensors and the fft_length parameter
result = tf.signal.ifftnd(x, fft_length)

# Print the result
print(result)
