import math
import matplotlib.pyplot as plt
import numpy as np

x = [0.01 * i for i in range(0,1000)]
y_sin = [math.sin(j*math.pi) for j in x]

y2_sin = [math.sin(j*math.pi * 2) for j in x]

y3_sin = [3* math.sin(j*math.pi) for j in x]

sumy = []
for i in range(1000):
    sumy.append(3*y_sin[i] + y2_sin[i])

def FFT(input_frame, frame_size):
    NFFT = frame_size
    Y = np.fft.fft(input_frame)/NFFT
    Y = Y[range(math.trunc(NFFT/4))]
    fft = 2*abs(Y)
    return fft

fft = FFT(y_sin, 1000)
fft2 = FFT(y2_sin, 1000)
fft3 = FFT(sumy, 1000)
fft4 = FFT(y3_sin, 1000)
print(fft)
print(fft2)
print(fft3)
#print(fft4)

plt.figure(figsize=(35,3))
plt.plot(x,y_sin)
plt.show()

'''
실험결과
진폭이 두배가 되면 fft값도 두 배가 된다.
3x+2y 를 하면 x 주파수가 3, y 주파수가 2가 제대로 나옴
그러면 진폭-체감 소리 크기가 로그 스케일인가? 그럼 그거 적용해보자
'''