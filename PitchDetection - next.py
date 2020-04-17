from Sound_ds import sound
from Score_ds import score
import os
import math
import numpy as np
from scipy import signal
from scipy import fftpack

import matplotlib.pyplot as plt
import seaborn as sns

def LUT(pitch_num):
    gye = (pitch_num-3)%12
    oc = int((pitch_num-3)/12)
    gyeLUT = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    gye = gyeLUT[gye]
    return gye, oc
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


def min_max_norm(x,axis=None):
    min = x.min(axis=axis,keepdims=True)
    max = x.max(axis=axis,keepdims=True)
    result = (x-min)/(max-min)
    return result

def get_key_freq(key_count=88):
    center_a = 48
    key_freq = {i:0 for i in range(key_count)}
    diff = [i-center_a for i in range(key_count)]

    for i in range(len(key_freq)):
        key_freq[i] = 440 * math.pow(2, diff[i] * (1/12.0))
    output_dict = {v:k for k,v in key_freq.items()}

    return output_dict

class pd_processor:
    def __init__(self):
        self.dict = get_key_freq()
        self.key_freq = list(self.dict)

    def do(self, input_pcm):
        self.pcm = input_pcm
        self.sample_rate = input_pcm.sample_rate
        self.get_spectrogram()
        self.result = score(self.sample_rate, self.time_resolution)
        #self.detect_pitches()
        self.detect_pitches_2dim()
        #self.result.print_notes()
        self.result.make_midi()

    def get_velocity(self, pitch, frame):
        ret = 0
        for freq in range(len(self.spec[0])):
            if self.get_near_pitch_num(freq) == pitch:
                ret+=self.spec[frame][pitch]
        return int(ret)


    def get_near_pitch_num(self, freq):
        keys = np.array(list(self.dict.keys()))
        if freq <= max(keys) and freq >= min(keys):
            idx = np.abs(keys - freq)
            idx = idx.argmin()
        else:
            idx = -1
        return idx

    def get_spectrogram(self):
        print("Calc Spectrogram...", end=" ")
        freq_resolution = self.key_freq[1]-self.key_freq[0]
        n = int(self.pcm.sample_rate / freq_resolution)
        freq_resolution = self.pcm.sample_rate / n
        overlap_rate = 0.95
        time_resolution_rate = 1-overlap_rate
        self.time_resolution = n / self.pcm.sample_rate * time_resolution_rate
        freq, t, Zxx = signal.stft(self.pcm.data, self.pcm.sample_rate, nperseg = n, noverlap = int(n*overlap_rate))
        # Zxx : [freq][time]
        self.spec = np.transpose(min_max_norm(np.abs(Zxx))*127)
        #Show_Spectrogram(self.spec, vmax=127)
        print("Done")
        print("\t sec per frame : ", self.time_resolution)
        
    def detect_melody(self, th):
        peak_i = -1
        start = 0
        end = 0
        for i in range(len(self.spec)):
            maxv = 0
            peak_i = -1
            for j in range(len(self.spec[i])):
                if self.spec[i][j] > maxv:
                    maxv = self.spec[i][j]
                    peak_i = j
            if maxv>th :
                print("over threshold", end=' ')
                peak = self.get_near_pitch_num(peak_i)
                print(peak)
            else:
                peak = -1
            
            if peak>0 and peak != last_peak:
                #self.result.push_note(peak, i, i+1, maxv)
                self.result.push_note(peak, i, i+1, 100)
                print("detected")

            last_peak = peak
    
    def detect_pitches(self):
        peak_map = [[0 for y in range(len(self.spec[0]))] for x in range(len(self.spec))]
        opt_th = 10

        for j in range(len(self.spec[0])):
            temp_spec = []
            for i in range(len(self.spec)):
                temp_spec.append(self.spec[i][j])
            peaks,_ = signal.find_peaks(temp_spec, height=opt_th)
            for i in range(len(self.spec)):
                if i in peaks:
                    peak_map[i][j] = self.spec[i][j]

        pitch_map = [[0 for y in range(88)] for x in range(len(self.spec))]
        for i in range(len(peak_map)):
            for j in range(len(peak_map[0])):
                converted = self.get_near_pitch_num(j)
                if pitch_map[i][converted] < peak_map[i][j]:
                    pitch_map[i][converted] = peak_map[i][j]

        for i in range(len(pitch_map)):
            for j in range(len(pitch_map[i])):
                if pitch_map[i][j]>0:
                    self.result.push_note(j, i, i+10, pitch_map[i][j])
                    #self.result.push_note(j,i,i+10, self.get_velocity())

        self.result.print_notes()

        '''
        TODO: 
        끝나는 부분 디텍트
        동시의 기준을 좀더 러프하게ㅇㅋ
        fft 했을때 수치 변동 어떻게 되나 실험해보기
        fft 했을때 잘 눌렀는데 수치가 작아진 이유는? -> 여러 대역대에 퍼져서?
            -> 아까 하던거 get_velocity 다시 해보자

        '''
        
                


    def detect_pitches_2dim(self):
        '''
        2-dim array에서 3*3 범위 안에서의 peaks를 찾아봅니다
        '''
        print("Start to Detect notes...")
        print("\t detecting local peaks...", end=" ")

        peak_map = [[0 for x in range(len(self.spec[0]))] for y in range(len(self.spec))]

        for i in range(1, len(self.spec)-1):
            for j in range(1, len(self.spec[i])-1):
                if (self.spec[i][j] > self.spec[i-1][j-1] and
                self.spec[i][j] > self.spec[i][j-1] and
                self.spec[i][j] > self.spec[i][j+1] and
                self.spec[i][j] > self.spec[i-1][j] and
                self.spec[i][j] > self.spec[i-1][j+1] and
                self.spec[i][j] > self.spec[i+1][j-1] and
                self.spec[i][j] > self.spec[i+1][j] and
                self.spec[i][j] > self.spec[i+1][j+1]):
                    peak_map[i][j] = self.spec[i][j]

        #del self.spec

        print("Done")
        print("\t remove too small notes...", end=" ")

        # 동일 시간에 등장한 가장 큰 음에 비해 너무 작은 음 제거
        opt_th = 10

        removed_count = 0

        '''
        for i in range(len(peak_map)):
            frame_max_peak = max(peak_map[i])
            for j in range(len(peak_map[0])):
                if peak_map[i][j] < opt_th:
                    peak_map[i][j] = 0
                if peak_map[i][j] < frame_max_peak/4:
                    peak_map[i][j] = 0
                    removed_count += 1
        '''
        same_frame = int(0.2/self.time_resolution)
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
                if peak_map[i][j] < mask_max_peak/4:
                    peak_map[i][j] = 0
                    removed_count += 1

        print("Done")
        print("\t\t removed", removed_count, "peaks")
        print("\t remove remained-echo...", end=" ")
        
        # 시간축으로 보아서 일렁이는 것 제거
        resolution_th = 5 # frames

        removed_count = 0
        for j in range(len(peak_map[0])):
            met = False
            i = 0
            while(i<len(peak_map)- resolution_th-1):
                if not met:
                    if peak_map[i][j] == 0:
                        i+= 1
                    else:
                        met = True
                        i+= 1
                else:
                    count = False
                    for k in range(resolution_th+1):
                        if peak_map[i+k][j] !=0:
                            count = True
                            peak_map[i+k][j] = 0
                            removed_count += 1
                            i+=k+1
                            break
                    if not count:
                        met = False
                        i+= k+1
        
        print("Done")
        print('\t\t removed', removed_count, 'peaks')

        #Show_Spectrogram(self.spec, vmin=0, vmax=30)
        #Show_Spectrogram(peak_map, vmin=0, vmax=1)

        # note detect
        for i in range(len(peak_map)):
            for j in range(len(peak_map[0])):
                if peak_map[i][j] !=0 :
                    pitch = self.get_near_pitch_num(j)
                    #self.result.push_note(pitch, i, i+10, peak_map[i][j])
                    self.result.push_note(pitch, i, i+10, 100)
                    #print(LUT(pitch), i, peak_map[i][j])
                    #self.result.push_note(pitch,i,i+10, self.get_velocity(pitch,i))
                

        


    
#test_sound = sound('test.mp3')
#test_sound2 = sound('test2.mp3')
test_sound3 = sound('https://www.youtube.com/watch?v=EeX8RWgq4Gs')
#test_sound3 = sound('bmajor.mp3')
pdp = pd_processor()
pdp.do(test_sound3)