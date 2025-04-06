
import tensorflow as tf

# Ensure both tensors have the same shape and type
x = tf.constant([[1, 2], [3, 4]], dtype=tf.complex64)
y = tf.constant([[1, 10000000]], dtype=tf.float32)  # Adjust the shape of y to match x

# Call the ifftnd function with the two tensors
result = tf.signal.ifftnd(x, y)

# Print the result
print(result)
