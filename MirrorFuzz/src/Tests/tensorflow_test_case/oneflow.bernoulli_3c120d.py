
import tensorflow as tf
import numpy as np

def code():
    arg_0_tensor = np.random.uniform(-8, 2048, [2, 3])
    arg_0_tensor = tf.convert_to_tensor(arg_0_tensor, dtype=tf.complex64)
    print(tf.signal.ifftnd(arg_0_tensor))

if __name__ == "__main__":
    code()
