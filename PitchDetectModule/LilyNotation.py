from collections import namedtuple
import Accord as AC

def lily_notation(lh_sheet, rh_sheet, bar, key, filename, midi=0):
    ret = "\\version \"2.20.0\"\n\\header{\n  title = \"" + filename + "\"\n}"
    RH_head = "rhMusic = {\n\t"
    LH_head = "lhMusic = {\n\t"
    minor = False
    if key in ['f', 'bes', 'ees', 'aes', 'des', 'ges', 'ces']:
        minor = True

    print("@@@@@",lh_sheet[0].beat)
    lh_sheet, rh_sheet = merge_rests(lh_sheet, rh_sheet)
    for i in range(len(lh_sheet)):
        print('after merge :', lh_sheet[i].beat)

    print(lh_sheet[0].beat)
    lh_sheet = divide_beat(lh_sheet, bar)
    rh_sheet = divide_beat(rh_sheet, bar)
    for i in range(len(lh_sheet)):
        print('after divide :', lh_sheet[i].beat)

    lh_sheet, rh_sheet = translate_beat(lh_sheet, rh_sheet)

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


def merge_rests(lh_sheet, rh_sheet):
    i=0
    print("left : ", len(lh_sheet))
    while(i < len(lh_sheet) and lh_sheet[i].vice != 0):
        sum = 0
        j = 0
        while i + j < len(lh_sheet) and lh_sheet[i+j].vice != 0:
            sum += lh_sheet[i+j].beat
            #print(i, j, sum)
            if(j >= 1):
                if lh_sheet[i+j].vice == -1:
                    lh_sheet.remove(lh_sheet[i+j])
                else:
                    j += 1
            else:
                j += 1
        lh_sheet[i].beat = lh_sheet[i].beat + sum
        i += 1
    print("after : ", len(lh_sheet))
    print(lh_sheet[0].beat)
    i=0
    while(i < len(rh_sheet) and rh_sheet[i].vice != 0):
        sum = 0
        j = 0
        while i + j < len(rh_sheet) and rh_sheet[i+j].vice != 0:
            sum += rh_sheet[i+j].beat
            if(j >= 1):
                if rh_sheet[i+j].vice == -1:
                    rh_sheet.remove(rh_sheet[i+j])
                else:
                    j += 1
            else:
                j += 1
        rh_sheet[i].beat = rh_sheet[i].beat + sum
        i += 1
    return lh_sheet, rh_sheet

def beat_LUT(beat):
    ##임시로##
    if(beat > 16):
        beat = 16
    ##########
    LUT = [[0], [1], [2], [3], [4], [4, 1], [6], [6, 1], [8], [8, 1], [8, 2], [8, 3], [12], [12, 1], [12, 2], [12, 3], [16]]
    return LUT[beat]

def translate_beat(lh_sheet, rh_sheet):#12345678910
    note_temp = namedtuple("note", "pitch time velocity")
    tie = AC.accord()
    tie.vice = -2
    beat_table = ['', '16', '8', '8.', '4', '', '4.', '', '2', '', '', '', '2.', '', '', '', '1']
    i = 0
    while(i < len(lh_sheet)):
        beat = beat_LUT(lh_sheet[i].beat)
        lh_sheet[i].beat = beat[0]
        if len(beat) == 2:
            temp_accord = AC.accord()
            for j in range (0, len(lh_sheet[i].notes)):
                temp_accord.notes.append(note_temp(lh_sheet[i].notes[j].pitch, 0, lh_sheet[i].notes[j].velocity))
            temp_accord.vice = lh_sheet[i].vice
            temp_accord.beat = beat[1]
            lh_sheet.insert((i+1), tie)
            lh_sheet.insert((i+2), temp_accord)
            i += 2
        i += 1
        
    i = 0
    while(i < len(rh_sheet)):
        beat = beat_LUT(rh_sheet[i].beat)
        rh_sheet[i].beat = beat[0] 
        if len(beat) == 2:
            temp_accord = AC.accord()
            for j in range(0, len(rh_sheet[i].notes)):
                temp_accord.notes.append(note_temp(rh_sheet[i].notes[j].pitch, 0, rh_sheet[i].notes[j].velocity))
            temp_accord.vice = rh_sheet[i].vice
            temp_accord.beat = beat[1]
            rh_sheet.insert((i+1), tie)
            rh_sheet.insert((i+2), temp_accord)
            i += 2
        i += 1

    for accord in lh_sheet:
        if accord.vice == 0 or accord.vice==-1:
            accord.beat = beat_table[int(accord.beat)]

    for accord in rh_sheet:
        if accord.vice == 0 or accord.vice==-1:
            accord.beat = beat_table[int(accord.beat)]
    return lh_sheet, rh_sheet

def divide_beat(accords, bar):
    bar = bar * 4
    note_temp = namedtuple("note", "pitch time velocity")
    tie = AC.accord()
    tie.vice = -2
    beat_sum = 0
    i = 0
    while(i < len(accords)):
        if accords[i].vice == 0:
            if beat_sum // bar == (beat_sum + accords[i].beat - 1) // bar:
                beat_sum += accords[i].beat
                i += 1
            else:
                bar_diff = (beat_sum + accords[i].beat) // bar - beat_sum // bar
                over = AC.accord()
                backward_beat = (beat_sum + accords[i].beat) % bar
                if bar_diff == 1:
                    forward_beat = accords[i].beat - backward_beat
                    beat_sum += accords[i].beat
                    accords[i].beat = forward_beat
                    over.notes = accords[i].notes
                    over.beat = backward_beat
                    accords.insert(i+1, tie)
                    accords.insert(i+2, over)
                    i += 3
                else:
                    forward_beat = (accords[i].beat - backward_beat) % bar
                    beat_sum += accords[i].beat
                    accords[i].beat = forward_beat
                    j = 0
                    while j < bar_diff:
                        over = AC.accord()
                        over.notes = accords[i].notes
                        if not j == bar_diff - 1:
                            over.beat = bar
                            accords.insert(i + j * 2 + 1, tie)
                            accords.insert(i + j * 2 + 2, over)
                        else:
                            over.beat = backward_beat
                            accords.insert(i + j * 2 + 1, tie)
                            accords.insert(i + j * 2 + 2, over)
                        j += 1
                    i += j * 2 + 3

        elif accords[i].vice == -1:
            j = 0
            while i + j < len(accords) and accords[i+j].vice == -1:
                if beat_sum // bar == (beat_sum + accords[i].beat - 1) // bar:
                    beat_sum += accords[i].beat
                    i += 1
                else:
                    bar_diff = (beat_sum + accords[i].beat) // bar - beat_sum // bar
                    over = AC.accord()
                    backward_beat = (beat_sum + accords[i].beat) % bar
                    if bar_diff == 1:
                        forward_beat = accords[i].beat - backward_beat
                        beat_sum += accords[i].beat
                        accords[i].beat = forward_beat
                        over.notes = accords[i].notes
                        over.beat = backward_beat
                        accords.insert(i+1, over)
                        i += 2
                    else:
                        if (accords[i].beat - backward_beat) % bar == 0:
                            forward_beat = bar
                        else:
                            forward_beat = (accords[i].beat - backward_beat) % bar
                        beat_sum += accords[i].beat
                        accords[i].beat = forward_beat
                        j = 0
                        while j < bar_diff:
                            over = AC.accord()
                            over.vice = -1
                            over.notes = accords[i].notes
                            if not j == bar_diff - 1:
                                over.beat = bar
                                accords.insert(i + j + 1, over)
                            else:
                                over.beat = backward_beat
                                accords.insert(i + j + 1, over)
                            j += 1
                        i += j + 2

        else:
            i += 1

    return accords
    

def get_body(accords, minor):
    body = ""
    for i in range(len(accords)):
        accord = accords[i]
        if accord.vice != 0:
            body += vice_to_string(accord)
        else:
            body += accord_to_string(accord, minor)
            if len(accord.notes)==0:
                print("함정발견")
    return body


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

def vice_to_string(accord):#############
    ret = ""
    if(accord.vice == -1):##rest
        ret += " r" + str(accord.beat)
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
    return ret

def accord_to_string(accord, minor):
    if len(accord.notes)>0:
        if accord.beat == -1:
            accord.beat = 16
        start = "\\relative {<"
        body = ""
        fin = ">" + str(accord.beat) + '} '

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
            for j in range(oc-last):##########
                body += "\'"
            for j in range(last-oc):
                body += ","
            body += " "
        
        return start + body + fin

    else:
        return ""

