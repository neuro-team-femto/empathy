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

def generate_trial_files(subject_number=1,actor_number=1,n_blocks=1,n_trials=100, practice=False):
# generates n_block trial files per subject
# each block contains n_trials trials, randomized from folder which name is inferred from subject_number
# returns an array of n_block file names
    seed = time.getTime()
    random.seed(seed)
    stim_folder = "stims/Actor"+str(actor_number)
    stim_files = ["Actor"+str(actor_number)+"/"+os.path.basename(x) for x in glob.glob(stim_folder+"/*.jpg")]
    random.shuffle(stim_files)
    first_half = stim_files[:int(len(stim_files)/2)]
    second_half = stim_files[int(len(stim_files)/2):]
    # trials consist of two random files, one from the first half, and one from the second half of the stimulus list
    # write trials by blocks of n_trials
    block_count = 0 # was: subject_number, for unknown reason
    trial_files = []
    for block_stims in enblock(list(zip(first_half, second_half)),n_trials):
        trial_file = 'trials/trials_subj' + str(subject_number) + '_actor' + str(actor_number)+ '_' \
                                          + ('PRACTICE' if practice else str(block_count))\
                                          + '_' + date.strftime('%y%m%d_%H.%M')+'.csv'
        print ("generate trial file "+trial_file)
        trial_files.append(trial_file)
        with open(trial_file, 'w+') as file :
            # each trial is stored as a row in a csv file, with format: stimA, stimB
            # write header
            writer = csv.writer(file)
            writer.writerow(["StimA","StimB"])
            # write each trial in block
            for trial_stims in block_stims:
                writer.writerow(trial_stims)
        # break when enough blocks
        block_count += 1
        if block_count >= n_blocks:
            break
    return trial_files

def read_trials(trial_file):
# read all trials in a block of trial, stored as a CSV trial file
    with open(trial_file, 'r') as fid:
        reader = csv.reader(fid)
        trials = list(reader)
    return trials[1::] #trim header


def generate_result_file(subject_number):

    result_file = os.path.dirname(__file__)+'/results/results_Subj'+str(subject_number)+'_'+date.strftime('%y%m%d_%H.%M')+'.csv'
    # results are stored one line per anchor point for each stim in each trial, i.e. a trial is stored in 23 lines (23 points) x true-response + 23 x false-response
    result_headers = ['subj','trial','block','practice', 'sex','age','date','actor','stim','stim_order','point','x','y','response','rt']

    with open(result_file, 'w+') as file:
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

def update_trial_gui():
    for response_label in response_labels: response_label.draw()
    for response_checkbox in response_checkboxes: response_checkbox.draw()
    win.flip()

def get_neutral_info(actor_number, folder):
# read stimulus information stored in same folder as file_name, with a .txt extension
# returns a list of values
#     info_file_name = os.path.join(folder, os.path.splitext(os.path.basename(file_name))[0]+'.txt')
    info_file_name = os.path.join(folder+'/Actor'+str(actor_number),'neutral.txt')
    info = []
    with open(info_file_name,'r') as file:
        reader = csv.reader(file)
        for row in reader:
            info.append(float(row[0]))
    x = info[0::2]
    y = info[1::2]
    return x,y

def get_stim_info(file_name, folder):
# read stimulus information stored in same folder as file_name, with a .txt extension
# returns a list of values, as well as actor_number parsed from file_name 
# file_name is format Actor1/2.jpg. 
# parse actor number from file_name
    actor_number = int(os.path.dirname(file_name)[5:])
    info_file_name = os.path.join(folder, os.path.splitext(file_name)[0]+'.txt')
    info = []
    with open(info_file_name,'r') as file:
        reader = csv.reader(file)
        for row in reader:
            info.append(float(row[0]))
    # info is a list of x1,y1,x2,y2, etc...
    # reformat as a list of x and a list of y, aligned
    x = info[0::2]
    y = info[1::2]
    return x,y, actor_number

def get_false_feedback(min,max):
# returns a random percentage (int) between min and max percent
# min, max: integers between 0 and 100
    return int(100*random.uniform(float(min)/100, float(max)/100))


icon_path = os.path.dirname(__file__)+'/icons/' # path for image icons used for GUI
stim_path = os.path.dirname(__file__)+'/stims/' # path for image stims

# get participant nr, age, sex
# NOTE definition: subject = participant; actor= person whose photograph is used as stimulus
subject_info = {u'Number':1, u'Age':20, u'Sex': u'f/m'}
dlg = gui.DlgFromDict(subject_info, title=u'REVCOR')
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
screen_ratio = (float(win.size[1])/float(win.size[0]))

# Response GUI
response_options = ['[g] image 1', '[h] image 2']
response_keys = ['g', 'h']
label_size = 0.07
response_labels = []
response_checkboxes = []
reponse_ypos = -0.7
reponse_xpos = -0.6
label_spacing = abs(-0.8 - reponse_ypos)/(len(response_options)+1)
for index, response_option in enumerate(response_options):
    y = reponse_ypos - label_spacing * index
    response_labels.append(visual.TextStim(win, units = 'norm', text=response_option, alignHoriz='left', height=label_size, color='black', pos=(reponse_xpos,y-0.2)))
    response_checkboxes.append(visual.ImageStim(win, image=icon_path+'rb_off.png', size=(label_size*screen_ratio, label_size), units='norm', pos=(reponse_xpos-label_size, y-label_size*.05 -0.2)))
    reponse_xpos=reponse_xpos+1

# generate data files
POINTS = [137,138,139,140,141,53,54,55,56,64,70,67,73,45,46,17,20,23, 52,51,35,32,29] #index of the manipulated face points, listed in that order in stimulus info files
result_file = generate_result_file(subject_number)

# generate trial files: 1 practice block per actor, then (n_blocks + (repeat_last_block==True)?1:0) blocks of n_stims trials
n_actors = 2 # sampling from actors 1..n_actors
n_practice_blocks = n_actors # there are as many practice blocks as there are actors
n_practice_trials = 4 # nb of trials per practice block (i.e. per actor)
n_blocks = 7 # nb of trial blocks (possibly + 1, if repeat_last_block)
repeat_last_block = True # if true, block (n_blocks) and block (n_blocks+1) are the same
n_trials = 50  # per trial block

actors = range(1,n_actors+1) 
random.shuffle(actors) # actors stimuli are presented in consecutive blocks, actor order is randomized
practice_files = []
trial_files = []
for actor_number in actors:
    # practice trials for this actor
    actor_practice_file = generate_trial_files(subject_number, actor_number, n_blocks=1, n_trials=n_practice_trials, practice=True)
    practice_files = practice_files + actor_practice_file
    # trials for this actor  
    actor_trial_files = generate_trial_files(subject_number, actor_number, n_blocks,n_trials)
    if repeat_last_block:
        actor_trial_files.append(actor_trial_files[-1])
    trial_files = trial_files + actor_trial_files
trial_files = practice_files + trial_files #each file is a block; first n_practice_blocks blocks are practice blocks. 

show_text_and_wait(file_name="intro_1.txt")
show_text_and_wait(file_name="intro_2.txt")
show_text_and_wait(file_name="practice.txt") # instructions for the n_practice_blocks first blocks of stimuli

trial_count = 0
n_blocks = len(trial_files)
practice_block = True
    
for block_count, trial_file in enumerate(trial_files):

    # inform end of practice at the end of the initial practice blocks
    if block_count == n_practice_blocks :
        show_text_and_wait(file_name="end_practice.txt")
        practice_block = False

    block_trials = read_trials(trial_file)
    print block_trials
    for trial in block_trials :
        for checkbox in response_checkboxes:
            checkbox.setImage(icon_path+'rb_off.png')
        stim_1 = stim_path+'/'+trial[0]
        stim_2 = stim_path+'/'+trial[1]
        end_trial = False
        while (not end_trial):
            update_trial_gui()
            stim_1_image = visual.ImageStim(win, image= stim_1, units='norm', size = (1,1.7), pos=(-0.5,0.1))
            stim_2_image = visual.ImageStim(win, image= stim_2, units='norm', size = (1,1.7), pos=(0.5,0.1))
            stim_1_image.draw()
            stim_2_image.draw()
            response_start = time.getTime()
            update_trial_gui()
            # upon key response...
            response_key = event.waitKeys(keyList=response_keys)
            response_time = time.getTime() - response_start
            # select checkbox
            response_checkboxes[response_keys.index(response_key[0])].setImage(icon_path+'rb_on.png')
            update_trial_gui()
            # blank screen and end trial
            core.wait(0.3)
            win.flip()
            core.wait(0.2)
            end_trial = True

            # log response
            row = [subject_number, trial_count, block_count, practice_block, subject_sex, subject_age, date]
            if response_key == ['g']:
                response_choice = 0
            elif response_key == ['h']:
                response_choice = 1

            with open(result_file, 'a') as file :
                writer = csv.writer(file,lineterminator='\n')
                for stim_order,stim in enumerate(trial):
                    stim_x, stim_y,actor_number = get_stim_info(folder=stim_path, file_name=stim)
                    print stim_x
                    #neutral_xy= get_neutral_info(folder=stim_path, actor_number = actor_number)
                    for point_index,(x,y) in enumerate(zip(stim_x,stim_y)): #iterate all successive xi,xyi
                        result = row + [actor_number, stim, stim_order] \
                                     + [POINTS[point_index], x, y] \
                                     + [response_choice==stim_order, round(response_time,3)]
                        writer.writerow(result) #store a line for each x,y pair in the stim

        trial_count += 1
        print "block"+str(block_count)+": trial"+str(trial_count) + ' (practice: '+ str(practice_block)+')'


    # pause at the end of subsequent blocks
    if ((block_count >= n_practice_blocks) and (block_count < n_blocks-1)):
        show_text_and_wait(message = u"Vous avez complété " \
                                + str(Fraction(block_count-n_practice_blocks+1, n_blocks-n_practice_blocks)) \
                                + u" de l'expérience.\n Votre score sur cette partie de l'expérience est de " \
                                + str(get_false_feedback(70,85))\
                                + u"%.\n\n Vous pouvez faire une pause si vous le souhaitez, puis appuyer sur une touche pour continuer.")
        #show_text("pause1.txt")
        #core.wait(5)
       #show_text_and_wait("pause0.txt")


#End of experiment
show_text_and_wait("end.txt")

# Close Python
win.close()
core.quit()
sys.exit()
