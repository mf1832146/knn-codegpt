# from mpl_toolkits import mplot3d
# import numpy as np
# import matplotlib.pyplot as plt
#
# fig = plt.figure()
# ax = plt.axes(projection='3d')
#
# t = 100
# x = np.linspace(0.01, 0.99, t)
# y = np.linspace(0.01, 0.99, t)
# x, y = np.meshgrid(x, y)
#
# z = x * np.power(y / (x+y), 0.25)
# z =
# z_2 = 0.25 * y + 0.75 * x
#
# ax.plot_surface(x,y,z, rstride=1, cstride=1)
# ax.plot_surface(x,y,z_2, rstride=1, cstride=1)
# plt.show()
import torch

knn_scores = torch.Tensor([[0, 0.1, 0.9], [0.2, 0.5, 0.3]])
pred_scores = torch.Tensor([[0.2, 0.4, 0.4], [0.5, 0.3, 0.2]])

knn_mask = knn_scores != 0
# [batch_size, seq_len-1,vocab_size]
knn_sum = torch.sum(pred_scores * knn_mask, dim=-1, keepdim=True)  # [batch_size, seq_len-1, 1]
knn_scores = knn_scores * knn_sum
tmp_scores = pred_scores * torch.pow(knn_scores / (pred_scores + knn_scores), 0.25)
tmp_sum = torch.sum(tmp_scores * knn_mask, dim=-1, keepdim=True)
tmp_scores = tmp_scores / tmp_sum * knn_sum

total_scores = pred_scores * (~knn_mask) + tmp_scores * knn_mask

print(total_scores)

c = torch.Tensor([5,6,6]).cuda()
for d in c:
    print(d == 5)