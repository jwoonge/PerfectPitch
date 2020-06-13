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

class sound:
    def __init__(self, filename, username=" ", file=True):
        self.data = []
        self.valid = True
        self.title = ' '
        self.author = ' '
        self.time=' '
        self.username=username
        if '.mp3' in filename or '.wav' in filename:
            self.extract_from_file(filename)
        else:
            if not self.extract_from_link(filename):
                self.valid = False

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
            'outtmpl' : self.username+'.%(ext)s',
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
                info_dict = ydl.extract_info(link,download=False)
                ydl.prepare_filename(info_dict)
                ydl.download([link])

                self.title = info_dict['title']
                self.author = info_dict['uploader']
                self.time = info_dict['duration']
            except Exception as e:
                
                return False
            print("Download Complete")
        self.extract_from_file(self.username+'.mp3')
        os.remove(self.username+'.mp3') ###########
        return True