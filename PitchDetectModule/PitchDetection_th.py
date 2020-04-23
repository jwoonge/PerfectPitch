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
        self.set_thresholds()

    def set_thresholds(self):
        # spectrogram
        self.spec_max_th = 10                       # to detect valid frame from origin-spec
        self.spec_th = 1                            # to detect valid freq from origin-spec
        self.normalization_diff = 10

        # octave reduce
        self.octave_reduce_rate_r = 0.6             # same octave high pitch decrease-rate
        self.octave_reduce_rate_l = 0               # same octave low pitch decrease-rate
        self.misol_reduce_rate = 0.4                # +4 +7 pitch decrease-rate

        # pitch detect
        self.max_th = 15                            # to remove too low band from peak_map
        self.len_th_sec = 0.2                       # to remove too short band from peak_map
        self.spa_th_sec = 0.1                       # to attach too short-space bands
        self.val_th = 10                             # to detect valid pitches

    def do(self, input_pcm):
        self.sample_rate = input_pcm.sample_rate
        self.spec = self.get_spectrogram(input_pcm)
        self.result = score(self.sample_rate, self.time_resolution)
        self.detect_pitches()
        return self.result


    def get_tuning_rate(self, spec):
        maxes = []
        for i in range(len(spec)):
            maxv = max(spec[i])
            listspec = list(spec[i])
            maxes.append([maxv, listspec.index(maxv)])
        maxes = sorted(maxes, key=lambda x:x[0], reverse=True)
        max_freq = maxes[0][1]
        near_freq = self.key_freq[get_near_pitch_num(max_freq)]

        return near_freq / max_freq

    def detect_pitches(self):
        peak_map = self.get_peak_map()
        self.octave_reduce(peak_map)
        self.peak_to_pitches(peak_map)

    def get_spectrogram(self, pcm):
        start_t = time.time()
        print("Calc Spectrogram...")
        freq_resolution = self.key_freq[1]-self.key_freq[0]
        n = int(pcm.sample_rate / freq_resolution)
        freq_resolution = pcm.sample_rate / n
        overlap_rate = 0.95
        time_resolution_rate = 1-overlap_rate
        self.time_resolution = n / pcm.sample_rate * time_resolution_rate
        freq, t, Zxx = signal.stft(pcm.data, pcm.sample_rate, nperseg = n, noverlap = int(n*overlap_rate))
        # Zxx : [freq][time]
        Zxx = np.transpose(np.abs(Zxx))

        tuning_rate = self.get_tuning_rate(Zxx)
        print("\t Tuning rate : ",tuning_rate)

        self.dict = get_freq_dict(len(Zxx[0]), tuning_rate)
        end_t = time.time()
        print("\t Fourier Transform Complete", round(end_t-start_t,2),"sec")

        start_t = time.time()

        spec = [[0 for y in range(88)] for x in range(len(Zxx))]
        for i in range(len(Zxx)):
            for j in range(len(Zxx[0])):
                pitch = self.dict[j]
                if Zxx[i][j] > self.spec_th:
                    spec[i][pitch] += Zxx[i][j]
        del Zxx
        end_t = time.time()
        print('\t Generating freq-to-pitch Complete', round(end_t-start_t,2),"sec")
        
        spec = self.spec_normalization(spec)

        print("\t Generating Spectrogram Complete")
        print("\t sec per frame : ", self.time_resolution)
        return spec
        
    def spec_normalization(self, spec):
        frame_valid = []
        spec_local_maxes = []
        
        for i in range(len(spec)):
            tmp_max = max(spec[i])
            spec_local_maxes.append(tmp_max)
            if tmp_max>self.spec_max_th:
                frame_valid.append(True)
            else:
                frame_valid.append(False)
        
        max_spec = max(spec_local_maxes)

        for i in range(len(spec)):
            for j in range(len(spec[i])):
                if frame_valid[i]:
                    spec[i][j] -= self.normalization_diff
                    if spec[i][j]<0:
                        spec[i][j]=0
                    #spec[i][j] *= (127 / spec_local_maxes[i])
                    spec[i][j] *= (127 / max_spec)
                    spec[i][j] = int(spec[i][j])
                else:
                    spec[i][j] = 0

        return spec
         
    def get_peak_map(self):
        print("Detecting pitches...")
        num_top = 10
        peaks = []
        for i in range(len(self.spec)):
            pairs = []
            for j in range(len(self.spec[i])):
                pairs.append([j,self.spec[i][j]])
            pairs = sorted(pairs, key=lambda x:x[1], reverse=True)
            pairs = pairs[0:num_top]
            pairs = sorted(pairs, key=lambda x:x[0])
            peaks.append(pairs)

        ## concave인지 확인 ##
        peak_map = [[0 for y in range(88)] for x in range(len(self.spec))]
        for i in range(len(peaks)):
            for j in range(len(peaks[i])):
                peak_map[i][peaks[i][j][0]] = peaks[i][j][1]
        del peaks
        for i in range(len(peak_map)):
            for j in range(1,len(peak_map[i])-1):
                if peak_map[i][j]<peak_map[i][j-1] or peak_map[i][j]<peak_map[i][j+1]:
                    peak_map[i][j] = 0
        return peak_map

    def octave_reduce(self, peak_map):
        ## 옥타브 감쇄 ##
        reduce_octave_count = 0
        reduce_misol_count = 0
        for i in range(len(peak_map)):
            octaves = [[] for k in range(12)]
            for j in range(len(peak_map[i])):
                if peak_map[i][j] >0:
                    octaves[j%12].append([j,peak_map[i][j]])
            # octaves[gye_num] = [[pitch,value],[pitch,value]]..
            for j in range(len(octaves)):
                ## 동일 계 감쇄
                if len(octaves[j])>1:
                    octaves[j] = sorted(octaves[j], key=lambda x:x[1], reverse=True)
                    reduce_value = octaves[j][0][1]
                    for k in range(1,len(octaves[j])):
                        if (octaves[j][0][0]-octaves[j][k][0])>0 :
                            octave_reduce_rate = self.octave_reduce_rate_l
                        else:
                            octave_reduce_rate = self.octave_reduce_rate_r
                        peak_map[i][octaves[j][k][0]] -= reduce_value*octave_reduce_rate
                        if peak_map[i][octaves[j][k][0]]<0:
                            peak_map[i][octaves[j][k][0]]=0
                            reduce_octave_count += 1
                    ## +4음 감쇄
                    mi = (j+4)%12
                    for k in range(len(octaves[mi])):
                        if (octaves[j][0][0]-octaves[mi][k][0])>0 :
                            octave_reduce_rate = self.octave_reduce_rate_l
                        elif (octaves[j][0][0]-octaves[mi][k][0])<0:
                            octave_reduce_rate = self.octave_reduce_rate_r
                        else:
                            octave_reduce_rate = 1
                        peak_map[i][octaves[mi][k][0]] -= reduce_value*octave_reduce_rate*self.misol_reduce_rate
                        if peak_map[i][octaves[mi][k][0]]<0:
                            peak_map[i][octaves[mi][k][0]]=0
                            reduce_misol_count += 1
                    ## +7음 감쇄
                    sol = (j+7)%12
                    for k in range(len(octaves[sol])):
                        if (octaves[j][0][0]-octaves[sol][k][0])>0 :
                            octave_reduce_rate = self.octave_reduce_rate_l
                        elif (octaves[j][0][0]-octaves[sol][k][0])<0:
                            octave_reduce_rate = self.octave_reduce_rate_r
                        else:
                            octave_reduce_rate = 1
                        peak_map[i][octaves[sol][k][0]] -= reduce_value*octave_reduce_rate*self.misol_reduce_rate
                        if peak_map[i][octaves[sol][k][0]]<0:
                            peak_map[i][octaves[sol][k][0]]=0
                            reduce_misol_count += 1

        print("\t Removed by octave reducing : ",reduce_octave_count+reduce_misol_count,"pitches")
        print("\t\tRemoved same octaves : ",reduce_octave_count)
        print("\t\tRemoved misols : ", reduce_misol_count)

    def peak_to_pitches(self, peak_map):
        len_th = int(self.len_th_sec/self.time_resolution)
        spa_th = int(self.spa_th_sec/self.time_resolution)
        del_count = 0
        
        for j in range(88):
            start = 0
            i=0
            pitch_stack = []
            while i<len(peak_map):
                if peak_map[i][j] >self.val_th:
                    start = i
                    peak_max = peak_map[start][j]
                    peak_max_i = start
                    while peak_map[i][j] >self.val_th and i<len(peak_map):
                        if peak_map[i][j] > peak_max:
                            peak_max = peak_map[i][j]
                            peak_max_i = i
                        i+=1
                    end = i
                    if end-start > len_th and peak_max > self.max_th:
                        peak_range = []
                        for k in range(start,end):
                            peak_range.append(peak_map[k][j])
                        peak_range = filters.gaussian_filter1d(peak_range,3)

                        c = 0
                        for k in range(1,len(peak_range)-1):
                            if peak_range[k]>peak_range[k-1] and peak_range[k]>peak_range[k+1]:
                                pitch_stack.append([j+9,start+k,start+k+10,100,start+k])
                                c += 1
                        if c==0:
                            pitch_stack.append([j+9,start,end,100,peak_max_i])

                    else:
                        del_count += 1
                else:
                    i+=1
            i=0

            while(True):
                if i>len(pitch_stack)-1:
                    break
                pitch = pitch_stack[i][0]
                start = pitch_stack[i][1]
                end = pitch_stack[i][2]
                value=pitch_stack[i][3]
                maxi= pitch_stack[i][4]

                if i==len(pitch_stack)-1:
                    #self.result.push_note(pitch,start,end,value)
                    self.result.push_note(pitch,maxi,end,value)
                    break
                
                else:
                    if pitch_stack[i+1][1]-pitch_stack[i][2]>=spa_th:
                        #self.result.push_note(pitch,start,end,value)
                        self.result.push_note(pitch,maxi,end,value)
                        i+=1
                    else:
                        #self.result.push_note(pitch,start,pitch_stack[i+1][2],value)
                        self.result.push_note(pitch,maxi,pitch_stack[i+1][2],value)
                        i+=2
        
        print(del_count)
        self.result.make_midi()
        Show_Animation(peak_map,self.time_resolution*1000)
        


if __name__=='__main__':
    #test_sound = sound('test.mp3')
    #test_sound2 = sound('test2.mp3')
    #test_sound3 = sound('https://www.youtube.com/watch?v=EeX8RWgq4Gs') #레헬른
    #test_sound3 = sound('bmajor.mp3')
    #test_sound3 = sound('https://www.youtube.com/watch?v=6vo66K06wFU') #아르카나
    #test_sound3 = sound('https://www.youtube.com/watch?v=22jE6FdYjxE') #왕벌
    test_sound3 = sound('https://www.youtube.com/watch?v=w-4xH2DLv8M') #작은별
    pdp = pd_processor()
    result = pdp.do(test_sound3)
    strin = result.str_pitches()
    #result.make_midi()