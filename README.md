---
# PerfectPitch  
Piano sound(wav, mp3, youtube links) to sheet music  

---  

## Authors
Team MJJ:  
*  jwoonge (511sjw@naver.com)  
*  jjiho (hana5837@naver.com)  
*  tlswn94 (jason-shin94@hanmail.net)  
  
This project was developed as Team MJJ's 2nd Capstone-Project, of Chung-Ang univ.  

---  


## Perpose  
PerfectPitch is a python-based software for  
"extract music sheet pdf file from .mp3, .wav, youtube links".  

---  

## Module Explaination  

### PitchDetectionModule  
This Module is divided into 4 parts :  
*  extract pcm datas from input(.mp3, .wav, youtube links)  
*  detect pitches from calculated spectrogram, and store the results as own data structure(score)  
*  do post-processing to make the output clean  
*  export datas as .pdf file format  
*  (measure the accuracy by own algorithm)  
  
You can find more detailed information & usage at ['PitchDetectionModule/ReadMe.md'](https://github.com/jwoonge/PerfectPitch/tree/master/PitchDetectModule)  
  

### MeasureAccuracyModule  
Because there is no known way to compare music and sheet music, we had to devise a reasonable way to evauate our project.  
The way to evauation is as follows:  
1. export the result of our project to wav file  
2. calculate the spectrogram from the wav file's pcm data  
3. compare two spectrogram (original sound's and result wav file's) by..  
 1. find onsets by frame energy's peaks  
 2. using DTW(Dynamic Time Wrapping), find best matches of two onsets  
  - the rate of sqrt((# of mathed onsets)/(# of union of onsets)) is treated as "beat accuracy"  
 3. the average of cosin similarities for every pairs of matched onsets is treated as "pitch accuracy"  
  - cosin similarity consider the difference of value, but sheet music does not consider accurate velocity so we doubled the score.  
4. beat accuracy * pitch accuracy will be final accuracy  

### MJJ_first_web  
MJJ First Web is a python and flask -based responsive web.  
*  flask for back-end implementation  
*  javascript/bootstrap for front-end  
*  jquery/ajax for asynchronous communication with client and server  
As Multi-user Access control is based on public IP, there can be a risk of conflect when using same public IP.  
  

---  


## Usages  

You can run PerfectPitch locally by
```
$ python PerfectPitch.py https://www.youtube.com/your?links  
$ python PerfectPitch.py https://www.youtube.com/your?links v
```
argument v means 'want to measure accuracy'  

if you want more information, please refer to  
['PitchDetectionModule/ReadMe.md'](https://github.com/jwoonge/PerfectPitch/tree/master/PitchDetectModule)  


---  


## Requirements  
open softwares  
*  [python==3.6](https://www.python.org/ftp/python/3.6.0/python-3.6.0-amd64.exe)  
*  [lilypond==2.20.0](https://lilypond.org/download/binaries/mingw/lilypond-2.20.0-1.mingw.exe)  
*  [ffmpeg==20200612](https://ffmpeg.zeranoe.com/builds/)  
 -  if you use our git's ffmpeg, you don't need to add the path to the env.var  

python library requirements  
*  click==7.1.2
*  dtw==1.4.0
*  Flask==1.1.2
*  itsdangerous==1.1.0
*  Jinja2==2.11.2
*  MarkupSafe==1.1.1
*  mido==1.2.9
*  numpy==1.18.5
*  pretty-midi==0.2.9
*  pydub==0.24.1
*  scipy==1.4.1
*  six==1.15.0
*  Werkzeug==1.0.1
*  youtube-dl==2020.6.6

---  

