from collections import namedtuple
import pretty_midi

def LUT(pitch_num):
    gye = (pitch_num-3)%12
    oc = int((pitch_num-3)/12)
    gyeLUT = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    gye = gyeLUT[gye]
    return gye, oc

class score:
    '''
    note_stack : 스택에 찾은 정보 전부다 넣은거
    time_line : 하나씩 보고 시간정보 순으로 정렬
    midi_data : 재생해서 들어보기 위해 midi형식에 맞게 변환
    score_data : 시간정보 -> 박자정보로 바꾼 최종 score
    '''
    def __init__(self):
        self.note_stack = []
        self.time_line = [] #2차원 배열
        self.midi_data = []
        self.score_data = [] #음표 + 악상기호
        '''
        self.bpm = 120
        self.장단조
        self.frame_rate # 밖에서 받아옴
        self.window_size # 밖에서 받아옴
        '''
        

    def make_score(self, frame_length):
        self.translate_stack(frame_length)

    def push_note(self, pitch_num, i_s, velocity):
        temp = namedtuple('notes',['pitch','start','velocity'])
        temp.pitch = pitch_num
        temp.start = i_s
        temp.velocity = velocity
        self.note_stack.append(temp)

    def translate_stack(self, frame_length):
        self.time_line = [[] for j in range(frame_length)]
        for i in range(len(self.note_stack)):
            self.time_line[self.note_stack[i].start].append(self.note_stack[i]) ## self.note_stack[i].pitch
        

    def print_notes(self):
        for i in range(len(self.note_stack)):
            gye, oc = LUT(self.note_stack[i].pitch)
            print(gye, oc)

