import sys
import os
import subprocess
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '\\MeasureAccuracyModule')
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + '\\PitchDetectModule')

from PitchDetectModule.PitchDetection import pd_processor
from PitchDetectModule.Sound_ds import sound
from PitchDetectModule.Score_ds import score
from MeasureAccuracyModule.MeasureAccuracy import measure_accuracy

path = os.getcwd()

if 'w' in sys.argv:
    
    #path = os.getcwd()
    print(os.getcwd())
    #os.system('cd {}'.format(os.getcwd()+'/MJJ_first_web'))

    #p=subprocess.Popen('cd MJJ_first_web',shell=True)

    os.chdir('Mjj_first_web')

    #subprocess.call(["set","FLASK_APP=flaskr"],shell=True)
    #subprocess.call(["flask","run"],shell=True)
    #os.popen('set FLASK_APP=flaskr')
    #os.popen('flask run')

    os.system('set FLASK_APP=flaskr')
    os.system('set FLASK_ENV=development')
    os.system('flask run')
    

else:
    file_name = ""
    for i in range(1,len(sys.argv)):
        if '.' in sys.argv[i] :
            file_name = sys.argv[i]
            break

    pdp = pd_processor()
    input_sound = sound(file_name)
    result = pdp.do(input_sound)
    result.make_score('result', test=True)
    result.make_midi('result')
    os.remove('result.ly')
    os.remove('result.log')

    if 'v' in sys.argv:
        result.make_wav('result', test=True)
        accuracy = measure_accuracy(pdp, 'result.wav')