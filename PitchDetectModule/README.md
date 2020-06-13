
--- 

# PitchDetectionModule  

---  

## Sound_ds.py  
### summary
this file defines the 'sound' class which is a data structure for storing pcm data  
### usage
create 'sound' class object by constructor with parameter 'filename' as file path or youtube link.  
```python
mysound = sound('file/or/youtube/links')
```
  
you can extract pcm data by
```python
pcm = mysound.data
sample_rate = mysound.sample_rate
```
  
if your data was from youtube link, you can extract the title and uploader by
```python
title = mysound.title
uploader = mysound.author
```
  
---  
  
## PitchDetection.py  
### summary
Detailed process is as follows:  
1. calculate spectogram from sound.pcm using scipy.signal.stft  
 - get_spectrogram() #line 229  
2. tune the frequencies rate of (expected frequency/max value frequency)  
 - get_tuning_rate() #line 243  
3. compact the spectrogram : frame*frequency to pitch*frequency  
 - #line 251  
4. find approximated GCD of Onset frames and make metronome  
 - approximated GCD is  
   $gcd(\text{diff}) := minimize_x(\sum_{i=0}^{len(\text{diff})}((\text{diff}_i/x)-round(\text{diff}_i/x)))$  
 - get_interval() #line 104 in detect_pitch()  
5. find valid peaks which meet 'metronome is in range peak start-end  
 - #line 154 in detect_pitch()  
6. decrease octave with appropriate coefficient  
 - octave_decrease() #line 203 in detect_pitch()  
7. create score class as a result  
 - automatically created 'pd_processor.result' whitch is score class object  
  
### usage  
You can detect pitch by creating 'pd_processor' object and calling do() function with parameter 'sound' object
```python
pdp = pd_processor()
result = pdp.do(mysound)
```
result is the object of 'score' class

---  


## Score_ds.py
### summury  
this file defines the 'score' class and its subclass 'accord_ds' and 'note'.  
*  'score' class includes a set of 'accord_ds'  
*  'accord_ds' class includes a set of 'note'  
*  'note' class is represent one note of sheet music.  

'score' class is used as the result of pitch detection process.  
It has many functions for post-processing  
Details of post-processing is as follows:  
1. mark the beat of each accords using 'interval'  
 - mark_beat() #line 338  
2. find music symbols  
 - mark_symboles() #line 94  
3. separate datas into left-hand & right-hand  
 - divide_hands() #line 263
4. detect key of sheet music which minimize the number of accidentals  
 - detect_key() #line 209  

### usage  
there are some callable functions to export results as file  
  - make_score(filename, title, author) : translate self to pdf file using lilypond  
  - make_wav(filename) : create wav file based frequencies translated from each note's pitch  
  - make_midi(filename) : not used in latest version  
  - make_midi_beat(filename) : not used in latest version  

You can translate score object to files by  
```python
result.make_score('output_pdf', title='PerfectPitch', author='team MJJ')
result.make_wav('output_wav')
```  

---  

## LilyNotation.py  
### summury
this file defines functions which convert 'score' class into "Lilypond"-syntax-string.  
Details of converting process is as follows:  
1. merge rests to look clean  
 - merge_rests() #line 257  
2. divide beat of pitches which are over the bar  
 - divide_beat() #line 148  
3. translate accord.beat into beats suitable for sheet music  
 - for example, sheet music represent 5 beats as (4 + 1) beats  
 - translate_beat() #line 279
4. convert the whole part of datas into lilypond string  
 - lily_notation() #line 6  
 - get_body() #line 37, in lily_notation()

---  
