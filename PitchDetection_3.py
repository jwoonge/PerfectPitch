from Sound_ds import sound
from Score_ds import score
import os
import math
import numpy as np
from scipy import signal
from scipy import fftpack


import time
import matplotlib.pyplot as plt
import seaborn as sns

def Show_Distribution(input_spec):
    maxes = []
    for i in range(len(input_spec)):
        maxes.append(max(input_spec[i]))
    maxZ = int(max(maxes))
    distribution = [0 for i in range(maxZ+5)]
    for i in range(len(input_spec)):
        for j in range(len(input_spec[i])):
            distribution[int(input_spec[i][j])] += 1
    
    plt.plot(distribution)
    plt.plot([0,len(distribution)],[0,0])
    plt.show()

def Show_Spectrogram(input_Spec, vmin=0, vmax=150, input_list_c = [], input_list_r = [], transpose = True):
    ''' input : Spectogram [] '''
    plt.figure(figsize=(35,3))
    if transpose:
        ax = sns.heatmap(np.transpose(input_Spec), vmin=vmin,vmax=vmax,cmap=sns.cm.rocket)
    else:
        ax = sns.heatmap(input_Spec, vmin=vmin,vmax=vmax,cmap=sns.cm.rocket)
    ax.invert_yaxis()
    maxValue = len(input_Spec[0])
    minValue = 0
    for i in range(len(input_list_c)):
        plt.plot([input_list_c[i],input_list_c[i]],[minValue,maxValue],'c')
    for i in range(len(input_list_r)):
        plt.plot([input_list_r[i],input_list_r[i]],[minValue,maxValue],'r')

    plt.show()


def get_key_freq(key_count=88):
    center_a = 48
    key_freq = {i:0 for i in range(key_count)}
    diff = [i-center_a for i in range(key_count)]

    for i in range(len(key_freq)):
        key_freq[i] = 440 * math.pow(2, diff[i] * (1/12.0))
    output_dict = {v:k for k,v in key_freq.items()}

    return output_dict

def get_freq_dict(freq_range, tuning_rate=1):
    dictionary = [0 for i in range(freq_range)]
    for i in range(len(dictionary)):
        dictionary[i] = get_near_pitch_num(int(i*tuning_rate))
    return dictionary

def get_near_pitch_num(freq):
    keys = np.array(list(get_key_freq()))
    if freq <= max(keys) and freq >= min(keys):
        idx = np.abs(keys - freq)
        idx = idx.argmin()
    else:
        idx = -1
    return idx

class pd_processor:
    def __init__(self):
        self.dict = get_key_freq()
        self.key_freq = list(self.dict)

    def do(self, input_pcm):
        self.pcm = input_pcm
        self.sample_rate = input_pcm.sample_rate
        self.get_spectrogram()
        self.result = score(self.sample_rate, self.time_resolution)
        self.detect_pitches3()
        #self.result.print_notes()
        self.result.make_midi()

    def get_spectrogram(self):
        start_t = time.time()
        print("Calc Spectrogram...")
        freq_resolution = self.key_freq[1]-self.key_freq[0]
        n = int(self.pcm.sample_rate / freq_resolution)
        freq_resolution = self.pcm.sample_rate / n
        overlap_rate = 0.95
        time_resolution_rate = 1-overlap_rate
        self.time_resolution = n / self.pcm.sample_rate * time_resolution_rate
        freq, t, Zxx = signal.stft(self.pcm.data, self.pcm.sample_rate, nperseg = n, noverlap = int(n*overlap_rate))
        # Zxx : [freq][time]
        Zxx = np.transpose(np.abs(Zxx))
        self.dict = get_freq_dict(len(Zxx[0]), 1.00)
        ### 0.97 조율 비율 찾아주는 기능 개발해야 함 ###
        end_t = time.time()
        print("\t Fourier Transform Complete", end_t-start_t)

        start_t = time.time()
        spec_th = 3

        ###################분포 확인####################3
        #Show_Distribution(Zxx)
        #################################################

        self.spec = [[0 for y in range(88)] for x in range(len(Zxx))]
        for i in range(len(Zxx)):
            for j in range(len(Zxx[0])):
                pitch = self.dict[j]
                if Zxx[i][j] > spec_th:
                    self.spec[i][pitch] += Zxx[i][j]
        del Zxx
        end_t = time.time()
        print('\t Generating freq-to-pitch Complete', end_t-start_t)
        start_t= time.time()
        max_spec = 0
        for i in range(len(self.spec)):
            tempmax = max(self.spec[i])
            if tempmax>max_spec:
                max_spec = tempmax

        for i in range(len(self.spec)):
            for j in range(len(self.spec[i])):
                self.spec[i][j] *= (127 / max_spec)
                self.spec[i][j] = int(self.spec[i][j])

        #self.spec = min_max_norm(self.spec)*127
        end_t = time.time()
        #Show_Spectrogram(self.spec, vmax=127)
        print("\t Generating Spectrogram Complete", end_t-start_t)
        print("\t sec per frame : ", self.time_resolution)

        #######################spect분포 조사############################
        #Show_Distribution(self.spec)
        ###########################################################


    
    def detect_pitches(self):
        pitch_map = [[0 for y in range(88)] for x in range(len(self.spec))]

        opt_th = 15
        len_th = 5 #frame 단위

        for i in range(len(self.spec)):
            temp_max = max(self.spec[i])
            for j in range(88):
                if self.spec[i][j] > temp_max/5 and self.spec[i][j] > opt_th:
                    pitch_map[i][j] = self.spec[i][j]

        for freq in range(88):
            start = 0
            i=0
            while i<len(pitch_map):
                if pitch_map[i][freq] !=0:
                    start = i
                    while pitch_map[i][freq] !=0 and i<len(pitch_map):
                        i+=1
                    end = i
                    if end-start > len_th:
                        self.result.push_note(freq+9, start, end, 100)
                        print(freq+9,start,end,100)
                else:
                    i+=1

    def detect_pitches2(self):
        peak_map = [[0 for y in range(88)] for x in range(len(self.spec))]
        opt_th = 5
        '''
        idea : threshold 를 구할때 확 튀는 음은 제거 - 전체에서 상위 10%를 기준으로 ? 

        '''
        for j in range(1,87):
            for i in range(1,len(self.spec)-1):
                if (self.spec[i-1][j-1] < self.spec[i][j] and self.spec[i-1][j+1] < self.spec[i][j]
                and self.spec[i][j-1] < self.spec[i][j] and self.spec[i][j+1] < self.spec[i][j]
                and self.spec[i+1][j-1] < self.spec[i][j] and self.spec[i+1][j+1] < self.spec[i][j]
                and self.spec[i-1][j] < self.spec[i][j] and self.spec[i+1][j] < self.spec[i][j]):
                    peak_map[i][j] = self.spec[i][j]
        
        Show_Spectrogram(peak_map,vmax=127) ######################### local muximum
        count_th = 0
        count_same = 0
        same_frame = int(0.1/self.time_resolution)
        for i in range(same_frame):
            for j in range(len(peak_map[0])):
                peak_map[i][j] = 0
        for i in range(len(peak_map)-same_frame, len(peak_map)):
            for j in range(len(peak_map[0])):
                peak_map[i][j] = 0

        for i in range(len(peak_map)-same_frame):
            mask_maxes = []
            for j in range(-1*same_frame, same_frame):
                mask_maxes.append(max(peak_map[i+j]))
            mask_max_peak = max(mask_maxes)
            for j in range(len(peak_map[0])):
                if peak_map[i][j]<opt_th:
                    peak_map[i][j] = 0
                    count_th+=1
                if peak_map[i][j] < mask_max_peak/100:
                    peak_map[i][j] = 0
                    count_same+=1

        Show_Spectrogram(peak_map, vmax=127) ######################### same frame 제거
        
        for i in range(len(peak_map)):
            for j in range(len(peak_map[0])):
                if peak_map[i][j] !=0:
                    self.result.push_note(j+9, i, i+10, 100)
                    print(j, i)
        print("count_th = ",count_th,"\tcount_same = ",count_same)

    def detect_pitches3(self):
        '''
        th = 10
        for i in range(len(self.spec)):
            for j in range(len(self.spec[i])):
                if self.spec[i][j] >th:
                    self.result.push_note(j+9,i,i+10,100)
                    print(i,j)

        '''

        ######### 이건 평균의 두배 안되는 넘들 지운것 #############
        for i in range(len(self.spec)):
            avg_frame = sum(self.spec[i])/88 *2.5
            for j in range(len(self.spec[i])):
                count = 0
                if self.spec[i][j] > avg_frame:
                    count += 1
            if count<20:
                for j in range(len(self.spec[i])):
                    if self.spec[i][j] < avg_frame:
                        self.spec[i][j] = 0
        
        len_th = int(0.1/self.time_resolution)
        del_count = 0
        for freq in range(88):
            start = 0
            i=0
            while i<len(self.spec):
                if self.spec[i][freq] >0:
                    start = i
                    while self.spec[i][freq] >0 and i<len(self.spec):
                        i+=1
                    end = i
                    if end-start > len_th:
                        self.result.push_note(freq+9, start, end, 100)
                        print(freq+9,start,end,100)
                    else:
                        del_count += 1
                else:
                    i+=1
        print(del_count)

        ### TODO: 배수 감쇄 해보자
        # 각 계이름별로 배열 만들어서 그중에 가장 큰 값 찾음, 그리고 나머지를 감쇄해서 뭐 절반 안되면 삭제 #

        '''
        max_rate = 0.3
        maxes = [max_rate * max(self.spec[i]) for i in range(len(self.spec))]
        th = 10
        del_count = 0
        len_th = 1
        for freq in range(88):
            start = 0
            i=0
            while i<len(self.spec):
                if self.spec[i][freq] >th and self.spec[i][freq] > maxes[i]:
                    start = i
                    while self.spec[i][freq] >th and i<len(self.spec):
                        i+=1
                    end = i
                    if end-start > len_th:
                        self.result.push_note(freq+9, start, end, 100)
                        print(freq+9,start,end,100)
                    else:
                        del_count += 1
                else:
                    i+=1
        print(del_count)
        '''
        

    
#test_sound = sound('test.mp3')
#test_sound2 = sound('test2.mp3')
#test_sound3 = sound('https://www.youtube.com/watch?v=EeX8RWgq4Gs') #레헬른
#test_sound3 = sound('bmajor.mp3')
test_sound3 = sound('https://www.youtube.com/watch?v=6vo66K06wFU') #아르카나
#test_sound3 = sound('https://www.youtube.com/watch?v=22jE6FdYjxE') #왕벌
#test_sound3 = sound('https://www.youtube.com/watch?v=w-4xH2DLv8M') #작은별
pdp = pd_processor()
pdp.do(test_sound3)