from Sound_ds import sound
from Score_ds import score
import os
import math
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import seaborn as sns
from dtw import dtw
from PitchDetection import pd_processor
from PitchDetection import Show_Spectrogram

'''
1. get spectrogram
2. divide and compact
3. get lump vertors
3. DTW 
4. get average of lump vertor cos

'''


def list_distance(list1,list2):
    dist = 0
    for i in range(len(list1)):
        dist += (list1[i] - list2[i])**2
    return dist

def get_dtw_path(x, y, cos=True):
    if cos:
        distance = lambda x,y:get_vector_cosin(x,y)
    else:
        dist = lambda x,y:list_distance(x,y)
    
    d, cost_matrix, acc_cost_matrix, path= dtw(x,y, dist=distance)

    pairs = []
    for i in range(len(path[0])):
        pairs.append([int(path[0][i]),int(path[1][i])])

    xmax = int(max(path[0]))
    ymax = int(max(path[1]))
    print('xmax : ', xmax)
    xcount = [[] for i in range(xmax+1)]
    ycount = [[] for i in range(ymax+1)]

    removed = []
    for i in range(len(pairs)):
        xcount[pairs[i][0]].append(i)  # 
    for i in range(len(xcount)):
        if len(xcount[i])==1:
            removed.append(pairs[xcount[i][0]])
        elif len(xcount[i])>1:
            best = xcount[i][0]
            value = cost_matrix[pairs[xcount[i][0]][0]][pairs[xcount[i][0]][1]]
            for j in range(1,len(xcount[i])):
                cost = cost_matrix[pairs[xcount[i][j]][0]][pairs[xcount[i][j]][1]]
                if value>cost:
                    best = xcount[i][j]
                    value = cost
            removed.append(pairs[best])

    pairs = removed
    removed = []
    for i in range(len(pairs)):
        ycount[pairs[i][1]].append(i)  # 
    for i in range(len(ycount)):
        if len(ycount[i])==1:
            removed.append(pairs[ycount[i][0]])
        elif len(ycount[i])>1:
            best = ycount[i][0]
            value = cost_matrix[pairs[ycount[i][0]][0]][pairs[ycount[i][0]][1]]
            for j in range(1,len(ycount[i])):
                cost = cost_matrix[pairs[ycount[i][j]][0]][pairs[ycount[i][j]][1]]
                if value>cost:
                    best = ycount[i][j]
                    value = cost
            removed.append(pairs[best])
    
    return removed
def get_key_freq(key_count=88):
    center_a = 48
    key_freq = {i:0 for i in range(key_count)}
    diff = [i-center_a for i in range(key_count)]

    for i in range(len(key_freq)):
        key_freq[i] = 440 * math.pow(2, diff[i] * (1/12.0))
    output_dict = {v:k for k,v in key_freq.items()}

    return output_dict

def get_spectrogram(sound):
    '''
    key = list(get_key_freq())
    overlap_rate = 0.95
    freq_resolution = key[1]-key[0]
    n = int(sound.sample_rate / freq_resolution)
    freq, t, Zxx = signal.stft(sound.data, sound.sample_rate, nperseg = n, noverlap= int(n*overlap_rate))
    Zxx = np.transpose(min_max_norm(np.abs(Zxx))*127)
    return Zxx
    '''

    pdp = pd_processor()
    spec = pdp.get_spectrogram(sound)
    Show_Spectrogram(spec)
    return spec




def get_lump_vector(compacted, num_lump = 10):
    ret = []
    for i in range(len(compacted)):
        lump = []
        for freq in range(1, len(compacted[i])-1):
            if compacted[i][freq] > compacted[i][freq-1] and compacted[i][freq] > compacted[i][freq+1]:
                lump.append([freq, compacted[i][freq]])
        lump = sorted(lump, key=lambda x:x[1], reverse=True)

        if len(lump) > num_lump:
            lump = lump[0:num_lump]
        
        lump = sorted(lump, key=lambda x:x[0])

        vector = []
        for j in range(num_lump - len(lump)):
            vector.append(j)
        for j in range(len(lump)):
            vector.append(lump[j][0])

        scaled = []
        div = vector[1]-vector[0]
        for i in range(len(vector)-1):
            scaled.append((vector[i+1]-vector[i])/div)
        ret.append(scaled)

    return ret

def get_lump_vector2(compacted, num_lump = 10):
    ret = []
    for i in range(len(compacted)):
        lump = []
        for freq in range(1, len(compacted[i])-1):
            if compacted[i][freq] > compacted[i][freq-1] and compacted[i][freq] > compacted[i][freq+1]:
                lump.append([freq, compacted[i][freq]])
        lump = sorted(lump, key=lambda x:x[1], reverse=True)

        if len(lump) > num_lump:
            lump = lump[0:num_lump]
        
        lump = sorted(lump, key=lambda x:x[0])

        vector = []
        for j in range(num_lump - len(lump)):
            vector.append(j)
        for j in range(len(lump)):
            vector.append(lump[j][0])

        scaled = []
        div = vector[1]-vector[0]
        for i in range(len(vector)-1):
            scaled.append(vector[i+1]-vector[i])
        sum_scaled = 0
        for i in range(len(scaled)):
            sum_scaled += (scaled[i])**2
        for i in range(len(scaled)):
            scaled[i] = scaled[i] / (sum_scaled)**(1/2)
        ret.append(scaled)

    return ret

def min_max_norm(x,axis=None):
    min = x.min(axis=axis,keepdims=True)
    max = x.max(axis=axis,keepdims=True)
    result = (x-min)/(max-min)
    return result

def divide_spec(Spec, thres2 = 2):
    bright = []
    block = []
    boundary = []
    delete = []

    for i in range(0, len(Spec)):
        count = 0
        for j in range(0, len(Spec[0])):
            if (Spec[i][j] > thres2):
                count += 1
        bright.append(count)
    
    #plt.plot(bright)

    for i in range(1, len(bright) - 1):
        if (bright[i] >= bright[i-1] and bright[i] >= bright[i+1] and bright[i] > max(bright) / 2):
            if (bright[i-1] >= bright[i-2] and bright[i+1] >= bright[i+2]):
                boundary.append(i)

    for i in range(0, len(boundary) - 1):
        if(boundary[i+1] - boundary[i] < 2):
            delete.append(boundary[i+1])

    boundary = list(set(boundary) - set(delete))
    boundary.sort()

    print("boundary : ", boundary)

    for i in range(0, len(boundary)):
        plt.plot(Spec[boundary[i]])
        plt.show()

    for i in range(0, len(boundary)):
        temp = []
        for j in range(-1, 2):
            temp.append(Spec[boundary[i] + j])           
        block.append(temp)

    return block

def compact_blocks(blocks):
    ret = []
    for i in range(len(blocks)):
        compacted = [0 for x in range(len(blocks[i][0]))]
        for j in range(len(blocks[i])):
            for k in range(len(blocks[i][j])):
                compacted[k] += blocks[i][j][k]
        ret.append(compacted)
    return ret

def get_vector_cosin(vector1, vector2):
    sumA = 0
    sumB = 0
    w = 0
    for i in range(0, len(vector1)):
        sumA += vector1[i]**2
        sumB += vector2[i]**2
        w += vector1[i]*vector2[i]
    disA = sumA**(1/2)
    disB = sumB**(1/2)

    #####  #####
    
    return w / (disA * disB)



def sound_similarity(sound1, sound2):
    vectors1 = get_lump_vector2(compact_blocks(divide_spec(get_spectrogram(sound1))))
    vectors2 = get_lump_vector2(compact_blocks(divide_spec(get_spectrogram(sound2))))

    path = get_dtw_path(vectors1,vectors2)

    dtw_accuracy = len(path)/(len(vectors1) + len(vectors2) - len(path))

    cos_s = []
    for i in range(len(path)):
        cos_s.append(get_vector_cosin(vectors1[path[i][0]], vectors2[path[i][1]]))

    print("dtw_acc:",dtw_accuracy)
    print("cos_s:",cos_s)

    score = sum(cos_s)/len(cos_s) * 100
    print("score:",score)
    print("Accuracy:",score*dtw_accuracy)

#sound1 = sound("https://www.youtube.com/watch?v=n0o1kgBRjh8")
#sound2 = sound("https://www.youtube.com/watch?v=ZeVUOs_o1VE")

#sound1 = sound("https://www.youtube.com/watch?v=a9hSy7soo-Y")
#sound2 = sound("https://www.youtube.com/watch?v=tKg3UtD1YdI")

#sound1 = sound("cminor.mp3")
#sound2 = sound("eminor.mp3")

sound1 = sound("sol.mp3")
sound2 = sound("back2.mp3")

sound_similarity(sound1, sound2)