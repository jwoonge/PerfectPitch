from collections import namedtuple
def DivideHands(Notes):
    sorted_notes = sorted(Notes, key = "start")
    note_temp = namedtuple("note", "pitch start beat velocity vice")
    temp_s = note_temp(0, 0, 0, 0, 0)
    a = [temp_s]
    
    rh_sheet = [a]
    lh_sheet = [a]

    for note in sorted_notes:
        if note.pitch > 50:
            if note.start == rh_sheet[-1][0].start:
                temp = rh_sheet[-1]
                del rh_sheet[-1]
                temp.append(note)
                rh_sheet.append(temp)
            else:
                a = [note]
                rh_sheet.append(a)
        elif note.pitch > 0:
            if note.start == lh_sheet[-1][0].start:
                temp = lh_sheet[-1]
                del lh_sheet[-1]
                temp.append(note)
                lh_sheet.append(temp)
            else:
                a = [note]
                lh_sheet.append(a)
        #elif note.pitch == :#쉼표, 악상기호 정의채

    del rh_sheet[0]
    del lh_sheet[0]


def LilyNotation(lh_sheet, rh_sheet, bar, filename):
    ret = "\\version \"2.20.0\"\n\\header{\n  title = \"" + filename + "\"\n}"
    RH_head = "lhMusic = \\relative c\' {"
    LH_head = "lhMusic = \\relative c\' {"
    RH_body = ""
    LH_body = ""
    fin = "\n}"
    for accord in rh_sheet:#오른손 악보정보
        Accord_to_String_r(accord)

    for accord in lh_sheet:#왼손 악보정보
        Accord_to_String_l(accord)

    score_data = "\n\\score {\n  \\new PianoStaff <<\n    \\new Staff = \"RH\"  <<\n      \\key g \\minor\n      \\rhMusic\n    >>\n    \\new Staff = \"LH\" <<\n      \\key g \\minor\n      \\clef \"bass\"\n      \\lhMusic\n    >>\n  >>\n}"
    ret += "\n" + RH_head + RH_body + fin + LH_head + LH_body + fin + score_data
    print(ret)
    return ret
        
def DivideBeat(accord, bar):
    note_temp = namedtuple("note", "pitch start beat velocity vice")
    note_tf = []
    for note in accord:
        note_tf.append(note.start // bar == (note.start + note.beat - 1) // bar)
    if all(note_tf):
        pass
        #고대로 냅둠
    else:
        over = []
        for note in accord:
            if not note.start // bar == (note.start + note.beat - 1) // bar:
                forward_beat = note.beat - (note.start+note.beat)%bar
                backward_beat = note.beat - forward_beat
                backward_start = note.start + note.beat - (note.start + note.beat) % bar
                accord.remove(note)
                accord.append(note_temp(note.pitch, note.start, forward_beat, note.velocity, note.vice))#note.vice에 연음줄 시작정보
                over.append(note_temp(note.pitch, backward_start, backward_beat, note.velocity, note.vice))#note.vice에 연음줄 끝 정보
        #class에 있는 악보객체에 accord와 over을 accord 대신에 삽입

def TranslateBeat(accord, bar):
    for note in accord:
        note.beat = bar / beat #bar = 한 마디에 들어가는 박자 / beat는 박자를 음표로 환산한 것이 되야 함

def Accord_to_String_r(accord, pre, bar):#뭐부터처리해야할까...? prin
    ret = print_accord_0(accord, pre, bar)
    if any(accord.vice == 1):
        ret += "( "
    if any(accord.vice == 2):
        ret += ") "
    if any(accord.vice == 3):
        ret += "\\< "
    if any(accord.vice == 4):
        ret += "\\> "
    if any(accord.vice == 5):
        ret += "\\! "
    if any(accord.vice == 6):
        ret += "\\accel "
    if any(accord.vice == 7):
        ret += "\\rit "


    #RH_body에 ret를 더함 

def Accord_to_String_l(accord):


def LUT(pitch_num):
    gye = (pitch_num-3)%12
    oc = int((pitch_num-3)/12)
    gyeLUT = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    gye = gyeLUT[gye]
    return gye, oc


def print_accord_0(accord, latest, bar):#latest : 직전 accord의 가장 마지막에 작성된 노트
    start = "<"
    fin = ">"
    body = ""
    last = latest
    for i in range(len(accord)):
        note = accord[i]
        gye, oc = LUT(note.pitch)
        gye_, oc_ LUT(last.pitch)

        body += gye + str(note.beat)###################################### 서순 주의
        if oc - oc_ > 6:
            for i in range(oc - oc_ // 12):
                body += "\'"
        elif oc_ - oc > 6:
            for i in range(oc_ - oc // 12):
                body += ","
        last = accord[i]

    return start + body + fin, accord[-1]


import csv
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
                    self.sample_rate = float(row[1])
                    i+=1
                else :
                    temp=[]
                    temp = namedtuple('notes',['pitch','start','end','velocity'])
                    temp.pitch = int(row[0])
                    temp.start = int(row[1])
                    temp.end = int(row[2])
                    temp.velocity = int(row[3])
                    self.note_stack.append(temp)

note_temp = namedtuple("note", "pitch start beat velocity")
temp_s = note_temp(1, 1, 1, 1)
a = [note_temp(1, 6, 2, 1), note_temp(3, 6, 2, 1), note_temp(5, 6, 2, 1), note_temp(7, 6, 4, 1)]
DivideBeat(a, 4)
'''
notice : 
        1. 처음에 들어가는 박자는 변환되지 않은 박자(ex 1박 = 1, 2박 = 2)
        2. note = namedtuple("note", "pitch start beat velocity vice") / vice: 악상기호
        3. vice :
                    0. 기본 음표. 악상기호가 없는 자리
                    1. 연음줄(이음줄)이 시작하는 음표
                    2. 연음줄(이음줄)이 끝나는 음표
                    3. crec 시작
                    4. decrec 시작 
                    5. crec, decrec 끝
                    6. 빠르게 accelerando
                    7. 느리게 ritardando
                    -----
                    8. octave 올리는거 시작
                    9. octave 끝
                    10. 물결표시
                    ------
                    이음줄이랑 연음줄을 따로처리해야하나?

        4. score 클래스엔 왼손이랑 오른손 악보정보를 따로 저장해 둘 수 있는 RH_score와 LH_score를 관리


서순 :
        전체 화음 찾기
        새로만드는 tempo synchro
        1. 왼손 오른손 나누기
        2. 각각에 대해 divide beat를 돌리고
        3. 각각에 대해 translatebeat를 돌리고
        5. 마지막에 lilynotation을 돌려라
'''