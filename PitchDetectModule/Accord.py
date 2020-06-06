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
from scipy.ndimage import filters
from scipy import signal

def get_interval_in_pitches(accords):
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
    ranges = [0.01*x for x in range(800,3000)]
    for interval in ranges:
        distance = 0
        for diff in pitches_diff:
            left = abs(diff / interval - round(diff/interval))
            distance += left / np.sqrt(interval)
        distances.append(distance)
    interval = np.argmin(distances)/100 + 8
    return interval

class note:
    def __init__(self, pitch, start, velocity):
        self.pitch = pitch
        self.time = start
        self.velocity = velocity

class accord:
    def __init__(self):
        self.vice = 0
        self.notes = []
        self.beat = 0
        self.velocity = 0
        self.time = 0
        self.tempo = 0

    def push_to_accord(self, note):
        self.notes.append(note)

    def calc_avg_velocity(self):
        for note in self.notes:
            self.velocity += note.velocity
        self.velocity /= len(self.notes)
        self.velocity = int(self.velocity)

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
        self.key = 'c'
        self.interval = 0

    def push_note(self, pitch_num, s, e, velocity, tempo):
        tnote = note(pitch_num, s, velocity)
        if len(self.accords)==0:
            tmp_accord = accord()
            tmp_accord.tempo = tempo
            tmp_accord.push_to_accord(tnote)
            self.accords.append(tmp_accord)

        elif abs(tnote.time - self.accords[-1].notes[-1].time) >= self.accord_th:
            self.accords[-1].calc_avg_start()
            self.accords[-1].calc_avg_velocity()
            tmp_accord = accord()
            tmp_accord.tempo = tempo
            tmp_accord.push_to_accord(tnote)
            self.accords.append(tmp_accord)

        else:
            self.accords[-1].push_to_accord(tnote)

    def push_finished(self):
        
        self.push_note(-10, self.accords[-1].notes[-1].time+320, self.accords[-1].notes[-1].time+320, -10, 0)
        self.accords[-1].vice=-1
        self.accords[-1].time = self.accords[-2].notes[-1].time+320
        self.mark_beat()
        self.mark_symboles()
        self.divide_hands()
        #self.detect_key()


    def mark_symboles(self):
        # divide hands 후에 크레센도, 전에 accent실행해야함
        velocities = []
        tempos = []
        for i in range(len(self.accords)):
            velocities.append(self.accords[i].velocity)
            tempos.append(self.accords[i].tempo)
        velocities = np.array(velocities)
        tempos = np.array(tempos)
        
        tempos = filters.gaussian_filter1d(tempos, 40)
        accents, _ = signal.find_peaks(velocities, prominence=10, height = max(velocities)*0.8)

        pianoforte = filters.gaussian_filter1d(velocities, 50)
        pianoforte_index = [0 for x in range(len(pianoforte))]
        tmp = (max(pianoforte)+1-min(pianoforte))/4
        bounds = []
        i = 0
        while True:
            if i >= len(pianoforte):
                break
            bound = (int((pianoforte[i]-min(pianoforte))/tmp))
            bounds.append(bound)
            if bound == 0:
                pianoforte_index[i] = -1
                while i<len(pianoforte) and (int((pianoforte[i]-min(pianoforte))/tmp))==0 :
                    bounds.append(bound)
                    i += 1
            elif bound == 3:
                pianoforte_index[i] = 1
                while i<len(pianoforte) and (int((pianoforte[i]-min(pianoforte))/tmp))==3 :
                    bounds.append(bound)
                    i += 1
            else:
                i += 1

        symbol_accords = []
         
        i = 0
        lastbound = -1
        startcrecendo= 0
        startdecrecendo=0
        oncrecendo = False
        ondecrecendo = False
        while True :
            if i >= len(bounds)-1 or i >= len(self.accords) :
                break
            else :
                symbol_accords.append(self.accords[i])

            if i in accents and bounds[i] != 0:
                tmp = accord()
                tmp.vice = -8

                symbol_accords.append(tmp)
                lastbound = 1
     
            if lastbound != 0 and bounds[i]==0 and ondecrecendo==True :
                tmp = accord()
                tmp.vice = -4
                lastbound = bounds[i]
                symbol_accords.insert(startdecrecendo+1,tmp)
                tmp = accord()
                tmp.vice = -5
                symbol_accords.append(tmp)
                ondecrecendo=False
                oncrecendo=True
            elif bounds[i] == 0 and lastbound !=0 :
                tmp = accord()
                tmp.vice = -6
                symbol_accords.append(tmp)

                lastbound = bounds[i]
                
                oncrecendo=True
                ondecrecendo=False
                startcrecendo = i

            if lastbound != 3 and bounds[i]==3 and oncrecendo==True :
                tmp = accord()
                tmp.vice = -3
                lastbound = bounds[i]
                symbol_accords.insert(startcrecendo+1,tmp)
                tmp = accord()
                tmp.vice = -5
                symbol_accords.append(tmp)
                ondecrecendo=True
                oncrecendo=False                
  
            elif bounds[i] == 3 and lastbound != 3 :
                tmp = accord()
                tmp.vice = -7
                symbol_accords.append(tmp)
                lastbound = bounds[i]
                startdecrecendo = i
                ondecrecendo=True
                oncrecendo=False

            i+=1

        self.accords = symbol_accords

        for i in range(len(self.accords)):
            print(self.accords[i].vice, end = " ")
        print('\n')

        ##악센트 음표 뒤 -8
        ##크레센도 -3 음표 뒤
        ## 디크레 -4 음표 뒤
        ## 크레 디크레 끝나는거 -5 뒤
        ##포르테 -7 음표 뒤
        ##피아니 -6 음표 뒤


    def detect_key(self):
        pitch_count = [0 for _ in range (0, 88)]
        for accord in self.accords_left:
            if accord.vice==0:
                for note in accord.notes:
                    pitch_count[note.pitch] += 1
        for accord in self.accords_right:
            if accord.vice==0:
                for note in accord.notes:
                    pitch_count[note.pitch] += 1
        gyeLUT = ['c','cis','d','dis','e','f','fis','g','gis','a','ais','b']

        gye_count = [0 for _ in range(0, 12)]
        for i in range(len(pitch_count)):
            gye, _ = LUT(i)
            gye_count[gyeLUT.index(gye)] += pitch_count[i]
        #print(gye_count)
        self.key = 'c'
        if(gye_count[6] / gye_count[5] >= gye_count[10] / gye_count[11]):
            if(gye_count[6] > gye_count[5]):#파샵
                self.key = 'g'
                if(gye_count[1] > gye_count[0]):#도샵
                    self.key = 'd'
                    if(gye_count[8] > gye_count[7]):#솔샵
                        self.key = 'a'
                        if(gye_count[3] > gye_count[2]):#레샵
                            self.key = 'e'
                            if(gye_count[10] > gye_count[9]):#라샵
                                self.key = 'b'
                                if(gye_count[5] > gye_count[4]):#미샵(파)
                                    self.key = 'fis'
                                    if(gye_count[0] > gye_count[11]):#시샵(도)
                                        self.key = 'cis'
        elif(gye_count[6] / gye_count[5] <= gye_count[10] / gye_count[11]):
            if(gye_count[10] > gye_count[11]):#시플랫
                self.key = 'f'
                if(gye_count[3] > gye_count[4]):#미플랫
                    self.key = 'bes'
                    if(gye_count[8] > gye_count[9]):#라플랫
                        self.key = 'ees'
                        if(gye_count[1] > gye_count[2]):#레플랫
                            self.key = 'aes'
                            if(gye_count[6] > gye_count[7]):#솔플랫
                                self.key = 'des'
                                if(gye_count[11] > gye_count[0]):#도플랫(시)
                                    self.key = 'ges'
                                    if(gye_count[4] > gye_count[5]):#파플랫(미)
                                        self.key = 'ces'
        else:
            self.key = 'c'

    def divide_hands(self):
        del self.accords[-1]
        print('\nc', len(self.accords))
        self.accords_left = []
        self.accords_right = []
        for i in range(len(self.accords)):
            accord_it = self.accords[i]

            if accord_it.vice==0 or accord_it.vice==1:

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
                        rest.vice = -1
                        rest.beat = accord_it.beat
                        self.accords_right.append(rest)
                if len(accord_right.notes)>0:
                    self.accords_right.append(accord_right)
                    self.accords_right[-1].beat = accord_it.beat
                    if len(accord_left.notes)==0:
                        rest = accord()
                        rest.vice = -1
                        rest.beat = accord_it.beat
                        self.accords_left.append(rest)
            
            else:
                self.accords_right.append(accord_it)
                #self.accords_left.append(accord_it)

        i=0
        accords_left = []
        while i<len(self.accords_left)-1:
            if self.accords_left[i].vice==0 and self.accords_left[i+1].vice!=0:
                start = self.accords_left[i]
                beatsum = self.accords_left[i].beat
                while i<len(self.accords_left)-1 and self.accords_left[i+1].vice!=0:
                    i+=1
                    beatsum += self.accords_left[i].beat
                accords_left.append(start)
                accords_left[-1].beat = beatsum
            else:
                accords_left.append(self.accords_left[i])
            i+=1
        accords_left.append(self.accords_left[-1])
        self.accords_left = accords_left

        i=0
        accords_right = []
        while i<len(self.accords_right):
            if self.accords_right[i].vice!=0:
                start = self.accords_right[i]
                beatsum = 0
                while i<len(self.accords_right) and self.accords_right[i].vice!=0:
                    beatsum += self.accords_right[i].beat
                    i += 1
                accords_right.append(start)
                accords_right[-1].beat = beatsum
            else:
                accords_right.append(self.accords_right[i])
                i += 1
        self.accords_right = accords_right

        print('r' ,len(self.accords_right))
        print('l' ,len(self.accords_left))
        print('########### vices ##################')
        for i in range(len(self.accords)):
            print(self.accords[i].vice, end=" ")
        print('\n')
        for i in range(len(self.accords_right)):
            print(self.accords_right[i].vice, end=" ")
        print('\n')
        for i in range(len(self.accords_left)):
            print(self.accords_left[i].vice, end = " ")
        print('\n##################################')

        #del(self.accords_left[-1])


    def mark_beat(self):
        ############ 
        n = 1
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

        double = False
        for index_bar in range(len(bars)):
            #interval = get_interval_in_pitches(bars[index_bar])
            interval = self.interval
            print('interval:',interval)
            for index_accord in range(len(bars[index_bar])-1):
                frames = bars[index_bar][index_accord+1].time - bars[index_bar][index_accord].time
                #print(frames, end=" : ")
                beat = self.get_near_beat(frames/interval)
                if beat==0.5:
                    double = True
                #print(beat, end="  ")
                self.accords[indexes[index_bar][index_accord]].beat = beat
            if index_bar < len(bars)-1:
                frame_last = bars[index_bar+1][0].time - bars[index_bar][-1].time
                beat_last = self.get_near_beat(frame_last/interval)
                if beat_last == 0.5:
                    double = True
                self.accords[indexes[index_bar][-1]].beat = beat_last
            else:
                self.accords[indexes[index_bar][-1]].beat = 1

            #print("\n-----------------------\n")
        if double:
            for i in range(len(self.accords)):
                self.accords[i].beat = int(self.accords[i].beat*2)
        for i in range(len(self.accords)):
            print(self.accords[i].beat, end=" ")

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

        
    def make_score(self, filename='test', title='test'):
        self.bar = 4
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
        midi = pretty_midi.PrettyMIDI(initial_tempo = 120)
        piano = pretty_midi.Instrument(program=1)

        for i in range(len(self.accords)):
            accord_it = self.accords[i]
            start_time = accord_it.time * self.time_resolution
            end_time = start_time + 0.25
            velocity = int(accord_it.velocity)
            for j in range(len(accord_it.notes)):
                note_it = accord_it.notes[j]
                midi_note = pretty_midi.Note(pitch=int(note_it.pitch+21), start=start_time, end=end_time, velocity=int(velocity))
                piano.notes.append(midi_note)
        
        midi.instruments.append(piano)
        midi.write(filename+'.mid')
        print("midi generated")

    def make_midi_beat(self, filename='output'):
        midi = pretty_midi.PrettyMIDI(initial_tempo = 120)
        piano = pretty_midi.Instrument(program=1)

        start_time = 3
        
        for i in range(len(self.accords_left)):
            accord_it = self.accords_left[i]

            if accord_it.vice==0 or accord_it.vice==-1:
            
                end_time = start_time + 0.25
                velocity = int(accord_it.velocity)
                
                for j in range(len(accord_it.notes)):
                    note_it = accord_it.notes[j]
                    print(note_it.pitch, end= " ")
                    midi_note = pretty_midi.Note(pitch=int(note_it.pitch+21), start=start_time, end=end_time, velocity=100)
                    piano.notes.append(midi_note)
            
                start_time = start_time + (accord_it.beat)*self.interval*self.time_resolution

            else:
                print('#',accord_it.vice, end= " ")

        start_time = 3
        for i in range(len(self.accords_right)):
            accord_it = self.accords_right[i]

            if accord_it.vice==0 or accord_it.vice==-1:
            
                end_time = start_time + 0.25
                velocity = int(accord_it.velocity)

                for j in range(len(accord_it.notes)):
                    note_it = accord_it.notes[j]
                    print(note_it.pitch, end= " ")
                    midi_note = pretty_midi.Note(pitch=int(note_it.pitch+21), start=start_time, end=end_time, velocity=100)
                    piano.notes.append(midi_note)
            
                start_time = start_time + (accord_it.beat)*self.interval*self.time_resolution

            else:
                print('#',accord_it.vice, end= " ")
        
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
            thedatawriter.writerow([self.time_resolution, self.interval])
            for accord in self.accords:
                for note in accord.notes:
                    thedatawriter.writerow([note.pitch,note.time,note.velocity,accord.tempo])
    
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
                    self.interval = float(row[1])
                    i+=1
                else :
                    pitch = int(row[0])
                    start = int(row[1])
                    velocity = int(row[2])
                    tempo = float(row[3])
                    self.push_note(pitch, start, start+25, velocity, tempo)

if __name__=='__main__':
    
    result = score(0)
    result.read_csv('작은별진짜.csv')
    result.push_finished()
    result.make_midi_beat('작은별진짜')
    result.make_score()