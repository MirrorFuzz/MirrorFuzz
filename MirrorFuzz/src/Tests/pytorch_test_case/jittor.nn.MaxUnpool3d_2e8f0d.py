
import torch
import torch.nn.functional as F

# Trigger bug for unfold
unfold = F.unfold(torch.randn(1, 3, 5, 5), kernel_size=-1, stride=-1)
print(unfold)

# Trigger bug for unfold
unfold = F.unfold(torch.randn(1, 3, 5, 5, 5), kernel_size=-1, stride=1)
print(unfold)
