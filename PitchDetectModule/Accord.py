import pretty_midi
import csv
from collections import Counter
from dtw import dtw
import numpy as np
from matplotlib import pyplot as plt
from LilyNotation import *
import os
import sys
import subprocess

class note:
    def __init__(self, pitch, start, velocity):
        self.pitch = pitch
        self.time = start
        self.velocity = velocity

class accord:
    def __init__(self):
        self.vice = False
        self.notes = []
        self.beat = 0
        self.origin_frames = -1
        self.velocity = 0
        self.time = 0
        self.beat_ac = 0

    def push_to_accord(self, note):
        self.notes.append(note)

    def calc_avg_velocity(self):
        for note in self.notes:
            self.velocity += note.velocity
        self.velocity /= len(self.notes)

    def calc_avg_start(self):
        self.time = 0
        for note in self.notes:
            self.time += note.time
        self.time /= len(self.notes)
    
    def calc_first_start(self):
        self.time = self.notes[0].time
        for note in self.notes:
            if note.time < self.time:
                self.time = note.time
            

class score:
    def __init__(self, time_resolution):
        self.accords_left = []
        self.accords_right = []
        self.accords = []
        self.accord_th = 5
        self.time_resolution = time_resolution

    def push_note(self, pitch_num, s, e, velocity):
        tnote = note(pitch_num, s, velocity)
        if len(self.accords)==0:
            tmp_accord = accord()
            tmp_accord.push_to_accord(tnote)
            self.accords.append(tmp_accord)

        elif abs(tnote.time - self.accords[-1].notes[-1].time) >= self.accord_th:
            tmp_accord = accord()
            tmp_accord.push_to_accord(tnote)
            self.accords.append(tmp_accord)

        else:
            self.accords[-1].push_to_accord(tnote)

    def push_finished(self):
        self.push_note(-1, self.accords[-1].notes[-1].time+320, self.accords[-1].notes[-1].time+320, -1)
        for i in range(len(self.accords)):
            self.accords[i].calc_avg_start()
            #self.accords[i].calc_first_start()
            self.accords[i].calc_avg_velocity()
        self.mark_beat()
        self.divide_hands()

        

    def divide_hands(self):
        del self.accords[-1]
        self.accords_left = []
        self.accords_right = []
        for i in range(len(self.accords)):
            accord_it = self.accords[i]
            accord_left = accord()
            accord_right = accord()
            accord_left.time = self.accords[i].time
            accord_right.time = self.accords[i].time

            for j in range(len(accord_it.notes)):
                note_it = accord_it.notes[j]
                if note_it.pitch <= 38:
                    accord_left.push_to_accord(note_it)
                else:
                    accord_right.push_to_accord(note_it)

            if len(accord_left.notes)>0:
                self.accords_left.append(accord_left)
                self.accords_left[-1].beat = accord_it.beat
                if len(accord_right.notes)==0:
                    rest = accord()
                    rest.vice = True
                    rest.pitch = -1
                    rest.beat = accord_it.beat
                    self.accords_right.append(rest)
            if len(accord_right.notes)>0:
                self.accords_right.append(accord_right)
                self.accords_right[-1].beat = accord_it.beat
                if len(accord_left.notes)==0:
                    rest = accord()
                    rest.vice = True
                    rest.pitch = -1
                    rest.beat = accord_it.beat
                    self.accords_left.append(rest)

    def get_interval(self, accords):
        pitches_starts = [[] for i in range(88)]
        for i in range(len(accords)-1):
            for j in range(len(accords[i].notes)):
                pitches_starts[accords[i].notes[j].pitch-8].append(accords[i].notes[j].time)
        pitches_diff = []
        for i in range(88):
            for j in range(len(pitches_starts[i])-1):
                diff = pitches_starts[i][j+1] - pitches_starts[i][j]
                pitches_diff.append(diff)

        distances = []
        ranges = [0.01*x for x in range(800,7000)]
        for interval in ranges:
            distance = 0
            for diff in pitches_diff:
                left = abs(diff / interval - round(diff/interval))
                distance += left / np.sqrt(interval)
            distances.append(distance)
        interval = np.argmin(distances)/100 + 8
        return interval

    def mark_beat(self):
        ############ 
        n = 4
        temp = int(self.accords[-1].time/n) #+1
        bars = [[] for x in range(n+50)]
        indexes = [[] for x in range(n+50)]
        for i in range(len(self.accords)):
            bars[int(self.accords[i].time/temp)].append(self.accords[i])
            indexes[int(self.accords[i].time/temp)].append(i)
        while(True):
            if len(indexes[-1])>0:
                break
            else:
                del bars[-1]
                del indexes[-1]


        for index_bar in range(len(bars)):
            interval = self.get_interval(bars[index_bar])
            print('interval:',interval)
            for index_accord in range(len(bars[index_bar])-1):
                frames = bars[index_bar][index_accord+1].time - bars[index_bar][index_accord].time
                #print(frames, end=" : ")
                beat = self.get_near_beat(frames/interval)
                if not beat==0:
                    beat = int(16/beat)
                #print(beat, end="  ")
                self.accords[indexes[index_bar][index_accord]].beat = beat
            if index_bar < len(bars)-1:
                frame_last = bars[index_bar+1][0].time - bars[index_bar][-1].time
                beat_last = self.get_near_beat(frame_last/interval)
                if not beat_last == 0:
                    beat_last = int(16/beat_last)
                self.accords[indexes[index_bar][-1]].beat = beat_last
            else:
                self.accords[indexes[index_bar][-1]].beat = 1

            #print("\n-----------------------\n")
        for i in range(len(self.accords)):
            print(self.accords[i].beat, end=" ")
        self.interval = 23

    def get_near_beat(self,frame):
        if frame > 32:
            return round(frame/16)*16
        elif frame > 16:
            return round(frame/8)*8
        elif frame > 8:
            return round(frame/4)*4
        elif frame > 4:
            return round(frame/2)*2
        elif frame <= 4 and frame>=0.75:
            return round(frame)
        elif frame<0.75 and frame>0.25:
            return 0.5
        else:
            return 0
            #return round(frame)

        
    def make_score(self, filename='test', title='test'):
        self.push_finished()

        self.bar = 4
        self.key = 'C'
        lily_string = lily_notation(self.accords_left, self.accords_right, self.bar, self.key, title, midi=0)
        try:
            f=open(filename+".ly","w")
            f.write(lily_string)
            f.close()
        except:
            print("except")
        #p = subprocess.Popen(filename+".ly", shell=True).wait()
        #os.remove(filename+".ly")
        #os.remove(filename+".log")


    def make_midi(self, filename='output'):
        self.push_finished()

        midi = pretty_midi.PrettyMIDI(initial_tempo = 120)
        piano = pretty_midi.Instrument(program=1)

        for i in range(len(self.accords)):
            accord_it = self.accords[i]
            start_time = accord_it.time * self.time_resolution
            end_time = start_time + 0.25
            velocity = accord_it.velocity
            for j in range(len(accord_it.notes)):
                note_it = accord_it.notes[j]
                midi_note = pretty_midi.Note(pitch=int(note_it.pitch+21), start=start_time, end=end_time, velocity=int(velocity))
                piano.notes.append(midi_note)
        
        midi.instruments.append(piano)
        midi.write(filename+'.mid')
        print("midi generated")

    def make_midi_beat(self, filename='output'):

        self.push_finished()

        midi = pretty_midi.PrettyMIDI(initial_tempo = 120)
        piano = pretty_midi.Instrument(program=1)

        start_time = 3
        for i in range(len(self.accords)):
            accord_it = self.accords[i]
            start_time = start_time + 16/(accord_it.beat)*self.interval*self.time_resolution
            end_time = start_time + 0.25
            #velocity = accord_it.velocity
            velocity=100
            for j in range(len(accord_it.notes)):
                note_it = accord_it.notes[j]
                midi_note = pretty_midi.Note(pitch=int(note_it.pitch+21), start=start_time, end=end_time, velocity=int(velocity))
                piano.notes.append(midi_note)
        
        midi.instruments.append(piano)
        midi.write(filename+'.mid')
        print("midi generated")
    
    def make_csv(self,filename) :
        csv.register_dialect(
            'mydialect',
            delimiter = ',',
            quotechar = '"',
            doublequote = True,
            skipinitialspace = True,
            lineterminator = '\r\n',
            quoting = csv.QUOTE_MINIMAL)
        with open(filename, 'w', newline='') as mycsvfile:
            thedatawriter = csv.writer(mycsvfile, dialect='mydialect')
            thedatawriter.writerow([self.time_resolution])
            for accord in self.accords:
                for note in accord.notes:
                    thedatawriter.writerow([note.pitch,note.time,note.velocity])
    
    def read_csv(self, filename) :
        csv.register_dialect(
            'mydialect',
            delimiter = ',',
            quotechar = '"',
            doublequote = True,
            skipinitialspace = True,
            lineterminator = '\r\n',
            quoting = csv.QUOTE_MINIMAL)

        with open(filename, 'r') as mycsvfile:
            thedata = csv.reader(mycsvfile, dialect='mydialect')
            i=0
            for row in thedata:
                if(i==0):
                    self.time_resolution = float(row[0])
                    i+=1
                else :
                    pitch = int(row[0])
                    start = int(row[1])
                    velocity = int(row[2])
                    self.push_note(pitch, start, start+25, velocity)

if __name__=='__main__':
    
    result = score(0)
    result.read_csv('작은별진짜.csv')
    result.make_midi_beat('작은별진짜')
    

    '''
    result = score(0.05)
    result.push_note(57,102,4,100) #2
    #result.push_note(57,20,4,100)
    result.push_note(57,139,4,100) #1
    result.push_note(57,160,4,100) #1
    result.push_note(57,179,4,100) #1
    result.push_note(57,199,4,100) #0
    result.push_note(57,205,4,100) #0
    result.push_note(57,211,4,100) #0.5
    result.push_note(57,220,4,100) #2
    result.push_note(57,264,4,100) #1
    result.push_note(67,282,4,100)
    result.make_midi_beat("results/test")
    # 답 : 2 1 1 1 1 2 1
    '''
    

    '''
    result = score(0.05)
    result.push_note(55,102,4,100) #2
    #result.push_note(57,20,4,100)
    result.push_note(57,139,4,100) #1
    result.push_note(27,160,4,100) #1
    result.push_note(57,179,4,100) #1
    result.push_note(59,199,4,100) #0.5
    result.push_note(51,200,4,100)
    result.push_note(61,211,4,100) #0.5
    result.push_note(63,220,4,100) #2
    result.push_note(57,264,4,100) #1
    result.push_note(67,282,4,100)
    result.make_score()
    '''
    