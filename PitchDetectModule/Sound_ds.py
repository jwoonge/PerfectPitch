import os
system_path = os.environ["PATH"]
ffmpeg_path = ""
tmp = os.path.dirname(os.path.realpath(__file__)).split('\\')
for i in range(len(tmp)-1):
    ffmpeg_path += tmp[i]+'\\'
ffmpeg_path += 'ffmpeg\\bin'
if not 'ffmpeg' in system_path:
    os.environ["PATH"] = system_path+';'+ffmpeg_path
    
from os import rename
import array
from pydub import AudioSegment
import youtube_dl
import time
import numpy as np



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
    def __init__(self, filename, file=True):
        #start_time = time.time()
        self.data = []
        self.valid = True
        if '.mp3' in filename or '.wav' in filename:
            self.extract_from_file(filename)
        else:
            if not self.extract_from_link(filename):
                self.valid = False
        #print("time:", time.time()-start_time)

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

    def extract_from_file(self, filename):
        print("Extract PCM from file...", end=" ")
        sound_file = AudioSegment.from_file(filename)
        self.sample_rate = sound_file.frame_rate

        samples = sound_file.split_to_mono()
        del sound_file

        for i in range(len(samples)):
            self.data.append(samples[i].get_array_of_samples())
        self.downmixing()
        print("Done")

    def extract_from_link(self, link):
        FORMAT = "mp3"

        options = {
            'format':'bestaudio/best',
            'extractaudio':True,
            'audioformat':FORMAT,
            'outtmpl' : 'temp.%(ext)s',
            'noplaylist':True,
            'quiet':True,
            'nocheckcertificate':True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': FORMAT,
                'preferredquality': '192',
            }]
        }

        with youtube_dl.YoutubeDL(options) as ydl:
            try:
                print("Downloading...")
                ydl.download([link])
            except Exception as e:
                return False
            print("Download Complete")
        self.extract_from_file('temp.mp3')
        os.remove('temp.mp3') ###########
        return True