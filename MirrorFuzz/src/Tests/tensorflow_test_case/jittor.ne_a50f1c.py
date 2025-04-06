
import tensorflow as tf

# Create two tensors of different shapes
x = tf.constant([[1, 2], [3, 4]], dtype=tf.complex64)
y = tf.constant([1, 2], dtype=tf.complex64)

# Call the ifftnd function with the two tensors
result = tf.signal.ifftnd(x, y)

# Print the result
print(result)
