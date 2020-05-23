import os
import sys
sys.path.append(os.path.dirname(__file__))

from Sound_ds import sound
from Score_ds import score
import math
import numpy as np
from scipy import signal
from scipy import fftpack
from scipy.ndimage import filters

import time
import matplotlib.pyplot as plt
import seaborn as sns
from celluloid import Camera
import csv

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

def Show_Animation(input_spec,input_interval) :

    # set figure and axes
    f, ax = plt.subplots(figsize=(15,5))
    camera = Camera(f)
    xlabel = [i for i in range(88)]
    ax.xaxis.set_ticks(np.arange(0, 88, 1))
    for i in range(len(input_spec)) :
        ax.plot(xlabel,input_spec[i])
        camera.snap()
        f

    animation = camera.animate(interval= input_interval, repeat=True)
    animation.save('animation.mp4')

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
        dictionary[i] = get_near_pitch_num(round(i*tuning_rate))
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
        self.set_thresholds()


    def set_thresholds(self):
        self.spec_th = 1
        # octave reduce
        self.octave_reduce_rate_r = 0.3             # same octave high pitch decrease-rate
        self.octave_reduce_rate_l = 0.10               # same octave low pitch decrease-rate
        self.misol_reduce_rate = 0.5                # +4 +7 pitch decrease-rate

    def do(self, input_pcm):
        self.sample_rate = input_pcm.sample_rate
        self.spec = self.get_spectrogram(input_pcm)
        #Show_Spectrogram(self.spec)
        self.octave_decrease()
        self.global_max = np.max(np.max(self.spec, axis=0),axis=0)
        #plt.plot(self.spec[:,50])
        plt.show()
        #Show_Spectrogram(self.spec, vmax=self.global_max)
        self.result = score(self.sample_rate, self.time_resolution)
        self.detect_pitch()
        return self.result

    def detect_pitch(self):
        #top_idx = np.argpartition(self.spec, -10, axis = 1)[:,-10:]
        #deleted_low = np.where(vfvgbg, 0, self.spec)
        count = 0
        for freq in range(1,87):
            peaks, _ = signal.find_peaks(self.spec[:,freq], prominence = 4.3) ## 4~5사이 값이 적당한듯함
            for frame in peaks:
                if (self.spec[frame][freq] >= self.spec[frame][freq-1]
                    and self.spec[frame][freq] >= self.spec[frame][freq+1]):
                    self.result.push_note(freq+8, frame, frame+40, 100)
                    count += 1

        print("num_notes : ",count)

    def get_tuning_rate(self, spec):
        max_freq = np.argmax(spec[:,50:150])%(100)+50
        #max_freq = np.argmax(spec[:][100:])%(np.shape(spec)[1]-100)+100
        near_freq = self.key_freq[get_near_pitch_num(max_freq)]
        print("\t max_freq : ",max_freq)
        print("\t near_freq: ",near_freq)
        tuning_rate = near_freq/max_freq
        print("\t tuning_rate: ",tuning_rate)
        return tuning_rate

    def get_spectrogram(self, pcm):
        start_t = time.time()
        print("Calc Spectrogram...")
        freq_resolution = self.key_freq[1]-self.key_freq[0]
        n = int(pcm.sample_rate/freq_resolution/4)
        overlap_rate = 0.95
        time_resolution_rate = 1-overlap_rate
        self.time_resolution = n / self.sample_rate * time_resolution_rate
        freq, t, Zxx = signal.stft(pcm.data, self.sample_rate, nperseg = n, noverlap = int(n*overlap_rate))
        Zxx = np.transpose(np.abs(Zxx))
        Zxx = np.where(Zxx<self.spec_th, 0, Zxx)
        del freq
        del t

        tuning_rate = self.get_tuning_rate(Zxx)
        self.dict = get_freq_dict(np.shape(Zxx)[1], tuning_rate*4)
        end_t = time.time()
        print("\t Fourier Transform Complete", round(end_t-start_t,2),"sec")

        start_t = time.time()
        spec = np.zeros((np.shape(Zxx)[0],88))

        for freq in range(len(Zxx[0])):
            pitch = self.dict[freq]
            spec[:,pitch] = spec[:,pitch] + Zxx[:,freq]
        spec = np.sqrt(spec)
        end_t = time.time()
        print('\t Generating freq-to-pitch Complete', round(end_t-start_t,2),"sec")

        print("\t Generating Spectrogram Complete")
        print("\t sec per frame : ", self.time_resolution)
        return spec
        
    def octave_decrease(self):
        decrease_value = np.zeros(np.shape(self.spec))
        for pitch_origin in range(88):
            for pitch_to_dec in range(88):
                reduce_rate = 0
                octave_dif = pitch_to_dec - pitch_origin

                if not octave_dif == 0:
                    if octave_dif%12 == 0:
                        reduce_rate = 1
                    elif octave_dif%12 == 4 or octave_dif%12 == 7:
                        reduce_rate = self.misol_reduce_rate

                    if octave_dif < 0:
                        reduce_rate *= self.octave_reduce_rate_l
                    elif octave_dif > 0:
                        reduce_rate *= self.octave_reduce_rate_r

                decrease_value[:,pitch_to_dec] = decrease_value[:,pitch_to_dec] + self.spec[:,pitch_origin]*reduce_rate
        
        self.spec = self.spec - decrease_value
        self.spec = np.where(self.spec < 0, 0, self.spec)






pdp = pd_processor()
#test_sound = sound('https://www.youtube.com/watch?v=Hf2MFBz4S_g') #라캄파넬라
test_sound = sound('https://www.youtube.com/watch?v=22jE6FdYjxE') #왕벌
#test_sound = sound('https://www.youtube.com/watch?v=6vo66K06wFU') #아르카나
result = pdp.do(test_sound)
result.make_midi()




'''
test2 = np.argpartition(test, -5,axis=0)
print(test2)

test3 = np.argpartition(test, -5,axis =1)
print(test3)
print(test3[:,-2:])

'''