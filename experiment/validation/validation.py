# coding=utf-8
import time
import sys
import os
import glob
import csv
import codecs
import datetime
import random
from psychopy import prefs
prefs.general['audioLib'] = ['pyo']
from psychopy import visual,event,core,gui,monitors
from fractions import Fraction
# import pyaudio
# import wave
# import cleese
# import scipy.io.wavfile as wav
import numpy as np
from math import sqrt

def enblock(x, n_stims):
    # generator to cut a list of stims into blocks of n_stims
    # returns all complete blocks
    for i in range(len(x)//n_stims):
        start = n_stims*i
        end = n_stims*(i+1)
        yield x[start:end]

def generate_trial_file(subject_number=1,n_actors=6,n_trials=1000, practice=False):
# generates one trial file 
# containing all files from stim folder, in random order
# returns one file name
    seed = time.getTime()
    random.seed(seed)

    trial_file = 'trials/trials_subj' + str(subject_number) + '_' + ('PRACTICE_' if practice else '') + date.strftime('%y%m%d_%H.%M')+'.csv'
    print ("generate trial file "+trial_file)

    # create list of trials, consisting of one neutral file, and one random file from each actor's stim_files
    trials = []
    actors = list(range(1,n_actors+1))
    for actor_number in actors:
        stim_folder = "stims/Actor"+str(actor_number)
        stim_files = ["Actor"+str(actor_number)+"/"+os.path.basename(x) for x in glob.glob(stim_folder+"/*.jpg")]
        neutral_file = ["Actor"+str(actor_number)+"/neutral/Actor"+str(actor_number)+"_neutral.jpg"]
        actor_trials = list(zip(neutral_file*len(stim_files), stim_files))
        trials = trials + actor_trials
    # randomize across actors
    random.shuffle(trials)

    # write trials in trial_file, max n_trials
    trial_count = 0
    with open(trial_file, 'wb+') as file :
            # each trial is stored as a row in a csv file, with format: stimA, stimB
            # write header
            writer = csv.writer(file)
            writer.writerow(["StimA", "StimB"])
            # write each trial in block
            for trial in trials:
                writer.writerow(trial)
                # break when enough trials
                trial_count += 1
                if trial_count >= n_trials:
                    break
    
    return trial_file

def read_trials(trial_file):
# read all trials in a block of trial, stored as a CSV trial file
    with open(trial_file, 'r') as fid:
        reader = csv.reader(fid)
        trials = list(reader)
    return trials[1::] #trim header


def generate_result_file(subject_number):

    result_file = 'results/results_Subj'+str(subject_number)+'_'+date.strftime('%y%m%d_%H.%M')+'.csv'
    # results are stored one line per anchor point for each stim in each trial, i.e. a trial is stored in 23 lines (23 points) x true-response + 23 x false-response
    result_headers = ['subj','trial', 'block', 'sex','age','date','actor','kernel_subj','neutral','stim','response','rt']

    with open(result_file, 'wb+') as file:
        writer = csv.writer(file)
        writer.writerow(result_headers)
    return result_file

def show_text_and_wait(file_name = None, message = None):
    event.clearEvents()
    if message is None:
        with codecs.open (file_name, "r", "utf-8") as file :
            message = file.read()
    text_object = visual.TextStim(win, text = message, color = 'black')
    text_object.height = 0.05
    text_object.draw()
    win.flip()
    while True :
        if len(event.getKeys()) > 0:
            core.wait(0.2)
            break
        event.clearEvents()
        core.wait(0.2)
        text_object.draw()
        win.flip()

def get_stim_info(file_name):
# read stimulus information, by parsing the file_name
# file_name is format Actor1/Actor1_Subject2.jpg.
# parse actor number from file_name
    actor_number = int(os.path.dirname(file_name)[5:])
    name = os.path.splitext(os.path.basename(file_name))[0]
    kernel_subject_number = int(name.split('_')[1][7:])
    return actor_number, kernel_subject_number

def get_false_feedback(min,max):
# returns a random percentage (int) between min and max percent
# min, max: integers between 0 and 100
    return int(100*random.uniform(float(min)/100, float(max)/100))

icon_path = os.path.dirname(__file__)+'/icons/' # path for image icons used for GUI
stim_path = os.path.dirname(__file__)+'/stims/' # path for image stims

# get participant nr, age, sex
# NOTE definition: subject = participant; actor= person whose photograph is used as stimulus
subject_info = {u'Number':1, u'Age':20, u'Sex': u'f/m'}
dlg = gui.DlgFromDict(subject_info, title=u'VALIDATION')
if dlg.OK:
    subject_number = subject_info[u'Number']
    subject_age = subject_info[u'Age']
    subject_sex = subject_info[u'Sex']
else:
    core.quit() #the user hit cancel so exit
date = datetime.datetime.now()
time = core.Clock()

# Monitor
widthPix = 1920 # screen width in px
heightPix = 1080 # screen height in px
monitorwidth = 53.1 # monitor width in cm
viewdist = 60. # viewing distance in cm
monitorname = 'iiyama'
scrn = 0 # 0 to use main screen, 1 to use external screen
mon = monitors.Monitor(monitorname, width=monitorwidth, distance=viewdist)
mon.setSizePix((widthPix, heightPix))
mon.saveMon()
win = visual.Window([1366, 768], fullscr=False, color="lightgray", units='norm', monitor=mon)
#screen_ratio = (float(win.size[1])/float(win.size[0]))

# generate data files
result_file = generate_result_file(subject_number)

# generate trial files: 1 practice block per actor, then n_blocks blocks of n_stims trials
n_actors = 6 #sampling from actors 1..n_actors
n_practice_trials = 4
n_practice_blocks = 1
practice_file = generate_trial_file(subject_number, n_actors, n_practice_trials, practice=True)
trial_file = generate_trial_file(subject_number, n_actors)
trial_files = [practice_file, trial_file] 

show_text_and_wait(file_name="intro_1.txt")
show_text_and_wait(file_name="intro_2.txt")
show_text_and_wait(file_name="practice.txt") # instructions for the n_practice_blocks first blocks of stimuli

trial_count = 0
n_blocks = len(trial_files)
practice_block = True

for block_count, trial_file in enumerate(trial_files):

    print (block_count)

    # inform end of practice at the end of the initial practice blocks
    if block_count == n_practice_blocks :
        show_text_and_wait(file_name="end_practice.txt")
        practice_block = False

    trials = read_trials(trial_file)

    for trial in trials :

        stim_1 = stim_path+'/'+trial[0]
        stim_2 = stim_path+'/'+trial[1]

        stim_1_image = visual.ImageStim(win, image= stim_1, units='norm', size = (0.66,1), pos=(-0.5,0.4))
        stim_2_image = visual.ImageStim(win, image= stim_2, units='norm', size = (0.66,1), pos=(0.5,0.4))
        
        scale=visual.RatingScale(win, low=1, high=9, labels=(u'Beaucoup \n moins amical',u'Pareil', u'Beaucoup \n plus amical'), textColor='black', lineColor='black'
                                , marker='triangle', markerColor='SkyBlue',  markerStart=5
                                , leftKeys='left', rightKeys='right', noMouse=True, pos = (0.0, -0.5)
                                , precision = 1, size = 1.2, stretch = 2, scale=u"Par rapport au visage de gauche, le visage de droite est-il ... ?"
                                , respKeys=(['1','2','3','4','5','6','7','8','9'])  # Or ['num_1','num_2','num_3','num_4','num_5','num_6','num_7','num_8','num_9']
                                , acceptKeys=(['return','space','num_enter']), skipKeys=None
                                , acceptPreText='Choisissez', acceptText='Valider', acceptSize=1
                                , showValue=True)    

        while scale.noResponse:
            stim_1_image.draw()
            stim_2_image.draw()
            scale.draw()
            win.flip()
        response = scale.getRating()
        response_time = scale.getRT()

        # blank screen and end trial
        core.wait(0.3)
        win.flip()
        core.wait(0.2)
       
        # log response
        [actor_number, kernel_number] = get_stim_info(trial[1])           
        row = [subject_number, trial_count, block_count, subject_sex, subject_age, date, 
                actor_number, kernel_number,trial[0], trial[1], 
                response, round(response_time,3)]

        with open(result_file, 'a') as file :
            writer = csv.writer(file,lineterminator='\n')
            writer.writerow(row) #store a line for each x,y pair in the stim
                
        trial_count += 1
        # print ("block"+str(block_count)+": trial"+str(trial_count) + ' (practice: '+ str(practice_block)+')')


#End of experiment
show_text_and_wait("end.txt")

# Close Python
win.close()
core.quit()
sys.exit()
