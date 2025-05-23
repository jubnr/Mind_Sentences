#! /usr/bin/env python3

"""
Last update: 6th December 11:37 by JB

================================
Mind Sentences Experiment Script
================================

This script manages a MEG experiment designed to study language processing.
Participants listen to audio sentences during the white fixation cross and mentally 
repeat them when the fixation cross turns green. They have to click on the right blue
button at the beginning of the mental repetition and click again once finished to go
to the next sentence. The experiment measures the mental repetition time and allows 
participants to indicate if they can't remember a sentence by clicking on the right
red button. The sentence is stored in a list and replayed at the end of the experiment.

Key Features:
-------------
- Optional training phase (--training).
- Sentences filtered by subject and run.
- Response detection via buttons (right blue to indicate repetition start and end, right red to skip).
- Replay of skipped sentences at the end of the main experiment (but not for the training phase).
- Calculation and recording of participant performance (repetition time, accuracy).

Usage:
------
Run the script with the following arguments:
    --subject [Subject ID]
    --run [Run number]
    --training (optional, to include a training phase)

Example:
    python mind_sentences.py --subject 1 --run 1 --training
or  python mind_sentences.py --subject 1 --run 1 (without training)

Developed for experimental environments with MEG and FORP buttons using parallel ports.
"""

import os, argparse, time, wave, csv
import pandas as pd
from expyriment import design, control, stimuli, io, misc
from pathlib import Path
from parallel import Parallel
from meg_forp_buttons import get_buttons_state, get_pp_status

# ----------------------- VARIABLES ----------------------- #

SHIFT_CENTER = 0  

pp = Parallel('/dev/parport3')

parser = argparse.ArgumentParser(description='Mind Sentences stimulation script')
parser.add_argument('--subject', type=int, required=True)  
parser.add_argument('--run', type=int, required=True)
parser.add_argument('--training', action='store_true', help="Include a training phase before the experiment")

args = parser.parse_args()

SUB = args.subject
RUN = args.run
training = args.training

CSV_FILE = Path('runs_organization.csv')
DF = pd.read_csv(CSV_FILE)

DF_FILTERED = DF[(DF['subject'] == SUB) & (DF['run'] == RUN)]

AUDIO_FOLDER = Path('audio/')

# ----------------------- FUNCTIONS ----------------------- #

def clear_screen():
    exp.screen.clear()
    exp.screen.update()

def send_trigger():
    pp.setData(255)
    # wait for 50ms
    end_time = time.perf_counter() + 0.05   
    while time.perf_counter() < end_time:
        pass
    pp.setData(0)

def get_audio_duration(audio_path):
    with wave.open(audio_path, 'rb') as audio_file:
        frames = audio_file.getnframes()
        rate = audio_file.getframerate()
        duration = frames / float(rate)
        return duration 
    
def save_response(SUB, RUN, audio_path, response_start_time, response_end_time, time_took, audio_duration, accuracy):
    csv_filename = f"data/sub-{sub}_response.csv"
    
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        if file.tell() == 0: 
            writer.writerow(["subject_id", "run", "audio", "response_start_time (s)", "response_end_time (s)", "time_took (s)", "audio_duration (s)", "accuracy (%)"])
        writer.writerow([SUB, RUN, audio_path, response_start_time, response_end_time, time_took, audio_duration, accuracy])

def calculate_accuracy(audio_duration, time_took):
    real_time_audio = audio_duration
    time_difference = abs(time_took - real_time_audio)
    normalized_difference = time_difference / real_time_audio
    accuracy = max(0, 100 * (1 - normalized_difference))
    return accuracy

def detect_button_pressed(mode="default"):
    """
    Manage buttons detection with 2 different modes.
    - mode="mental_repetition": wait for 2 clicks on 'rightBlue' to go to the next sentence
    - mode="skip" : wait for 1 click on 'rightRed' to go to the next sentence
    """
    press_count = {"rightBlue": 0, "rightRed": 0}
    response_start_time = None
    while True:
        io.Keyboard.process_control_keys()
        pp_status = get_pp_status()
        button_state = get_buttons_state(pp_status)
        
        for button, pressed in button_state.items():
            if pressed and button in press_count:
                if response_start_time is None: 
                    response_start_time = exp.clock.time / 1000
                    print(response_start_time)
                press_count[button] += 1
                print(f"{button} pressed {press_count[button]} time(s)")
                exp.clock.wait(300)  # Anti-rebond
        
        if mode == "mental_repetition":
            if press_count["rightRed"] >= 1:
                print("Participant chose to skip the sentence.")
                return "skip", response_start_time
            elif press_count["rightBlue"] >= 2:
                print("Mental repetition completed.")
                return "completed", response_start_time
        
        elif mode == "skip" and press_count["rightRed"] >= 1:
            print("Skipping to the next sentence.")
            return "skip"

def display_instructions(title, instructions):
    instruction_screen = stimuli.TextScreen(
        title,
        instructions,
        text_colour=(255, 255, 255),
        text_size=30,
        position=(SHIFT_CENTER, 0)
    )
    instruction_screen.present()
    exp.keyboard.wait(misc.constants.K_SPACE)
    clear_screen()

def process_audio(audio_path):
    stim = stimuli.Audio(audio_path)
    stim.preload()

    audio_duration = get_audio_duration(audio_path)

    fixcrossWhite.present(clear=True, update=True)
    exp.clock.wait(1000)

    send_trigger()

    stim.present()
    control.wait_end_audiosystem(process_control_events=True)

    send_trigger()

    clear_screen()
    exp.clock.wait(2000)

    send_trigger()

    fixcrossGreen.present(clear=True, update=True) 

    result, response_start_time = detect_button_pressed(mode="mental_repetition")

    if result == "skip":
        clear_screen()
        exp.clock.wait(1000)
        return True 
    
    response_end_time = exp.clock.time / 1000

    time_took = response_end_time - response_start_time
    accuracy = calculate_accuracy(audio_duration, time_took)
    print(f"Accuracy(%):{accuracy:.2f}")

    clear_screen()
    
    send_trigger()

    exp.clock.wait(1000)

    save_response(SUB, RUN, audio_path, response_start_time, response_end_time, time_took, audio_duration, accuracy)
    return False # phrase not skipped 

def play_phrases(phrases_df, is_training=False, skip_first_n=0):
    """
    Play phrases from the big DataFrame. Optionally skip the first N phrases (e.g., those used in training).
    """
    skipped_phrases = []

    if skip_first_n > 0:
        phrases_df = phrases_df.iloc[skip_first_n:] # or DF_FILTERED

    if is_training:
        training_instructions = (
            "This is a short training phase to get familiar with the task.\n\n"
            "You will now listen to 3 practice sentences.\n\n"
            "Press the blue button at the beginning of your mental repetition,\n"
            "and press it again when you finish.\n"
            "If you cannot remember the sentence, press the red button.\n\n"
            "Press Spacebar to begin the training."
        )
        display_instructions("Training Instructions", training_instructions)

    for _, row in phrases_df.iterrows():
        audio_path = os.path.join(AUDIO_FOLDER, str(row['audio_filename'].split('.')[0])+'_click.wav')
        skipped = process_audio(audio_path)

        if skipped and not is_training:
            skipped_phrases.append(audio_path)

    if not is_training and skipped_phrases:
        print("Replaying skipped phrases...")
        for audio_path in skipped_phrases:
            process_audio(audio_path)

    if is_training:
        post_training_instructions = (
            "The training is now complete.\n\n"
            "We will now proceed to the main experiment.\n\n"
            "Press Spacebar to start the main experiment."
        )
        display_instructions("End of Training", post_training_instructions)

def run_experiment():
    if training:
        play_phrases(DF_FILTERED.head(3), is_training=True)

    # Main experiment phase (skip first 3 phrases if training was conducted)
    experiment_instructions = (
        "Welcome to the Mind Sentences experiment!\n\n"
        "You will listen to a sentence.\n"
        "When the fixation cross turns GREEN, mentally repeat\n"
        "the sentence you just heard.\n\n"
        "Press the blue button at the beginning of your mental repetition,\n"
        "and press the same button again once you have finished.\n"
        "If you can't remember the sentence, just press once the red button.\n\n"
        "Press Spacebar to start."
    )

    display_instructions("Main Experiment Instructions", experiment_instructions)
    skip_first_n = 3 if training else 0
    play_phrases(DF_FILTERED, is_training=False, skip_first_n=skip_first_n)

# ----------------------- EXPERIMENT (SETTINGS AND RUN) ----------------------- #

exp = design.Experiment(name="Mind Sentences")
control.defaults.initialize_delay = 0
control.defaults.audio_system_buffer_size = 4096  
control.audiosystem_channels = 1

control.audiosystem_sample_rate = 44100 #48000  
control.set_develop_mode(False)
control.initialize(exp)

fixcrossWhite = stimuli.FixCross(size=(45, 45), line_width=3,
                                 colour=(255, 255, 255), position=(SHIFT_CENTER, 0))
fixcrossGreen = stimuli.FixCross(size=(45, 45), line_width=3,
                                 colour=(0, 255, 0), position=(SHIFT_CENTER, 0))
fixcrossWhite.preload()
fixcrossGreen.preload()

control.start(exp, subject_id=SUB, skip_ready_screen=True)

run_experiment()

io.Keyboard.process_control_keys()
control.end()
