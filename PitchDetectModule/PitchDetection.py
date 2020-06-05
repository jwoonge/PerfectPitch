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
import csv
from Accord import score

def get_interval(input_list, vmin=8, vmax=70):
    diffs = []
    for i in range(len(input_list)-1):
        diffs.append(input_list[i+1]-input_list[i])

    distances = []
    ranges = [0.01*x for x in range(vmin*100,vmax*100)]
    for interval in ranges:
        distance = 0
        for diff in diffs:
            left = abs(diff / interval - round(diff / interval))
            distance += left / np.sqrt(interval)
        distances.append(distance)
    interval = np.argmin(distances)/100 + 8
    return interval

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
        self.one_pitch_reduce_rate = 0.4
        self.two_pitch_reduce_rate = 0.25
        self.octave_reduce_rate_r = 0.15             # same octave high pitch decrease-rate
        self.octave_reduce_rate_l = 0.05               # same octave low pitch decrease-rate
        self.misol_reduce_rate = 0.5                # +4 +7 pitch decrease-rate

    def do(self, input_pcm):
        self.sample_rate = input_pcm.sample_rate
        self.spec = self.get_spectrogram(input_pcm)
        self.global_max = np.max(np.max(self.spec, axis=0),axis=0)
        self.result = score(self.time_resolution)
        self.detect_pitch()
        return self.result


    def detect_pitch(self):
        frame_energy = np.sum((np.power(self.spec, 4)/100000000), axis=1)
        total_concaves, _ = signal.find_peaks(frame_energy, distance=15, height=max(frame_energy)/10)
        interval = get_interval(total_concaves) / 4
        #########이부분 나누기를 어떻게 해줄지 고민하자
        #########그리고 마디별로 나눠서 템포 찾아보자
        self.result.interval = interval
        print(interval)
        metronome = [total_concaves[0]]
        for i in range(1,len(total_concaves)):
            dif = total_concaves[i]-total_concaves[i-1]
            beat = round(dif / interval)
            if beat > 1:
                for j in range(int(round(dif/interval))-1):
                    metronome.append(metronome[-1] + dif / beat)
            metronome.append(total_concaves[i])
        
        valid_peaks = []
        start_ends = []

        for i in range(88):
            convex, _ = signal.find_peaks(max(self.spec[:,i])-self.spec[:,i], prominence=3)
            peaks, _ = signal.find_peaks(self.spec[:,i], prominence = 4) #450/(i+40)
            convex = np.insert(convex, 0, 0)
            convex = np.insert(convex, len(convex), len(self.spec[:,i])-1)
            j=0;k=0
            valid_peak = []
            start_end = []
            while True:
                if j >= len(convex)-1 or k >= len(peaks):
                    break
                if convex[j] <= peaks[k] and convex[j+1] > peaks[k]:
                    valid_peak.append(peaks[k])
                    start_end.append([convex[j], convex[j+1]])
                    j += 1; k += 1
                elif convex[j+1] <= peaks[k]:
                    j += 1
                else:
                    k += 1
            valid_peaks.append(valid_peak)
            start_ends.append(start_end)

        pitch_map = np.zeros(np.shape(self.spec))
        for i in range(88):
            j=0;k=0
            while True:
                if j>=len(start_ends[i]) or k>=len(metronome):
                    break
                start = start_ends[i][j][0]
                end = start_ends[i][j][1]
                peak = metronome[k]
                if start <= peak and end >= peak:
                    pitch_map[int(round(peak))][i]=1
                    k += 1 ; j += 1
                elif peak < start:
                    k += 1
                else:
                    j += 1

        self.octave_decrease()
        count = 0
        for frame in range(len(self.spec)):
            for freq in range(1,87):
                if pitch_map[frame][freq] != 0 and self.spec[frame][freq]>0:
                    #if self.spec[frame][freq-1] < self.spec[frame][freq] and self.spec[frame][freq+1]<self.spec[frame][freq]:
                        #self.result.push_note(freq+8, frame, frame+40, self.spec[frame][freq])
                    self.result.push_note(freq+8, frame, frame+40, 100)
                    count += 1
        print("num_note : ", count)





    def detect_pitch5(self):
        
        distances=[]
        for i in range(len(self.spec)-1) :
            distances.append(np.sum(np.power(self.spec[i]-self.spec[i+1], 4)))
        distances = np.array(distances)
        distances = filters.gaussian_filter1d(distances, 2)
        total_concaves, _ = signal.find_peaks(distances, distance=8, height=0.0001, prominence=3)

        plt.plot(distances)
        plt.plot(total_concaves, distances[total_concaves], 'ob')

        #plt.plot(total_concaves,height_val,color='r')
        plt.show()


        valid_peaks = []
        start_ends = []

        for i in range(88):
            convex, _ = signal.find_peaks(max(self.spec[:,i])-self.spec[:,i], prominence=2)
            peaks, _ = signal.find_peaks(self.spec[:,i], prominence = 4) #450/(i+40)
            convex = np.insert(convex, 0, 0)
            convex = np.insert(convex, len(convex), len(self.spec[:,i])-1)
            j=0;k=0
            valid_peak = []
            start_end = []
            while True:
                if j >= len(convex)-1 or k >= len(peaks):
                    break
                if convex[j] <= peaks[k] and convex[j+1] > peaks[k]:
                    valid_peak.append(peaks[k])
                    start_end.append([convex[j], convex[j+1]])
                    j += 1; k += 1
                elif convex[j+1] <= peaks[k]:
                    j += 1
                else:
                    k += 1
            valid_peaks.append(valid_peak)
            start_ends.append(start_end)

        
        pitch_map = np.zeros(np.shape(self.spec))
        for i in range(88):
            j=0;k=0
            while True:
                if j>=len(start_ends[i]) or k>=len(total_concaves):
                    break
                start = start_ends[i][j][0]
                end = start_ends[i][j][1]
                peak = total_concaves[k]
                if start <= peak and end >= peak:
                    pitch_map[peak][i]=1
                    k += 1 ; j += 1
                elif peak < start:
                    k += 1
                else:
                    j += 1

        self.octave_decrease()
        count = 0
        for frame in range(len(self.spec)):
            for freq in range(1,87):
                if pitch_map[frame][freq] != 0 and self.spec[frame][freq]>0:
                    #if self.spec[frame][freq-1] < self.spec[frame][freq] and self.spec[frame][freq+1]<self.spec[frame][freq]:
                        #self.result.push_note(freq+8, frame, frame+40, self.spec[frame][freq])
                    self.result.push_note(freq+8, frame, frame+40, 100)
                    count += 1
        print("num_note : ", count)

    def detect_pitch_for_octave_test(self):
        pitch_map = np.zeros(np.shape(self.spec))
        for i in range(88):
            peaks, _ = signal.find_peaks(self.spec[:,i], prominence = 4) #450/(i+40)
            for j in range(len(peaks)):
                pitch_map[peaks[j]][i] = 1

        self.octave_decrease()
        count = 0
        for frame in range(len(self.spec)):
            for freq in range(1,87):
                if pitch_map[frame][freq] != 0 and self.spec[frame][freq]>0:
                    #if self.spec[frame][freq-1] < self.spec[frame][freq] and self.spec[frame][freq+1]<self.spec[frame][freq]:
                        #self.result.push_note(freq+8, frame, frame+40, self.spec[frame][freq])
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
                
                if abs(pitch_to_dec-pitch_origin) == 2:
                    reduce_rate = self.two_pitch_reduce_rate
                elif abs(pitch_to_dec - pitch_origin)==1:
                    reduce_rate = self.one_pitch_reduce_rate

                decrease_value[:,pitch_to_dec] = decrease_value[:,pitch_to_dec] + self.spec[:,pitch_origin]*reduce_rate
        
        self.spec = self.spec - decrease_value
        self.spec = np.where(self.spec < 0, 0, self.spec)


if __name__=='__main__':
    
    pdp = pd_processor()
    test_sound = sound('https://www.youtube.com/watch?v=Hf2MFBz4S_g') #라캄파넬라
    #test_sound = sound('https://www.youtube.com/watch?v=22jE6FdYjxE') #왕벌
    #test_sound = sound('https://www.youtube.com/watch?v=6vo66K06wFU') #아르카나
    #test_sound = sound('https://www.youtube.com/watch?v=w-4xH2DLv8M') # 작은별
    #test_sound = sound('https://www.youtube.com/watch?v=cqOY7LF_QrY') #관짝
    result = pdp.do(test_sound)
    result.make_csv('작은별진짜.csv')
    result.make_midi('abc')
    result.make_midi_beat('def')
    result.make_score()
    
