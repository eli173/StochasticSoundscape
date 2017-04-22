#!/usr/bin/python3
#
# Copyright © 2017 jared <jared@jared-devstation>
#

import math
import sys, os
import wave, struct
import numpy
import librosa
from PyTransitionMatrix.Markov import TransitionMatrix as tm
import settings

# This function performs the analysis of any given sound.
# Function can be modified as desired to analyze whatever
# feature is desired.
def sound_analyze(fname, mode):
    y, sr = librosa.load(fname) # load the temp file
    if mode == 'rolloff':
        feature = librosa.feature.spectral_rolloff(y=y, sr=sr)
        return math.floor(numpy.average(feature))
    elif mode == 'spectral_centroid':
        feature = librosa.feature.spectral_centroid(y=y, sr=sr)
        return math.floor(numpy.average(feature))
    elif mode == 'zero_crossing':
        ft = librosa.feature.zero_crossing_rate(y)
        return numpy.average(ft.transpose())

# This function uses Librosa's onset detection to find
# impulses in the sound, and returns an array of positions
# in frames
def pulse_detect(fname, mode):
    y, sr = librosa.load(fname)
    if mode == 'onset':
        array = librosa.onset.onset_detect(y, sr)
        return array
    elif mode == 'beat_track':
        array = librosa.beat.beat_track(y,sr)[1]
        return array

# Analyze a single sound file
# Return the file with the frequency data
def analyze(fname):
    # Current file is the one we are iterating over
    current_file = wave.open(fname, 'r')
    length = current_file.getnframes()
    prev_classifier = None
    hash_dict = {}

    TEMP_NAME = 'temp.wav'
    markov_data = tm(fname) # initialize markov object
    
    # Iterate over current file INTERVAL frames at a time
    pulse_loc = pulse_detect(fname, settings.PULSE_TYPE)
    prev_point = 0
    for i in range (0, len(pulse_loc)-1):
        pulse_point = pulse_loc[i] * 1024 # 512 default hop length * halved librosa sample rate
        read_length = pulse_point - prev_point
        sys.stdout.write('\r')
        sys.stdout.write('frame ' + str(i) + ' of ' + str(len(pulse_loc)))
        sys.stdout.flush()
        working = wave.open(TEMP_NAME, 'w') # open the temp file for writing
        working.setparams(current_file.getparams())
        working.setnframes(0)
        curr_data = current_file.readframes(read_length)
        working.writeframes(curr_data) # save the working frames to the temp file
        working.close()
        prev_point = pulse_point

        # Within current 10 frames, perform analysis + write to stochastic matrix
        # This is one of the parameters that can be changed
        classifier = sound_analyze(TEMP_NAME, settings.ANALYSIS_MODE)
        
        # write the transition if there is a previous number
        if prev_classifier:
            markov_data.add_transition(prev_classifier, classifier)

        prev_classifier = classifier

    os.remove(TEMP_NAME)
    return markov_data.save() # save the associated data for that file

# Generate data based on every file in the 'data' folder
def data_gen():
    markov_master = tm('master_data')
    for fname in os.listdir('./data'):
        if fname[len(fname)-4:len(fname)] == '.wav':
            curr_out_data = analyze(os.path.abspath('data/' + fname))
            markov_master.load_data(curr_out_data)

    markov_master.save()
    return markov_master # return the associated data in a markov object

# Load existing data
def load_existing():
    markov_master = tm()
    markov_master.load_data('master_data.mkv')
    return markov_master
