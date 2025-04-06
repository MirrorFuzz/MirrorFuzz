from FlagEmbedding import BGEM3FlagModel

import numpy as np


def cosine_similarity(embeddings_1, embeddings_2):
    norm_1 = np.linalg.norm(embeddings_1, axis=1, keepdims=True)
    norm_2 = np.linalg.norm(embeddings_2, axis=1, keepdims=True)
    similarity = (embeddings_1 @ embeddings_2.T) / (norm_1 * norm_2.T)
    return similarity



model = BGEM3FlagModel('../LLMs/BAAI/bge-m3',
                       use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation

sentences_1 = ["汽车"]
sentences_2 = ["car",
               "自行车",
               "火车",
               "automobile",
               "test"]

embeddings_1 = model.encode(sentences_1,
                            batch_size=12,
                            max_length=8192, # If you don't need such a long length, you can set a smaller value to speed up the encoding process.
                            )['dense_vecs']
embeddings_2 = model.encode(sentences_2)['dense_vecs']
print(embeddings_1)
print("...")
print(embeddings_2)
print("...")
similarity = embeddings_1 @ embeddings_2.T
print(similarity)
print("...")
cosine_sim = cosine_similarity(embeddings_1, embeddings_2)
print(cosine_sim)

# [[0.6265, 0.3477], [0.3499, 0.678 ]]