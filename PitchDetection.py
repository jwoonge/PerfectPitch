from Sound_ds import sound
from Score_ds import score
import os
import math
import numpy as np
from scipy import signal
from scipy import fftpack

import matplotlib.pyplot as plt
import seaborn as sns


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
        self.result = score()

    def do(self, input_pcm):
        self.pcm = input_pcm
        self.get_spectrogram()
        self.detect_melody(20)
        self.result.print_notes()

    def get_near_pitch_num(self, freq):
        keys = np.array(list(self.dict.keys()))
        if freq <= max(keys) and freq >= min(keys):
            idx = np.abs(keys - freq)
            idx = idx.argmin()
        else:
            idx = -1
        return idx

    def get_spectrogram(self):
        freq_resolution = self.key_freq[1]-self.key_freq[0]
        n = int(self.pcm.sample_rate / freq_resolution)
        freq_resolution = self.pcm.sample_rate / n
        time_resolution = n / self.pcm.sample_rate
        #n/=10
        freq, t, Zxx = signal.stft(self.pcm.data, self.pcm.sample_rate, nperseg = n)
        # Zxx : [freq][time]
        self.spec = np.transpose(min_max_norm(np.abs(Zxx))*127)
        #print("spec:", np.shape(self.spec))
        #Show_Spectrogram(self.spec, vmax=127)
        

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
                self.result.push_note(peak, i, maxv)
                print("detected")

            last_peak = peak
            


    
#test_sound = sound('test.mp3')
#test_sound2 = sound('test2.mp3')
test_sound3 = sound('test3.mp3')
pdp = pd_processor()
pdp.do(test_sound3)