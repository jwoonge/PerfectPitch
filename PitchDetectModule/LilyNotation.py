from collections import namedtuple


def lily_notation(lh_sheet, rh_sheet, bar, key, filename, midi=0):
    ret = "\\version \"2.20.0\"\n\\header{\n  title = \"" + filename + "\"\n}"
    RH_head = "rhMusic = {\n\t"
    LH_head = "lhMusic = {\n\t"
    RH_body = get_body(rh_sheet)
    LH_body = get_body(lh_sheet)
    fin = "\n}\n\n"
    midi_str = ""
    if midi>0:
        midi_str = "  \\midi { \n    \\tempo 4 = " + str(midi) + "\n  }\n"
    score_data = "\n\\score {\n  \\new PianoStaff <<\n    \\new Staff = \"RH\"  <<\n      \\key " + key + " \\major\n      \\rhMusic\n    >>\n    \\new Staff = \"LH\" <<\n      \\key " + key + "\\major\n      \\clef \"bass\"\n      \\lhMusic\n    >>\n  >>\n" + midi_str + "}"
    
    ret += "\n" + RH_head + RH_body + fin + LH_head + LH_body + fin + score_data
    return ret
        
def divide_beat(accords, bar):
    note_temp = namedtuple("note", "pitch start beat velocity")
    i = 0
    tie = accord()
    tie.vice = True
    tie.pitch = 0
    while(i < len(accords)):
        if not accords[i].vice:
            note_tf = []
            for note in accords[i].notes:
                note_tf.append(note.start // bar == (note.start + note.beat - 1) // bar)
            if all(note_tf):
                i += 1
            else:
                over = accord()
                for note in accords[i]:
                    if not note.start // bar == (note.start + note.beat - 1) // bar:
                        forward_beat = note.beat - (note.start+note.beat)%bar
                        backward_beat = note.beat - forward_beat
                        backward_start = note.start + note.beat - (note.start + note.beat) % bar
                        accords[i].notes.remove(note)
                        accords[i].notes.append(note_temp(note.pitch, note.start, forward_beat, note.velocity))
                        over.push_to_accord(note_temp(note.pitch, backward_start, backward_beat, note.velocity))
                        accords.insert(i+1, tie)
                        accords.insert(i+2, over)
                i += 3
    return accords

def translate_beat(accord, bar):
    for note in accord:
        note.beat = bar / beat #bar = 한 마디에 들어가는 박자 / beat는 박자를 음표로 환산한 것이 되야 함

def get_body(accords):
    body = ""
    for accord in accords:
        if accord.vice==True:
            body += vice_to_string(accord)
        else:
            body += accord_to_string(accord)
    return body


def LUT(pitch_num):
    gye = (pitch_num-3)%12
    oc = int((pitch_num-3)/12)
    gyeLUT = ['c','cis','d','dis','e','f','fis','g','gis','a','ais','b']
    gye = gyeLUT[gye]
    return gye, oc


def vice_to_string(accord):#############
    #if(accord.pitch == ):
    return ""

def accord_to_string(accord):
    if accord.beat == -1:
        accord.beat = 16
    start = "\\relative {<"
    body = ""
    fin = ">" + str(accord.beat) + '} '

    gye, oc = LUT(accord.notes[0].pitch)
    body += gye
    for i in range(0, oc - 2):
        body += '\''
    for i in range(0, 2 - oc):
        body += ','
    body += " "
    last = oc
    
    for i in range(1, len(accord.notes)):
        gye, oc = LUT(accord.notes[i].pitch)
        body += gye
        for j in range(oc-last):##########
            body += "\'"
        for j in range(last-oc):
            body += ","
        body += " "
    
    return start + body + fin
    