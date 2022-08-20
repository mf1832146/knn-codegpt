

import numpy as np


def get_rand():
    return np.random.rand(10) * 3

def norm(x):
    return (x - x.mean()) / np.std(x) / np.sqrt(10)


a = norm(get_rand())
a = np.expand_dims(a, 0)

for i in range(10):
    b = norm(get_rand())
    c = norm(get_rand())
    e = norm(get_rand())
    b = np.expand_dims(b, 0)
    c = np.expand_dims(c, 0)
    e = norm(get_rand())

    ab = np.matmul(a, b.transpose())
    ac = np.matmul(a, c.transpose())
    bc = np.matmul(b, c.transpose())
    c2 = np.matmul(c, c.transpose())
    ae = np.matmul(a, e.transpose())
    be = np.matmul(b, e.transpose())
    #print(c2)
    print(2 * ab - (ac*bc + be*ae))

