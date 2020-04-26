import math
import matplotlib.pyplot as plt
import numpy as np

def f_prime(a,b,c,x):
    if x==a:
        x+= math.e**(-64)
    return -c/(x-a)

def g_prime(a,b,c,x):
    if x==a:
        x+= math.e**(-64)
    return -c*log(x-a)-c*x/(x-a)+b

def f(a,b,c,x):
    if x==a:
        x+= math.e**(-64)
    return -c*log(x-a)+b

def log(x):
    if x!=0:
        return np.log(x)
    else:
        return 10000

x_s = [0.1*i for i in range(11)]
a_s = [-0.1*i for i in range(0,1000)]
b_s = [0.1*i for i in range(-1000,1000)]
c_s = [0.1*i for i in range(-100,100)]


for a in a_s:
    for b in b_s:
        for c in c_s:
            if abs(f(a,b,c,1)-0.08)<0.01 and abs(f(a,b,c,0.3)-1)<0.01:
                count = 0
                for x in x_s:
                    count += 1
                    if not(g_prime(a,b,c,x)>=0 and f_prime(a,b,c,x)<0):
                        break
                if count==len(x_s):
                    print(a,b,c)