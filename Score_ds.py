from collections import namedtuple

def LUT(pitch_num):
    gye = (pitch_num-3)%12
    oc = int((pitch_num-3)/12)
    gyeLUT = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    gye = gyeLUT[gye]
    return gye, oc

class score:
    def __init__(self):
        print("악보 생성")
        self.note_stack = []
        self.midi_data = []

    def push_note(self, pitch_num, i_s, velocity):
        temp = namedtuple('notes',['pitch','start','velocity'])
        temp.pitch = pitch_num
        temp.start = i_s
        temp.velocity = velocity
        self.note_stack.append(temp)

    def translate_stack(self):
        print("TODO")

    def print_notes(self):
        for i in range(len(self.note_stack)):
            gye, oc = LUT(self.note_stack[i].pitch)
            print(gye, oc)

