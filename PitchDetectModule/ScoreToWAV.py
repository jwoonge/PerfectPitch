from Accord import *
import numpy as np
import math
import wave, struct


def pitch_to_freq(pitch):
    return 440 * math.pow(2, (pitch - 48) * (1/12.0))
def note_to_wave(note, length, sample_rate):
    pitch = note.pitch
    wave = np.zeros(length)
    reduce_rate = 1
    while pitch_to_freq(pitch) < sample_rate/8:
        wave = wave + pitch_to_wave(pitch, length, sample_rate) * reduce_rate
        wave = wave + freq_to_wave(pitch + 4, length, sample_rate) * 0.5 * reduce_rate
        wave = wave + freq_to_wave(pitch + 7, length, sample_rate) * 0.5 * reduce_rate
        pitch += 12
        reduce_rate = 0.2
    return wave

def pitch_to_wave(pitch, length, sample_rate):
    freq = pitch_to_freq(pitch)
    return freq_to_wave(freq, length, sample_rate)

def freq_to_wave(freq, length, sample_rate):
    x = np.arange(0,length,1)
    y = np.sin(2*math.pi*freq*x/sample_rate)
    #x = x*8 / (interval*time_resolution * sample_rate)

    return y

def score_to_wav(score, filename, sample_rate):
    '''
    time = beat * score.interval * score.time_resolution
    1초에 sample rate 개, time초에는 time * sample_rate개
    즉 frame개수는 beat * score.interval * score.time_resolution * sample_rate
    '''
    print('Export Wav File...',end=" ")
    one_beat_samples = int(round(score.interval * score.time_resolution * sample_rate))
    values = np.zeros(3*sample_rate)
    for accord in score.accords:
        if accord.vice==0:
            accord_samples = int(accord.beat * one_beat_samples)
            accord_wave = np.zeros(accord_samples)

            velocity_range = np.arange(0,accord_samples,1)
            velocity_range = velocity_range * 8/one_beat_samples + 1
            velocity_templete = np.log(velocity_range)/np.square(velocity_range)

            for note in accord.notes:
                accord_wave = accord_wave + note_to_wave(note, accord_samples, sample_rate)
            accord_wave = accord_wave * accord.velocity * velocity_templete
            values = np.append(values, accord_wave)

    values = values * 20000/max(values)
    write_wav_file(filename, values, sample_rate)
    print('Done')


def write_wav_file(filename, values, sample_rate):
    obj = wave.open(filename+'.wav','w')
    obj.setnchannels(1)
    obj.setsampwidth(2)
    obj.setframerate(sample_rate)
    for value in values:
        obj.writeframesraw(struct.pack('<h', int(value)))

if __name__ == '__main__':    
    result = score(0)
    result.read_csv('result.csv')
    result.push_finished()
    score_to_wav(result, "resultwav", 44100)

