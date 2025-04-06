
import oneflow as flow
import numpy as np
import matplotlib.pyplot as plt

# Set the random seed for reproducibility
flow.manual_seed(4)

# Define the Laplacian matrix for a 1D grid
def lap1d(n, dtype=np.float64):
    v = np.ones(n, dtype=dtype)
    L1 = sparse.spdiags([-v, 2 * v, -v], [-1, 0, 1], n, n)
    return L1

n = 50000  # 40000 would be fine
A_sp = lap1d(n).tocsr()

A = flow.sparse_csr_tensor(A_sp.indptr, A_sp.indices, A_sp.data, A_sp.shape, dtype=flow.float64)
# A = A.to_sparse_coo()  # If converted to COO it would be fine.
x = flow.Parameter(flow.rand(n, dtype=flow.float64))

def loss(x, A):
    x = flow.nn.SiLU()(x)
    return (A @ x).norm()

numerical = []
perturb = np.logspace(-8, 0, 50)
with flow.no_grad():
    for eps in perturb:
        L_p = loss(x + eps, A)
        L_m = loss(x - eps, A)
        numerical.append((L_p - L_m) / (2 * eps))
numerical = np.array(numerical)

L = loss(x, A)
L.backward()
dLdx = x.grad.sum().item()
err = np.abs(numerical - dLdx) / np.abs(dLdx)

plt.loglog(perturb, err)
plt.xlabel('epsilon')
plt.ylabel('Relative error')
plt.grid()
plt.savefig("finite_difference.png")
