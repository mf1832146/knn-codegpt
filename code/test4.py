# import json
#
# data = []
# with open('/Users/tangze/Downloads/test.txt', 'r') as f:
#     for line in f.readlines():
#         x = json.loads(line)
#         data.append(x['token_type'])
#
# statics = {}
#
# type_num = {}
# total_num = 0
#
# for d in data:
#     for i, e in enumerate(d):
#         total_num += 1
#         if i > 0:
#             cur_type = d[i]
#             before_type = d[i-1]
#
#             if cur_type not in type_num:
#                 type_num[cur_type] = 0
#             type_num[cur_type] += 1
#
#             if cur_type not in statics:
#                 statics[cur_type] = {}
#
#             if before_type not in statics[cur_type]:
#                 statics[cur_type][before_type] = 0
#             statics[cur_type][before_type] += 1
#
# for k in statics.keys():
#     k_num = type_num[k]
#     for t in statics[k].keys():
#         statics[k][t] = statics[k][t] / k_num
#
# print({k:v/total_num for k, v in type_num.items()})
#
#
#
# print(statics)

import numpy as np

d = np.array([1,2,3])
e = np.array([0]* 10)

d = np.concatenate([e, d], axis=0)

print(d)
print(d[1:])