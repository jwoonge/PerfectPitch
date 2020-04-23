import functools

from flask import (Blueprint , flash , g, redirect, render_template, request, session, url_for)
from flask import send_file
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

bp = Blueprint('youtube', __name__, url_prefix='/youtube')
@bp.route('/')
def toyoutube() :
  return render_template('Youtube/youtube.html')


@bp.route('/translate_youtube_link',methods=['GET','POST'])
def youtube_link() :


    if request.method == 'POST' :
      f = request.form['link']
      pdp = PitchDetection.pd_processor()

      filename_mid = '../output.mid'
      filename_txt = 'detected_pitch.txt'
      
      result = pdp.do(Sound_ds.sound(f))
      result.make_midi()
      file = open(filename_txt, 'w')
      file.write(result.str_pitches())
      file.close()
      output_zip = zipfile.ZipFile('output.zip', 'w')
      output_zip.write('output.mid', compress_type=zipfile.ZIP_DEFLATED)
      output_zip.write('detected_pitch.txt', compress_type=zipfile.ZIP_DEFLATED)


      return send_file('../output.zip',
                         # 다운받아지는 파일 이름.
                       as_attachment=True)
      
     

@bp.route('/download_pitch')
def download_pitch() :

    filename_txt = 'detected_pitch.txt'
    
    
    return send_file(filename_txt,
                         # 다운받아지는 파일 이름.
                       as_attachment=True)


@bp.route('/txt_pcm_file_download_with_file')
def txt_pcm_download_with_file():
    file_name = f"pcmtxt.txt"
    return send_file(file_name,
                     mimetype='text/txt',
                     attachment_filename='downloaded_pcm_txt_file_name.txt',# 다운받아지는 파일 이름.
                     as_attachment=True)