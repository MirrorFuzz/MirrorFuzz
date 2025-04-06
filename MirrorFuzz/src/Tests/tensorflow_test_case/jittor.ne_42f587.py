
import tensorflow as tf

# Create two tensors of different types
x = tf.constant([[1, 2], [3, 4]], dtype=tf.complex64)
y = tf.constant([1, 2], dtype=tf.float32)

# Call the ifftnd function with the two tensors
result = tf.signal.ifftnd(x, y)

# Print the result
print(result)
