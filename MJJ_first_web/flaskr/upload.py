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

bp = Blueprint('upload', __name__, url_prefix='/upload')

@bp.route('/upload',methods=['GET','POST'])
def upload_file() :

    if request.method == 'POST' :
      f = request.files['file']
      username = str(request.form['name'])
      testname = f.filename
      filename_mid = username
      if '.wav' in testname or '.mp3' in testname:
        f.save(secure_filename(f.filename))
        try :
          pdp = PitchDetection.pd_processor()
          result = pdp.do(Sound_ds.sound(f.filename))
          result.make_midi_beat(filename_mid)
          result.make_score(filename_mid)
          filename_mid = 'static/assets/pdf/' + filename_mid

          response = make_response(send_file(filename_mid+'.pdf',
                    # 다운받아지는 파일 이름.
                  as_attachment=True))
        except :
          return jsonify(massage='Incorrect File Format'),500

        return response
      else :
        return jsonify(massage='Incorrect File Format'),500
    else :
      return jsonify(massage='Incorrect File Format'), 500


@bp.route('/showpdf',methods=['GET','POST'])
def show_pdf() :
  try :
    user_name = str(request.form['name'])
    print('##############################')
    print(user_name)
    print('############################')
    filename = 'static/assets/pdf/'+user_name+'.pdf'
    response = make_response(send_file(filename,
                    # 다운받아지는 파일 이름.
                  as_attachment=True))
    return response
  except :
    return jsonify(massage='Incorrect File Format'), 500

@bp.route('/playaudio',methods=['GET','POST'])
def play_audio() :
  try :
    user_name = str(request.form['name'])
    filename = 'static/assets/audio/' + user_name + '.mp3'
    print("여기왓다")
    #filename = 'static/assets/audio/' + '2109625371' + '.mp3'
    response = make_response(send_file(filename,
                    # 다운받아지는 파일 이름.
                  as_attachment=True))
    return response
  except :
    return jsonify(massage='Incorrect File Format'), 500