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
        #self.spec_max_th = 10                       # to detect valid frame from origin-spec
        self.spec_th = 1                            # to detect valid freq from origin-spec
        self.normalization_diff = 10

        # octave reduce
        self.octave_reduce_rate_r = 0.6             # same octave high pitch decrease-rate
        self.octave_reduce_rate_l = 0               # same octave low pitch decrease-rate
        self.misol_reduce_rate = 0.4                # +4 +7 pitch decrease-rate

        # pitch detect
        #self.max_th = 15                            # to remove too low band from peak_map
        self.len_th_sec = 0.2                       # to remove too short band from peak_map
        #self.spa_th_sec = 0.1                       # to attach too short-space bands
        #self.val_th = 10                             # to detect valid pitches
        self.pff_th = 10
        self.concave_th = 100 ##나중에 바꿔야댐

    def do(self, input_pcm):
        self.sample_rate = input_pcm.sample_rate
        self.spec = self.get_spectrogram(input_pcm)
        self.result = score(self.sample_rate, self.time_resolution)
        self.detect_pitches_jiho(self.spec)
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

        print("\t Generating Spectrogram Complete")
        print("\t sec per frame : ", self.time_resolution)

        #maxes = max(spec)
        #maxes = max(maxes)
        #Show_Spectrogram(spec, vmax=maxes)

        return spec

    def detect_pitches(self, spec):
        '''
        원본 spectrogram (88) 받아서 onset, offset, max 확인
        '''

        len_th = int(self.len_th_sec/self.time_resolution)
        #spa_th = int(self.spa_th_sec/self.time_resolution)

        concaves = [] # concaves[freq] = [frame1, frame2...]
        onoff = [] #onoff[freq] = [[start,end],[start,end]...]
        for j in range(len(spec[0])):
            freq_onoff = []
            freq_concaves = []
            freq_values = []
            for i in range(len(spec)):
                freq_values.append(spec[i][j])
            
            for i in range(1,len(freq_values)-1):
                if freq_values[i]>self.concave_th:
                    if freq_values[i]>freq_values[i-1] and freq_values[i]>freq_values[i+1]:
                        freq_concaves.append(i)

            ########### start,end들 가져오는 파트 ##########
            start = 0
            i = 0
            while i<len(freq_values):
                if freq_values[i] > self.concave_th: ###이것도 바까야함
                    start = i
                    while freq_values[i] > self.concave_th and i<len(freq_values):
                        i += 1
                    end = i
                    if end-start > len_th:
                        freq_onoff.append([start,end])
                else:
                    i += 1

            ###############################################

            concaves.append(freq_concaves)
            onoff.append(freq_onoff)

        all_concaves = [] # 모든 concave들 합집합
        for i in range(len(concaves)):
            for j in range(len(concaves[i])):
                if not concaves[i][j] in all_concaves:
                    all_concaves.append(concaves[i][j])

        pitches_per_frames = [[] for x in range(len(spec))]
        for frame_no in all_concaves:
            frame = spec[frame_no]
            pitches = self.get_pitch_from_frame(frame)
            pitches_per_frames[frame_no] = pitches
            #pitches_per_frames : 어떤 프레임에서 어떤 피치들이 나왔는가?
        
        ####print("pitches_per_frames : ", pitches_per_frames)

        # concaves[freq] = [frame1, frame2...]
        # pitches_per_frames[frame] = [pitch1, pitch2, ...]
        # onoff[freq] = [[start,end],[start,end]...]
        final_pitches = [[] for x in range(len(concaves))] #교집합(concaves, pitches_per_frames)
    
        # final_pitches[freq] = [frame1,..frame,,]
        for freq in range(len(concaves)):
            for j in range(len(concaves[freq])):
                frame_no = concaves[freq][j]
                if freq in pitches_per_frames[frame_no]:
                    final_pitches[freq].append(frame_no)

        ###################### start,end 범위 조사 ##################
        for freq in range(len(onoff)):
            mark = [0 for x in range(len(onoff[freq]))]
            for i in range(len(onoff[freq])):
                start = onoff[freq][i][0]
                end = onoff[freq][i][1]
                
                for k in range(len(final_pitches[freq])):
                    if final_pitches[freq][k] in range(start,end):
                        if mark[i]==0:
                            self.result.push_note(freq+9, start,start+20,100)
                            mark[i] = 1

    def detect_pitches_jiho(self, spec):
        '''
        원본 spectrogram (88) 받아서 onset, offset, max 확인
        '''

        len_th = int(self.len_th_sec/self.time_resolution)
        #spa_th = int(self.spa_th_sec/self.time_resolution)

        concaves = [] # concaves[freq] = [frame1, frame2...]

        for j in range(len(spec[0])):
            freq_concaves = []
            freq_values = []
            for i in range(len(spec)):
                freq_values.append(spec[i][j])
            
            for i in range(1,len(freq_values)-1):
                if freq_values[i]>self.concave_th:
                    if freq_values[i]>freq_values[i-1] and freq_values[i]>freq_values[i+1]:
                        freq_concaves.append(i)

            ########### start,end들 가져오는 파트 ##########
            
            del_list = []
            i = 1
            k = 1
            while i+k <len(freq_values):
                k = 1
                while i+k <len(freq_values):
                    if i+k in freq_concaves:
                        if freq_values[i+k] < freq_values[i] * 0.75:
                            del_list.append(i+k)
                            k+=1
                        else:
                            i+=k
                            break
                    elif freq_values[i+k] < 10:
                        i+=k
                        break
                    else:
                        k+=1
            
            deleted = list(set(freq_concaves)-set(del_list))
            deleted.sort()
            concaves.append(deleted)
            ###############################################

        all_concaves = [] # 모든 concave들 합집합
        for i in range(len(concaves)):
            for j in range(len(concaves[i])):
                if not concaves[i][j] in all_concaves:
                    all_concaves.append(concaves[i][j])

        pitches_per_frames = [[] for x in range(len(spec))]
        for frame_no in all_concaves:
            frame = spec[frame_no]
            pitches = self.get_pitch_from_frame(frame)
            pitches_per_frames[frame_no] = pitches
            #pitches_per_frames : 어떤 프레임에서 어떤 피치들이 나왔는가?
        
        ####print("pitches_per_frames : ", pitches_per_frames)

        # concaves[freq] = [frame1, frame2...]
        # pitches_per_frames[frame] = [pitch1, pitch2, ...]
 
        for freq in range(len(concaves)):
            for j in range(len(concaves[freq])):
                frame_no = concaves[freq][j]
                if freq in pitches_per_frames[frame_no]:
                    self.result.push_note(freq+9, frame_no, frame_no+20, 100)
            
        


    def get_pitch_from_frame(self, fft):
        '''
        spectrogram의 한 frame 받아서 배수감쇄 등 해서 pitch 뽑기
        ret : 유효한 피치no들의 리스트
        '''
        pitch_fft = [0 for x in range(len(fft))]
        #### Normalization ####
        max_fft = max(fft)
        for i in range(len(fft)):
            if fft[i] > self.normalization_diff:
                fft[i] -= self.normalization_diff
            else:
                fft[i] = 0
            fft[i] *= 127.0
            fft[i] /= max_fft

        #### Get Top N ####
        num_top = 10
        pairs = []
        for i in range(len(fft)):
            pairs.append([i,fft[i]])
        pairs = sorted(pairs, key=lambda x:x[1], reverse=True)
        pairs = pairs[0:num_top]
        tops = []
        for i in range(len(pairs)):
            tops.append(pairs[i][0])

        #### Concave 인지 확인 ####
        for i in range(1,len(fft)-1):
            if i in tops and fft[i-1]<fft[i] and fft[i+1]<fft[i]:
                pitch_fft[i] = fft[i]

        #### Octave 감쇄 ####
        pitch_fft = self.decrease_octave(pitch_fft)

        detected_pitches = []
        for i in range(len(pitch_fft)):
            if pitch_fft[i] > self.pff_th: ###########이것도
                detected_pitches.append(i)

        return detected_pitches
        
    def decrease_octave(self, pitch_fft):

        octaves = [[] for i in range(12)]

        for j in range(len(pitch_fft)):
            if pitch_fft[j] >0:
                octaves[j%12].append([j,pitch_fft[j]])
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
                    pitch_fft[octaves[j][k][0]] -= reduce_value*octave_reduce_rate
                    if pitch_fft[octaves[j][k][0]]<0:
                        pitch_fft[octaves[j][k][0]]=0

                ## +4음 감쇄
                mi = (j+4)%12
                for k in range(len(octaves[mi])):
                    if (octaves[j][0][0]-octaves[mi][k][0])>0 :
                        octave_reduce_rate = self.octave_reduce_rate_l
                    elif (octaves[j][0][0]-octaves[mi][k][0])<0:
                        octave_reduce_rate = self.octave_reduce_rate_r
                    else:
                        octave_reduce_rate = 1
                    pitch_fft[octaves[mi][k][0]] -= reduce_value*octave_reduce_rate*self.misol_reduce_rate
                    if pitch_fft[octaves[mi][k][0]]<0:
                        pitch_fft[octaves[mi][k][0]]=0
  
                ## +7음 감쇄
                sol = (j+7)%12
                for k in range(len(octaves[sol])):
                    if (octaves[j][0][0]-octaves[sol][k][0])>0 :
                        octave_reduce_rate = self.octave_reduce_rate_l
                    elif (octaves[j][0][0]-octaves[sol][k][0])<0:
                        octave_reduce_rate = self.octave_reduce_rate_r
                    else:
                        octave_reduce_rate = 1
                    pitch_fft[octaves[sol][k][0]] -= reduce_value*octave_reduce_rate*self.misol_reduce_rate
                    if pitch_fft[octaves[sol][k][0]]<0:
                        pitch_fft[octaves[sol][k][0]]=0

        return pitch_fft

        

        


if __name__=='__main__':
    #test_sound = sound('test.mp3')
    #test_sound2 = sound('test2.mp3')
    #test_sound3 = sound('https://www.youtube.com/watch?v=EeX8RWgq4Gs') #레헬른
    #test_sound3 = sound('bmajor.mp3')
    test_sound3 = sound('https://www.youtube.com/watch?v=6vo66K06wFU') #아르카나
    #test_sound3 = sound('https://www.youtube.com/watch?v=22jE6FdYjxE') #왕벌
    #test_sound3 = sound('https://www.youtube.com/watch?v=w-4xH2DLv8M') #작은별
    pdp = pd_processor()
    result = pdp.do(test_sound3)
    strin = result.str_pitches()
    result.make_midi()