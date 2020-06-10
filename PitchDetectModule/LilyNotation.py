import Accord as ac
import copy

def lily_notation(lh_sheet, rh_sheet, bar, key, filename, midi=0):
    ret = "\\version \"2.20.0\"\n\\header{\n  title = \"" + filename + "\"\n}"
    RH_head = "rhMusic = {\n\t"
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
    fin = "\n}\n\n"
    midi_str = ""
    if midi>0:
        midi_str = "  \\midi { \n    \\tempo 4 = " + str(midi) + "\n  }\n"
    score_data = "\n\\score {\n  \\new PianoStaff <<\n    \\new Staff = \"RH\"  <<\n      \\key " + key + " \\major\n      \\rhMusic\n    >>\n    \\new Staff = \"LH\" <<\n      \\key " + key + "\\major\n      \\clef \"bass\"\n      \\lhMusic\n    >>\n  >>\n" + midi_str + "}"
    
    ret += "\n" + RH_head + RH_body + fin + LH_head + LH_body + fin + score_data
    return ret

def get_body(accords, minor):
    body = ""
    for accord in accords:
        if accord.vice !=0 :
            body += vice_to_string(accord)
        else:
            body += accord_to_string(accord, minor)
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

def accord_to_string(accord, minor):
    if len(accord.notes)>0:
        start = "\\relative {<"
        body = ""
        fin = ">" + beat_table(accord.beat) + '} '

        if not minor:
            gye, oc = LUT(accord.notes[0].pitch)
        else:
            gye, oc = LUT_minor(accord.notes[0].pitch)
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
            for j in range(oc-last):
                body += "\'"
            for j in range(last-oc):
                body += ","
            body += " "
        
        return start + body + fin

    else:
        return ""

def vice_to_string(accord):
    ret = ""
    if(accord.vice == -1):##rest
        ret += " r" + beat_table(accord.beat)
    elif(accord.vice == -2):##연음줄
        ret += "  ~"
    elif(accord.vice == -3):##crec
        ret += " \\< "
    elif(accord.vice == -4):##decrec
        ret += " \\> "
    elif(accord.vice == -5):#end crec or decrec
        ret += " \\! "
    elif(accord.vice == -6):#piano
        ret += ' \\p '
    elif(accord.vice == -7):#forte
        ret += ' \\f '
    elif(accord.vice == -8):#accent
        ret += ' -> '
    elif(accord.vice == -9):#rit
        ret += '\\mark \"rit\"'
    elif(accord.vice == -10):#accel
        ret += '\\mark \"accel\"'
    elif(accord.vice == -11):#enter
        #ret += '\\ bar \"\" \\break\n    '
        ret += ' '
    elif(accord.vice == -12):#divide_bar
        ret += ' | \n'
        #ret += " "
    return ret


def divide_beat(accords, bar):
    new = []

    bar = bar * 4
    enter_th = 4

    tie = ac.accord()
    tie.vice = -2
    tie.beat = 0
    tie.notes = []

    enter = ac.accord()
    enter.vice = -11
    enter.beat = 0
    enter.notes = []

    bd = ac.accord()
    bd.vice = -12
    bd.beat = 0
    bd.notes = []

    left = 0
    bar_count = 0

    for accord in accords:
        accord.beat = round(accord.beat)
        quo = (left + accord.beat) // bar

        if accord.beat == 0:
            new.append(accord)
        else:
            if quo <= 1: # 온음표가 안생기는 경우
                if left + accord.beat < bar: # 안넘어가는 경우
                    new.append(accord)
                    left += accord.beat
                
                elif left + accord.beat == bar: # 안넘어가고 딱 꽉찬 경우
                    new.append(accord)
                    bar_count += 1
                    new.append(bd)
                    if bar_count % enter_th == 0:
                        new.append(enter)
                    left = 0
            
                else: # 마디 하나 넘어가는 경우
                    forward = copy.deepcopy(accord)
                    forward.beat = bar-left
                    
                    new.append(forward)
                    bar_count += 1
                    new.append(bd)
                    if bar_count % enter_th == 0:
                        new.append(enter)
                    
                    if accord.vice==0:
                        new.append(tie)
                    backward = copy.deepcopy(accord)
                    backward.beat = accord.beat - (bar-left)
                    new.append(backward)

                    left = (left + accord.beat) % bar
            
            else: # 온음표가 생기는 경우
                forward = copy.deepcopy(accord)
                forward.beat = bar - left
                new.append(forward)
                bar_count += 1
                new.append(bd)

                if bar_count % enter_th == 0:
                    new.append(enter)
                
                for i in range(quo-1):
                    if accord.vice==0:
                        new.append(tie)

                    whole_note = copy.deepcopy(accord)
                    whole_note.beat = bar
                    new.append(whole_note)

                    bar_count += 1
                    new.append(bd)

                    if bar_count % enter_th == 0:
                        new.append(enter)

                    
                backward = copy.deepcopy(accord)
                backward.beat = (left + accord.beat) % bar
                if not backward.beat == 0:
                    if accord.vice==0:
                        new.append(tie)

                    new.append(backward)

                left = (left + accord.beat) % bar

    i = -1
    accord = new[i]
    while accord.beat==0:
        i += -1
        accord = new[i]
    new[i].beat = new[i].beat + bar - left

    '''
    barsum = []
    i = 0
    while True:
        if i >= len(new):
            break
        tempsum = 0
        while i < len(new) and new[i].vice!=-12:
            tempsum += new[i].beat
            i += 1
        
        barsum.append(tempsum)
        i += 1
    print(barsum)
    '''
    return new

def merge_rests(accords):
    new = []

    i = 0
    while i<len(accords):
        if accords[i].vice==-1:
            j = 1
            beatsum = accords[i].beat
            while i+j < len(accords)-1 and accords[i+j].vice!=0:
                if accords[i+j].vice!=-1:
                    new.append(accords[i+j])
                j += 1
                beatsum += accords[i+j].beat
            tmpaccord = accords[i]
            tmpaccord.beat = beatsum
            new.append(tmpaccord)
            i += j
        else:
            new.append(accords[i])
            i += 1

    return new

def translate_beat(accords):
    new = []
    
    tie = ac.accord()
    tie.vice = -2
    tie.beat = 0
    tie.notes = []

    for accord in accords:
        if accord.beat == 0:
            new.append(accord)
        else:
            beat = translate_beat_sub(accord.beat)
            for i in range(len(beat)-1):
                accord_tmp = copy.deepcopy(accord)
                accord_tmp.beat = beat[i]
                new.append(accord_tmp)
                if accord.vice == 0:
                    new.append(tie)
            accord_tmp = copy.deepcopy(accord)
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

