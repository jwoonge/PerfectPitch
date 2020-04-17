import functools

from flask import (Blueprint , flash , g, redirect, render_template, request, session, url_for)
from flask import send_file
from werkzeug.security import check_password_hash,generate_password_hash
from werkzeug.utils import secure_filename
from . import soundfileproc

from flaskr.db import get_db

bp = Blueprint('youtube', __name__, url_prefix='/youtube')
@bp.route('/')
def toyoutube() :
  return render_template('Youtube/youtube.html')


@bp.route('/translate_youtube_link',methods=['GET','POST'])
def youtube_link() :


    if request.method == 'POST' :
      f = request.form['link']
      soundproc = soundfileproc.sound(f)
      pcmvalue = str(soundproc.data)
      route = 'flaskr/'
      filename = 'pcmtxt.txt'
      file = open(route + filename, 'w')
      file.write(pcmvalue)
      file.close()
      return send_file(filename,
                       mimetype='text/txt',
                       attachment_filename='downloaded_pcm_txt_file_name.txt',  # 다운받아지는 파일 이름.
                       as_attachment=True)


@bp.route('/txt_pcm_file_download_with_file')
def txt_pcm_download_with_file():
    file_name = f"pcmtxt.txt"
    return send_file(file_name,
                     mimetype='text/txt',
                     attachment_filename='downloaded_pcm_txt_file_name.txt',# 다운받아지는 파일 이름.
                     as_attachment=True)