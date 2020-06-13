from Score_ds import accord
from Score_ds import score
from Score_ds import note
import copy

def lily_notation(lh_sheet, rh_sheet, bar, key, filename, author, bpm, midi=0):
    ret = "\\version \"2.20.0\"\n\\header{\n  dedication=\"   \"\n  title = \"" + filename + "\"\n  subtitle = \"     \"\n  composer = \"" + author + "\"\n  arranger = \"   \"\n}"
    RH_head = "rhMusic = {\n\t\\tempo 4 = "+str(int(bpm))+"\n\t"
    LH_head = "lhMusic = {\n\t"
    minor = False

    if key in ['f', 'bes', 'ees', 'aes', 'des', 'ges', 'ces']:
        minor = True

    lh_sheet = merge_rests(lh_sheet)
    rh_sheet = merge_rests(rh_sheet)

    lh_sheet = divide_beat(lh_sheet, bar)
    rh_sheet = divide_beat(rh_sheet, bar)

    lh_sheet = translate_beat(lh_sheet)
    rh_sheet = translate_beat(rh_sheet)

    RH_body = get_body(rh_sheet, minor)
    LH_body = get_body(lh_sheet, minor)

    fin_bar = "\\bar \"|.\""
    fin = fin_bar + "\n}\n\n"
    midi_str = ""
    if midi>0:
        midi_str = "  \\midi { \n    \\tempo 4 = " + str(midi) + "\n  }\n"
    score_data = "\n\\score {\n  \\new PianoStaff <<\n    \\new Staff = \"RH\"  <<\n      \\key " + key + " \\major\n      \\rhMusic\n    >>\n    \\new Staff = \"LH\" <<\n      \\key " + key + "\\major\n      \\clef \"bass\"\n      \\lhMusic\n    >>\n  >>\n" + midi_str + "}"
    
    ret += "\n" + RH_head + RH_body + fin + LH_head + LH_body + fin + score_data
    return ret

def get_body(accords, minor):
    body = ""
    for accord_it in accords:
        if accord_it.vice !=0 :
            body += vice_to_string(accord_it)
        else:
            body += accord_to_string(accord_it, minor)
    return body

def beat_table(beat):
    bt = ['$', '16', '8', '8.', '4', '!', '4.', '!', '2', '!', '!', '!', '2.', '!', '!', '!', '1']
    return bt[int(beat)]

def LUT(pitch_num):
    gye = (pitch_num-3)%12
    oc = int((pitch_num-3)/12)
    gyeLUT = ['c','cis','d','dis','e','f','fis','g','gis','a','ais','b']
    gye = gyeLUT[gye]
    return gye, oc

def LUT_minor(pitch_num):
    gye = (pitch_num-3)%12
    oc = int((pitch_num-3)/12)
    gyeLUT = ['c','des','d','ees','e','f','ges','g','aes','a','bes','b']
    gye = gyeLUT[gye]
    return gye, oc

def accord_to_string(accord_it, minor):
    table = ['a','b','c','d','e','f','g']

    if len(accord_it.notes)>0:
        start = "\\relative {<"
        body = ""
        fin = ">" + beat_table(accord_it.beat) + '} '

        if not minor:
            gye, oc = LUT(accord_it.notes[0].pitch)
        else:
            gye, oc = LUT_minor(accord_it.notes[0].pitch)
        body += gye
        
        for i in range(0, oc - 2):
            body += '\''
        for i in range(0, 2 - oc):
            body += ','
        body += " "
        
        last_pitch = accord_it.notes[0].pitch
        last_gye = gye
        last_oc = oc

        for i in range(1, len(accord_it.notes)):
            last_index = table.index(last_gye[0])
            gye, oc = LUT(accord_it.notes[i].pitch)
            left = []
            right = []
            for j in range(1,4):
                left.append(table[(last_index-j)%7])
                right.append(table[(last_index+j)%7])
            body += gye
            dif = accord_it.notes[i].pitch - last_pitch
            oc_dif = int((dif)/12)
            if dif < 0 and gye[0] in right:
                oc_dif -= 1
            elif dif > 0 and gye[0] in left:
                oc_dif += 1
            for j in range(oc_dif):
                body += "\'"
            for j in range(-oc_dif):
                body += ","
            body += " "
            last_pitch = accord_it.notes[i].pitch
            last_gye = gye
            last_oc = oc
        
        return start + body + fin

    else:
        return ""

def vice_to_string(accord_it):
    ret = ""
    if(accord_it.vice == -1):##rest
        ret += " r" + beat_table(accord_it.beat)
    elif(accord_it.vice == -2):##연음줄
        ret += "  ~"
    elif(accord_it.vice == -3):##crec
        ret += " \\< "
    elif(accord_it.vice == -4):##decrec
        ret += " \\> "
    elif(accord_it.vice == -5):#end crec or decrec
        ret += " \\! "
    elif(accord_it.vice == -6):#piano
        ret += ' \\p '
    elif(accord_it.vice == -7):#forte
        ret += ' \\f '
    elif(accord_it.vice == -8):#accent
        ret += ' -> '
    elif(accord_it.vice == -9):#rit
        ret += '\\mark \"rit\"'
    elif(accord_it.vice == -10):#accel
        ret += '\\mark \"accel\"'
    elif(accord_it.vice == -11):#enter
        #ret += '\\ bar \"\" \\break\n    '
        ret += ' '
    elif(accord_it.vice == -12):#divide_bar
        #ret += ' | \n'
        ret += " "
    return ret


def divide_beat(accords, bar):
    new = []

    bar = bar * 4
    enter_th = 4

    tie = accord()
    tie.vice = -2
    tie.beat = 0
    tie.notes = []

    enter = accord()
    enter.vice = -11
    enter.beat = 0
    enter.notes = []

    bd = accord()
    bd.vice = -12
    bd.beat = 0
    bd.notes = []

    left = 0
    bar_count = 0

    for accord_it in accords:
        accord_it.beat = round(accord_it.beat)
        quo = int((left + accord_it.beat)/bar)

        if accord_it.beat == 0:
            new.append(accord_it)
        else:
            if quo <= 1: # 온음표가 안생기는 경우
                if left + accord_it.beat < bar: # 안넘어가는 경우
                    new.append(accord_it)
                    left += accord_it.beat
                
                elif left + accord_it.beat == bar: # 안넘어가고 딱 꽉찬 경우
                    new.append(accord_it)
                    bar_count += 1
                    new.append(bd)
                    if bar_count % enter_th == 0:
                        new.append(enter)
                    left = 0
            
                else: # 마디 하나 넘어가는 경우
                    forward = copy.deepcopy(accord_it)
                    forward.beat = bar-left
                    
                    new.append(forward)
                    bar_count += 1

                    if accord_it.vice==0:
                        new.append(tie)
                    new.append(bd)
                    if bar_count % enter_th == 0:
                        new.append(enter)
                    backward = copy.deepcopy(accord_it)
                    backward.beat = accord_it.beat - (bar-left)
                    new.append(backward)

                    left = (left + accord_it.beat) % bar
            
            else: # 온음표가 생기는 경우
                forward = copy.deepcopy(accord_it)
                forward.beat = bar - left
                new.append(forward)
                bar_count += 1
                if accord_it.vice==0:
                    new.append(tie)
                new.append(bd)

                if bar_count % enter_th == 0:
                    new.append(enter)
                
                for i in range(quo-1):
                    whole_note = copy.deepcopy(accord_it)
                    whole_note.beat = bar
                    new.append(whole_note)
                    
                    if accord_it.vice==0:
                        new.append(tie)

                    bar_count += 1
                    new.append(bd)

                    if bar_count % enter_th == 0:
                        new.append(enter)

                    
                backward = copy.deepcopy(accord_it)
                backward.beat = (left + accord_it.beat) % bar
                if not backward.beat == 0:
                    if accord_it.vice==0:
                        new.append(tie)

                    new.append(backward)

                left = (left + accord_it.beat) % bar

    
    i = -1
    accord_last = new[i]
    while abs(i) < len(new) and accord_last.beat==0:
        i += -1
        accord_last = new[i]
    new[i].beat = new[i].beat + bar - left
    
    return new

def merge_rests(accords):
    new = []
    i = 0
    while i<len(accords):
        if accords[i].vice==-1:
            vice = []
            new.append(accords[i])
            beatsum = accords[i].beat
            i += 1
            while i < len(accords) and accords[i].vice!=0:
                beatsum += accords[i].beat
                if accords[i].vice!=-1:
                    vice.append(accords[i])
                i += 1
            new[-1].beat = beatsum
            for j in range(len(vice)):
                new.append(vice[j])
        else:
            new.append(accords[i])
            i += 1
    return new

def translate_beat(accords):
    new = []
    
    tie = accord()
    tie.vice = -2
    tie.beat = 0
    tie.notes = []

    for accord_it in accords:
        if accord_it.beat == 0:
            new.append(accord_it)
        else:
            beat = translate_beat_sub(accord_it.beat)
            for i in range(len(beat)-1):
                accord_tmp = copy.deepcopy(accord_it)
                accord_tmp.beat = beat[i]
                new.append(accord_tmp)
                if accord_it.vice == 0:
                    new.append(tie)
            accord_tmp = copy.deepcopy(accord_it)
            accord_tmp.beat = beat[-1]
            new.append(accord_tmp)
    return new

def translate_beat_sub(beat):
    LUT = [1,2,3,4,6,8,12,16]
    ret = []
    left = beat
    while True:
        i = 0
        while i<len(LUT)-1 and LUT[i+1] <= left:
            i += 1
        left -= LUT[i]
        ret.append(LUT[i])
        if left == 0:
            break
    return ret

if __name__=='__main__':
    test = score(0.03)
    test.interval = 20
    
    for k in range(7):
        notes = []
        for i in range(12):
            notes.append(note(38+2*i+k, 100, 100))
        accorrd = accord()
        accorrd.notes = notes
        accorrd.beat = 2
        accorrd.vice = 0
        test.accords_left.append(accorrd)
        test.accords_right.append(accorrd)

        accorrd = accord()
        accorrd.notes.append(note(38+k,100,100))
        accorrd.vice = 0
        accorrd.beat = 4

        test.accords_left.append(accorrd)
        test.accords_right.append(accorrd)


    test.make_score()

