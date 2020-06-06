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

bp = Blueprint('youtube', __name__, url_prefix='/youtube')
@bp.route('/')
def toyoutube() :
  return render_template('Youtube/youtube.html')


@bp.route('/translate_youtube_link',methods=['GET','POST'])
def youtube_link() :


    if request.method == 'POST' :
      f = request.form['link']
      pdp = PitchDetection.pd_processor()
      username = str(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
      username = username.replace('.','')
      filename_mid = username
      filename_txt = username + '_detected_pitch.txt'
      
      
      Valid = Sound_ds.sound(f, username)
      if Valid.valid:
        result = pdp.do(Valid)
        result.make_midi_beat(filename_mid)
        result.make_score(filename_mid)


        '''
        return send_file('../'+filename_mid,
                          # 다운받아지는 파일 이름.
                        as_attachment=True)
        '''
        #filename_mid='test.pdf'
        response = make_response(send_file('../'+filename_mid+'.mid',
                          # 다운받아지는 파일 이름.
                        as_attachment=True))
    
        return response
      
      else :
        print('에러났어씨발')
        return jsonify(massage='This is an incorrect YouTube link.'),500


      
      #return redirect(url_for('youtube.download_pitch',filename=filename_mid))
      
     

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


