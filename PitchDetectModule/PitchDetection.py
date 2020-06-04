import os
import sys
sys.path.append(os.path.dirname(__file__))

from Sound_ds import sound
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
from Accord import score

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
        self.global_max = np.max(np.max(self.spec, axis=0),axis=0)
        self.result = score(self.time_resolution)
        self.detect_pitch()
        return self.result

    def detect_pitch_Muitos(self) :
        freq_peaks = []
        frame_peaks = []
        freq_convex = []
        valid_peaks = []
        start_ends = []
        for i in range(88) :
            convex, _ = signal.find_peaks(max(self.spec[:,i])-self.spec[:,i],prominence=1)
            peaks, _ = signal.find_peaks(self.spec[:,i],prominence= 450/(i+40))

            freq_peaks.append(peaks)
            freq_convex.append(convex)
        
        for i in range(88):
            valid_peak = []
            start_end = []
            for j in range(len(freq_peaks[i])):
                for k in range(len(freq_convex[i])-1):
                    if freq_peaks[i][j] in range(freq_convex[i][k], freq_convex[i][k+1]):
                        if freq_convex[i][k+1]-freq_convex[i][k] > 20:
                            valid_peak.append(freq_peaks[i][j])
                            start_end.append([freq_convex[i][k],freq_convex[i][k+1]])
            valid_peaks.append(valid_peak)
            start_ends.append(start_end)
        freq_peaks = valid_peaks

        '''
        for i in range(88) :
            if(max(self.spec[:,i]) > 50) :
                plt.plot(self.spec[:,i])
                plt.plot(freq_convex[i],self.spec[:,i][freq_convex[i]],'or')
                plt.plot(freq_peaks[i],self.spec[:,i][freq_peaks[i]],'xb')
                plt.title(str(i+1))
                plt.show()
        '''

        for i in range(len(self.spec)):
            peaks,_ = signal.find_peaks(self.spec[i,:])
            frame_peaks.append(peaks)
        '''
        union_peaks = []
        for i in range(88) :
            union_peaks = np.union1d(union_peaks,freq_peaks[i])'''



        
        coord_list = []
        for i in range(88):
            for j in range(len(frame_peaks)):

                if i in frame_peaks[j] and j in freq_peaks[i] :
                    coord_list.append([j,i])

        #print(coord_list)

        self.octave_decrease()
        count = 0
        for i in range(len(coord_list)) :
            if self.spec[coord_list[i][0]][coord_list[i][1]] > 1 :
                    count+=1
                    self.result.push_note(coord_list[i][1]+8,coord_list[i][0],coord_list[i][0]+40,100)
   

        print("note count = ",count)


    def detect_pitch(self):

        frame_energy = np.sum((self.spec**4)/100000000, axis=1)
        total_concaves, _ = signal.find_peaks(frame_energy, distance=5, height=0.15)

        plt.plot(frame_energy)
        plt.plot(total_concaves, frame_energy[total_concaves], 'ob')
        plt.show()

        valid_peaks = []
        start_ends = []
        for i in range(88):
            convex, _ = signal.find_peaks(max(self.spec[:,i])-self.spec[:,i], prominence=2)
            peaks, _ = signal.find_peaks(self.spec[:,i], prominence = 4) #450/(i+40)

            np.insert(convex,0,0)
            valid_peak = []
            start_end = []
            for j in range(len(peaks)):
                for k in range(len(convex)-1):
                    if peaks[j] in range(convex[k], convex[k+1]):
                        if convex[k+1]-convex[k] > 20:
                            valid_peak.append(peaks[j])
                            start_end.append([convex[k], convex[k+1]])
                            break
            valid_peaks.append(valid_peak)
            start_ends.append(start_end)
        
        pitch_map = np.zeros(np.shape(self.spec))

        for i in range(88):
            for j in range(len(start_ends[i])):
                for k in range(len(total_concaves)):
                    if total_concaves[k] in range(start_ends[i][j][0], start_ends[i][j][1]):
                        pitch_map[total_concaves[k]][i] = 1
                        break

        self.octave_decrease()
        count = 0
        for frame in range(len(self.spec)):
            for freq in range(1,87):
                if pitch_map[frame][freq] != 0 and self.spec[frame][freq]>1:
                    if self.spec[frame][freq-1] < self.spec[frame][freq] and self.spec[frame][freq+1]<self.spec[frame][freq]:
                        self.result.push_note(freq+8, frame, frame+40, 100)
                        count += 1
        print("num_note : ", count)


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
#test_sound = sound('https://www.youtube.com/watch?v=22jE6FdYjxE') #왕벌
test_sound = sound('https://www.youtube.com/watch?v=6vo66K06wFU') #아르카나
#test_sound = sound('https://www.youtube.com/watch?v=w-4xH2DLv8M') # 작은별
#test_sound = sound('https://www.youtube.com/watch?v=cqOY7LF_QrY') #관짝
result = pdp.do(test_sound)
result.make_csv('작은별진짜.csv')
result.make_midi()
result.make_midi_beat()
#result.make_score()



#파  파도    파도솔  파도솔레    파도솔레라        15
