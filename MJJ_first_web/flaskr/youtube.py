import functools

from flask import (Blueprint , flash , g, redirect, render_template, request, session, url_for)
from flask import send_file
from flask import make_response,jsonify
from werkzeug.security import check_password_hash,generate_password_hash
from werkzeug.utils import secure_filename
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
from PitchDetectModule import PitchDetection
from PitchDetectModule import Sound_ds
import time

bp = Blueprint('youtube', __name__, url_prefix='/youtube')



@bp.route('/translate_youtube_link',methods=['GET','POST'])
def youtube_link() :
    starttime= time.time()

    if request.method == 'POST' :
      try:
        f = request.form['link']
        pdp = PitchDetection.pd_processor()
        username = request.form['name']
        filename_mid = username


        Valid = Sound_ds.sound(f, username)
        if Valid.valid:

          result = pdp.do(Valid)

          result.make_score(filename_mid,title=Valid.title,author=Valid.author)
          endtime= time.time() - starttime

          starttesttime= time.time()
          result.make_wav(filename_mid)
          
          from PitchDetectModule import MeasureAccuracy          ###
          filename_wav = 'flaskr/static/assets/mid/' + filename_mid
          accuracy = MeasureAccuracy.measure_accuracy(pdp, filename_wav+'.wav', username=username)    ####
          print('ACC : ',round(accuracy,2))        ####

          testendtime=time.time()-starttesttime
          testing = open(username+'.txt','a',encoding="utf-8")
          testing.write(Valid.title+' '+ Valid.author+' '+str(Valid.time) +' '+ str(round(endtime,2)) +' '+ str(round(testendtime,2)) +' '+ str(round(accuracy,2))+'\n')
          filename_mid = 'static/assets/pdf/' + filename_mid

          '''
          return send_file('../'+filename_mid,
                            # 다운받아지는 파일 이름.
                          as_attachment=True)
          '''
          #filename_mid='test.pdf'
          response = make_response(send_file(filename_mid+'.pdf',
                            # 다운받아지는 파일 이름.
                          as_attachment=True))

          return response
        else:
          return jsonify(massage='This is an incorrect YouTube link.'), 500
      except Exception as e :
        print(e)
        return jsonify(massage='This is an incorrect YouTube link.'), 500
    else :
      return jsonify(massage='This is an incorrect YouTube link.'), 500


      
      #return redirect(url_for('youtube.download_pitch',filename=filename_mid))
      
     


@bp.route('/showpdf',methods=['GET','POST'])
def show_pdf() :
  try :
    user_name = str(request.form['name'])
    filename = 'static/assets/pdf/'+user_name+'.pdf'

    response = make_response(send_file(filename,
                    # 다운받아지는 파일 이름.
                  as_attachment=True))
    return response
  except :
    return jsonify(massage='This is an incorrect YouTube link.'), 500


@bp.route('/playaudio',methods=['GET','POST'])
def play_audio() :
  try :
    user_name = str(request.form['name'])
    filename = 'static/assets/mid/' + user_name + '.wav'
    response = make_response(send_file(filename,
                    # 다운받아지는 파일 이름.
                  as_attachment=True))
    return response
  except :
    return jsonify(massage='This is an incorrect YouTube link.'), 500
