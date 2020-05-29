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
        self.notes = []
        self.beat = -1
        self.origin_frames = -1
        self.velocity = 0

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
        self.start /= len(self.notes)
    
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
        for i in range(len(self.accords)):
            self.accords[i].calc_avg_start()
            #self.accords[i].calc_first_start()
            self.accords[i].calc_avg_velocity()
        self.divide_hands()
        self.mark_beat()

    def divide_hands(self):
        for i in range(len(self.accords)):
            accord_it = self.accords[i]
            accord_left = accord()
            accord_right = accord()
            accord_left.time = self.accords[i].time
            accord_right.time = self.accords[i].time

            for j in range(len(accord_it.notes)):
                note_it = accord_it.notes[j]
                if note_it.pitch <= 50:
                    accord_left.push_to_accord(note_it)
                else:
                    accord_right.push_to_accord(note_it)

            if len(accord_left.notes)>0:
                self.accords_left.append(accord_left)
            if len(accord_right.notes)>0:
                self.accords_right.append(accord_right)


    def mark_beat(self):
        print("todo: mark_beat")
        intervals = []
        for i in range(1,len(self.accords)):
            intervals.append(int(self.accords[i].time - self.accords[i-1].time))
        cnt = Counter(intervals)
        self.interval = cnt.most_common(1)[0][0]
        ## interval 구할 때 범위 지정해서 줘보자
        metronome = []
        for i in range(int((self.accords[-1].time-self.accords[0].time) / self.interval)+1):
            metronome.append(i * self.interval)
        myframes = [0]
        for i in range(1,len(self.accords)):
            tmp = self.accords[i].time - self.accords[0].time
            myframes.append(tmp)
        
        metronome = np.array(metronome)
        myframes = np.array(myframes)

        euclidean_norm = lambda x, y : np.square(x-y)
        d, cost_matrix, acc_cost_matrix, path = dtw(myframes, metronome, dist=euclidean_norm)
        #print(path)

        print("\t interval: ",self.interval)

        for i in range(len(path[0])):
            self.accords[path[0][i]].beat = path[1][i]+1
            ###여따가 만약 다른 어코드가 같은 매트로놈으로 가는 경우, 0.5박도 넣어야 함

        for i in range(1,len(self.accords)):
            print(self.accords[i].beat - self.accords[i-1].beat, end=" ")
        
        
    def make_score(self, filename='test', title='test'):
        self.push_finished()
        self.bar = 4
        self.key = 'C'
        lily_string = LilyNotation.LilyNotation(self.accords_left, self.accords_right, self.bar, self.key, title)
        try:
            f=open(filename+".ly","w")
            f.write(lily_string)
            f.close()
        except:
            print("except")
        p = subprocess.Popen(filename+".ly", shell=True).wait()
        os.remove(filename+".ly")
        os.remove(filename+".log")


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

        for i in range(len(self.accords)):
            accord_it = self.accords[i]
            start_time = 3 + accord_it.beat*self.interval*self.time_resolution
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
    '''
    def make_csv(self,filename) :
        self.note_stack = sorted(self.note_stack, key=lambda x:x.start)
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
            for row in self.note_stack:
                thedatawriter.writerow([row.pitch,row.start,row.end,row.velocity])
    '''
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
                    end = int(row[2])
                    velocity = int(row[3])
                    self.push_note(pitch, start, end, velocity)

if __name__=='__main__':
    result = score(0)
    result.read_csv('results/아르카나.csv')
    result.make_midi('results/아르카나')
    result.make_midi_beat('results/아르카나비트')
