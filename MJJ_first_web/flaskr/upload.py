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
from PitchDetectModule import Score_ds
import zipfile


from flaskr.db import get_db

bp = Blueprint('upload', __name__, url_prefix='/upload')
@bp.route('/')
def toupload() :
  return render_template('upload/upload.html')

@bp.route('/upload',methods=['GET','POST'])
def upload_file() :

    if request.method == 'POST' :
      f = request.files['file']
      username = str(request.form['name'])
      testname = f.filename
      filename_mid = username
      print(testname)
      if '.wav' in testname or '.mp3' in testname:
        f.save(secure_filename(f.filename))
        pdp = PitchDetection.pd_processor()
        result = pdp.do(Sound_ds.sound(f.filename))
        result.make_midi_beat(filename_mid)
        result.make_score(filename_mid)


        response = make_response(send_file('../'+filename_mid+'.mid',
                  # 다운받아지는 파일 이름.
                as_attachment=True))

        return response
      else :
        return jsonify(massage='Incorrect File Format'),500


@bp.route('/txt_pcm_file_download_with_file')
def txt_pcm_download_with_file():
    file_name = f"pcmtxt.txt"
    return send_file(file_name,
                     mimetype='text/txt',
                     attachment_filename='downloaded_pcm_txt_file_name.txt',# 다운받아지는 파일 이름.
                     as_attachment=True)
#send_file(filename, mimetype='text',attachment_filename='download pcm value.txt', as_attachment=True)

@bp.route('/showpdf',methods=['GET','POST'])
def show_pdf() :
  user_name = str(request.form['name'])
  print('##############################')
  print(user_name)
  print('############################')
  filename = 'static/assets/pdf/'+user_name+'.pdf'
  response = make_response(send_file(filename,
                  # 다운받아지는 파일 이름.
                as_attachment=True))
  return response