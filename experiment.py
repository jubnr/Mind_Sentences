#! /usr/bin/env python3
#----- 20k-phrases experiment script -----#

import utils, os, random, argparse
from expyriment import design, control, stimuli, io, misc
from pathlib import Path

SHIFT_CENTER = 0  
BIP_WINDOW = 0.220 # seconds
SILENCE_WINDOW = 0.300 # seconds

#pp = io.ParallelPort('/dev/parport1')

def clear_screen():
    exp.screen.clear()
    exp.screen.update()

def calculate_accuracy(audio_duration, response_end_time):
    #real_time_audio = audio_duration - (BIP_WINDOW - SILENCE_WINDOW)
    real_time_audio = audio_duration # added in V2
    time_difference = abs(time_took - real_time_audio)
    normalized_difference = time_difference / real_time_audio
    accuracy = max(0, 100 * (1 - normalized_difference))
    return accuracy

parser = argparse.ArgumentParser(description='20k-phrases stimulation script')
parser.add_argument('--subject', type=int, required=True)  
args = parser.parse_args()
sub = args.subject

audio_folder = Path('audio/')
files = [f for f in os.listdir(audio_folder) if f.endswith('.wav')]
random.shuffle(files)
audio_files = [os.path.join(audio_folder, f) for f in files]

exp = design.Experiment(name="20k-phrases")
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

control.start(exp, subject_id=sub, skip_ready_screen=True)

stimuli.TextLine("Press Spacebar when ready...", text_size=50, text_colour=(245, 167, 66), position=(SHIFT_CENTER, 0)).present()
exp.keyboard.read_out_buffered_keys()
exp.keyboard.wait(misc.constants.K_SPACE)
clear_screen()

start_sound = stimuli.Audio("bip.wav")
stop_sound = stimuli.Audio("boop.wav")
start_sound.preload()
stop_sound.preload()

for audio_path in audio_files:
    stim = stimuli.Audio(audio_path) # to be changed
    stim.preload()

    audio_duration = utils.get_audio_duration(audio_path)

    #utils.send_trigger()

    fixcrossWhite.present(clear=True, update=True)
    exp.clock.wait(1000)

    stim.present()
    control.wait_end_audiosystem(process_control_events=True)
    
    #utils.send_trigger()

    #exp.clock.wait(2000)
    clear_screen()
    exp.keyboard.wait()
    fixcrossGreen.present(clear=True, update=True) 
    response_start_time = exp.clock.time / 1000
    
    #start_sound.play()
    exp.keyboard.wait() # added in V2
    response_end_time = exp.clock.time / 1000
    #stop_sound.play()
    exp.clock.wait(1000)
    time_took = response_end_time - response_start_time

    accuracy = calculate_accuracy(audio_duration, response_end_time)
    print(f"Accuracy(%):{accuracy:.2f}")

    clear_screen()
    exp.clock.wait(1000)

    utils.save_response(sub, audio_path, response_start_time, response_end_time, time_took, audio_duration, accuracy)

io.Keyboard.process_control_keys()
control.end()
