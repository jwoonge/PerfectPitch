import os
from os import rename
import array

def read_little_endian(num, wav_file):
    buf = wav_file.read(num)
    '''if not buf:
        return None'''
    ret = 0
    for i in range(0,num):
        ret+=buf[i]*(256**i)
    return ret

def convert_signed(value, bitnum):
    ret = value
    if value > 2**(bitnum*8-1):
        ret -= 2**(bitnum*8)
        return ret
    return ret

def split_wav(wav_pointer, num_channels, value_size, value_count):
    '''
    num_channels
    1 (mono): [data][data][data]...
    2 (stereo): [left][right]...
    3 (3ch) : [left][right][center]...
    4 (quad): [front left][front right][rear left][rear right]...
    5 (4ch) : [left][center][right][surround]...
    6 (6ch) : [left center][left][center][right center][right][surround]...
    '''
    split_data = []
    converted_num_channels = 1
    if num_channels==5:
        converted_num_channels = 4
    else:
        converted_num_channels = num_channels
    
    for i in range(converted_num_channels):
        split_data.append([])

    print('start converting...')

    for i in range(value_count * converted_num_channels):
        split_data[i%converted_num_channels].append(convert_signed(read_little_endian(value_size, wav_pointer), value_size))

    return split_data

def Write_wav(filename, input, sample_rate=16000, value_size=2, num_channels=1):
    bytes_per_sample = value_size
    bits_per_sample = bytes_per_sample * 8
    byte_rate = sample_rate * bytes_per_sample * num_channels
    value_count = len(input)

    with open(filename,'wb') as write_file:
        #write riff
        write_file.write(b'RIFF')
        write_file.write((36 + bytes_per_sample * num_channels * value_count).to_bytes(4,byteorder='little',signed=False))
        write_file.write(b'WAVE')

        #write fmt
        write_file.write(b'fmt ')
        fmtchunksize = 16
        fmtaudioformat = 1
        write_file.write(fmtchunksize.to_bytes(4,byteorder='little',signed = False))
        write_file.write(fmtaudioformat.to_bytes(2,byteorder='little',signed = False))
        write_file.write(num_channels.to_bytes(2,byteorder='little',signed = False))
        write_file.write(sample_rate.to_bytes(4,byteorder='little',signed = False))
        write_file.write(byte_rate.to_bytes(4,byteorder='little',signed = False))
        write_file.write(num_channels*bytes_per_sample.to_bytes(2,byteorder='little',signed = False))
        write_file.write(bits_per_sample.to_bytes(2,byteorder='little',signed = False))

        #write data
        write_file.write(b'data')
        write_file.write((bytes_per_sample * value_count * num_channels).to_bytes(4,byteorder='little',signed=False))

        for i in range(0,value_count*num_channels):
            if input[i]>32767:
                input[i] = 32767
            elif input[i]<-32768:
                input[i] = -32768
        for i in range(0, value_count*num_channels):
            write_file.write(input[i].to_bytes(bytes_per_sample,byteorder='little',signed=True))



class sound:
    def __init__(self, filename):
        self.data = []
        if '.mp3' in filename:
            self.extract_from_mp3(filename)
        elif '.wav' in filename:
            self.extract_from_wav(filename)
        else:
            self.extract_from_link(filename)

        #self.downmixing()

    def downmixing(self):
        downmixed = []
        for t in range(len(self.data[0])):
            temp = 0
            for ch in range(len(self.data)):
                temp += self.data[ch][t]
            temp /= len(self.data)
            downmixed.append(temp)
        self.data = downmixed
        del downmixed


    def extract_from_mp3(self, filename):
        print("TODO")

    def extract_from_wav(self, filename):
        wav_file = open(filename, 'rb+')
        RIFF = wav_file.read(12)
        fmt1 = wav_file.read(10)
        num_channels = read_little_endian(2, wav_file)
        print('num_channels : ', num_channels)
        self.sample_rate = read_little_endian(4, wav_file)
        fmt2 = wav_file.read(6)
        value_size = int(read_little_endian(2, wav_file) / 8)
        while(True):
            ChunkID = wav_file.read(4)
            if ChunkID == b'data' :
                break
            wav_file.seek(-3, 1)
        self.value_count = int(read_little_endian(4, wav_file) / (num_channels * value_size))

        self.data = split_wav(wav_file, num_channels, value_size, self.value_count)
        #self.split_pcm()

        wav_file.close()

    def split_pcm(self):
        for i in range(len(self.data)):
            Write_wav(str(i) + '.wav', self.data[i], self.sample_rate)

    def extract_from_link(self, link):
        print('TODO')
