import functools

from flask import (Blueprint , flash , g, redirect, render_template, request, session, url_for,send_file)
from werkzeug.security import check_password_hash,generate_password_hash
from werkzeug.utils import secure_filename
from . import soundfileproc


from flaskr.db import get_db

bp = Blueprint('upload', __name__, url_prefix='/upload')
@bp.route('/')
def toupload() :
  return render_template('upload/upload.html')

@bp.route('/upload',methods=['GET','POST'])
def upload_file() :

    if request.method == 'POST' :
      f = request.files['file']
      testname = f.filename
      if '.wav' in testname or '.mp3' in testname:
        f.save(secure_filename(f.filename))
        soundproc = soundfileproc.sound(f.filename)
        pcmvalue = str(soundproc.data)
        route = 'flaskr/'
        filename = 'pcmtxt.txt'
        file = open(route + filename, 'w')
        file.write(pcmvalue)
        file.close()
        return send_file(filename,
                       mimetype='text/txt',
                       attachment_filename='downloaded_pcm_txt_file_name.txt',# 다운받아지는 파일 이름.
                       as_attachment=True)
      else :
        return 'error'


@bp.route('/txt_pcm_file_download_with_file')
def txt_pcm_download_with_file():
    file_name = f"pcmtxt.txt"
    return send_file(file_name,
                     mimetype='text/txt',
                     attachment_filename='downloaded_pcm_txt_file_name.txt',# 다운받아지는 파일 이름.
                     as_attachment=True)
#send_file(filename, mimetype='text',attachment_filename='download pcm value.txt', as_attachment=True)