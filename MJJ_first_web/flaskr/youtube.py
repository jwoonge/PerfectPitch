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


bp = Blueprint('youtube', __name__, url_prefix='/youtube')



@bp.route('/translate_youtube_link',methods=['GET','POST'])
def youtube_link() :


    if request.method == 'POST' :
      try:
        f = request.form['link']
        pdp = PitchDetection.pd_processor()
        username = request.form['name']
        filename_mid = username


        Valid = Sound_ds.sound(f, username)
        if Valid.valid:

          result = pdp.do(Valid)
          result.make_midi_beat(filename_mid)

          result.make_score(filename_mid)
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
      except :
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
    filename = 'static/assets/mid/' + user_name + '.mp3'
    response = make_response(send_file(filename,
                    # 다운받아지는 파일 이름.
                  as_attachment=True))
    return response
  except :
    return jsonify(massage='This is an incorrect YouTube link.'), 500
