from Sound_ds import sound
import numpy as np

import matplotlib.pyplot as plt
from dtw import dtw
from PitchDetection import pd_processor
from scipy import signal

def measure_accuracy(pdp, result_wav):
    print('Measure Accuracy...')
    source = spec_normalize(pdp.spec)

    result_source = sound(result_wav)
    pdp_r = pd_processor()
    pdp_r.sample_rate = result_source.sample_rate
    result = spec_normalize(pdp_r.get_spectrogram(result_source))

    onset_source = select_onsets(source)
    onset_result = select_onsets(result)

    print('\tonset_source : ',len(onset_source))
    print('\tonset_result : ',len(onset_result))

    num_pitch = np.shape(onset_result)[1]
    num_frame = np.shape(onset_result)[0]
    beat_score = 0
    pitch_score = 0
    final_score = 0
    best_index = 0
    for i in range(-7,8):
        if i<0:
            onset_result_tuned = onset_result[:,abs(i):]
            onset_result_tuned = np.hstack([onset_result_tuned, np.zeros((num_frame,abs(i)))])
        elif i>0:
            onset_result_tuned = np.zeros((num_frame, abs(i)))
            onset_result_tuned = np.hstack([onset_result_tuned, onset_result[:,:num_pitch-i]])
        else:
            onset_result_tuned = onset_result
        bs, ps, fs = calc_acc_cos(onset_source, onset_result_tuned)
        if fs > final_score:
            beat_score = bs
            pitch_score = ps
            final_score = fs
            beat_index = i
    print('accuracy : ',round(final_score*100,2),"%")
    return final_score

def spec_normalize(spec):
    return spec/np.max(spec)*100
def cos_distance(x, y):
    return 1/cos_similarity(x,y)
def cos_similarity(x,y):
    cos = np.sum(x*y) / (np.sqrt(np.sum(np.square(x))) + np.sqrt(np.sum(np.square(y))))
    return correlation_norm(cos)
def get_dtw_path(x, y, dist):
    d, cost_matrix, acc_cost_matrix, path= dtw(x,y, dist=dist)

    pairs = []
    for i in range(len(path[0])):
        pairs.append([int(path[0][i]),int(path[1][i])])

    xmax = int(max(path[0]))
    ymax = int(max(path[1]))

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
def correlation_norm(x):
    if x>0.5:
        return 1
    else:
        return 2*x
def calc_acc_cos(source, result):
    dist_c = lambda x, y: cos_distance(x,y)
    path_b = get_dtw_path(source, result, dist_c)
    if len(source)==len(result):
        beat_detection_score = 1
    else:
        beat_detection_score = np.sqrt(len(path_b) / (len(source)+len(result)-len(path_b)))
    
    pitch_scores = []
    for i in range(len(path_b)):
        source_t = source[path_b[i][0]]
        result_t = result[path_b[i][1]]
        cos_sim = cos_similarity(source_t, result_t)
        pitch_scores.append(cos_sim)
    pitch_detection_score = np.average(pitch_scores)
    final_score = beat_detection_score * pitch_detection_score
    return beat_detection_score, pitch_detection_score, final_score


def select_onsets(spec):
    onsets = []
    frame_sum = np.sum(spec, axis=1)
    frame_energy = np.sum((np.power(spec, 4)/100000000), axis=1)
    total_concaves, _ = signal.find_peaks(frame_energy, distance=15, height=max(frame_energy)/10)
    onsets = spec[total_concaves,:]
    return onsets

if __name__=='__main__':
    pdp = pd_processor()

    test_sound = sound('https://www.youtube.com/watch?v=Hf2MFBz4S_g') #라캄파넬라
    #test_sound = sound('https://www.youtube.com/watch?v=22jE6FdYjxE') #왕벌
    #test_sound = sound('https://www.youtube.com/watch?v=6vo66K06wFU') #아르카나
    #test_sound = sound('https://www.youtube.com/watch?v=w-4xH2DLv8M') # 작은별
    #test_sound = sound('https://www.youtube.com/watch?v=cqOY7LF_QrY') #관짝
    #test_sound = sound('https://www.youtube.com/watch?v=EiVmQZwJhsA') #금만
    #test_sound = sound('https://www.youtube.com/watch?v=NV43k7fq8jA') #흑건
    result = pdp.do(test_sound)
    result.make_wav('testwav')

    measure_accuracy(pdp, 'testwav.wav')