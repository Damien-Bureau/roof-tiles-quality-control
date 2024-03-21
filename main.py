import sys
import os
import shutil
import traceback

import time as t
import datetime as dt

import RPi.GPIO as GPIO # buttons

import numpy as np
import csv
import sounddevice as sd # record audio
import scipy # save audio in a file

import devices
from shell_functions import error, info, comment, green, red, bold, italic, clear_console_line, print_config, log_journalctl
from led_display_functions import led_fully_white, led_circle, led_white_cross, led_error_animation


def read_button(button_pin: int):
    return GPIO.input(button_pin)


def green_btn_pressed():
    global green_btn_press_timestamp, nothing_happened_feedback_shown
    green_btn_press_timestamp = get_record_duration()
    write_event_in_file(event_name="green", event_timestamp=green_btn_press_timestamp)
    led_circle(color=GREEN_RGB)
    nothing_happened_feedback_shown = False
    print(f"{green('Green button')} was pressed (timestamp: {round(green_btn_press_timestamp,3)})")


def red_btn_pressed():
    global red_btn_press_timestamp, nothing_happened_feedback_shown
    red_btn_press_timestamp = get_record_duration()
    write_event_in_file(event_name="red", event_timestamp=red_btn_press_timestamp)
    led_circle(color=RED_RGB)
    nothing_happened_feedback_shown = False
    print(f"{red('Red button')} was pressed (timestamp: {round(red_btn_press_timestamp,3)})")


def get_datetime():
    raw_datetime = dt.datetime.now()
    return raw_datetime.strftime("%Y%m%d_%H-%M-%S")


def reset_audio_variables():
    global audio, samples_counter
    audio = []
    samples_counter = 0


def error_while_writing_in_storage_device(stop_the_record: bool):
    global last_screen_shown
    last_screen_shown = False

    if stop_the_record == True:
        stop_recording(reason="error while writing in storage device")
    
    # Waits for the device to be disconnected (so the user can free up space)
    while devices.is_storage_device_connected():
        led_error_animation(error="writing")

    # The storage device is disconnected
    check_storage_device()

    # Show last image on LED screen (always white cross because record stops when an error occurs)
    if last_screen_shown == False:
        reset_audio_variables()
        clear_console_line()
        led_white_cross()
        last_screen_shown = True


def write_csv_row(filename: str, data: list):
    with open(filename, 'a') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(data)


def write_event_in_file(event_name: str, event_timestamp: float):
    try:
        write_csv_row(f"{devices.EVENTS_FILES_FOLDER}{filename}.csv", [round(event_timestamp,3), event_name])
        return True
    
    except Exception as e: # device disconnected or no space left on device
        print(red("\nerror while writing event in csv file"), end="")
        log_journalctl(message=repr(e), options=["-p", "error"])
        log_journalctl(message="Error while writing event in csv file", options=["-p", "debug"])
        error_while_writing_in_storage_device(stop_the_record=True)
        return False


def write_config_file_with_default_values(config_file):
    try:
        with open(config_file, mode='w') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerows([
                ["device_name", device_name],
                ["cutoff_Hz", CUTOFF_FREQUENCY],
                ["threshold", AMPLITUDE_THRESHOLD],
                ["rec_duration_seconds", REC_DURATION],
                ["sample_rate_Hz", SAMPLE_RATE],
                ["waiting_duration", 5],
                ["long_press_duration", 1.5],
                ["min_time_gap_between_2_button_presses", 0.1],
                ["min_time_gap_between_2_hits", 0.5]])
        print(green("done"))
        print_config(config_file, device_name, CUTOFF_FREQUENCY, AMPLITUDE_THRESHOLD, REC_DURATION, SAMPLE_RATE)
        return True

    except Exception as e: # device disconnected or no space left on device
        print(error("failed"))
        log_journalctl(message=traceback.print_exc, options=["-p", "error"])
        log_journalctl(message="Error while writing config file with default values", options=["-p", "debug"])
        error_while_writing_in_storage_device(stop_the_record=False)
        return None


def save_audio_file(path: str, filename: str, data: list):
    scipy.io.wavfile.write(f"{path}{filename}.wav", SAMPLE_RATE, np.array(data)) # saves the audio recorded into a file


def samples_to_seconds(sample: int):
    return sample * SAMPLE_DURATION


def get_record_duration(str_format=False):
    duration = len(audio) * SAMPLE_DURATION
    return f"{duration:.3f}" if str_format else duration


def lowpass(data: list, cutoff: float, sample_rate: float, poles: int=5):
    sos = scipy.signal.butter(poles, cutoff, 'lowpass', fs=sample_rate, output='sos')
    filtered_data = scipy.signal.sosfiltfilt(sos, data, padlen=None)
    return filtered_data


def hit_detection(data: list):
    global last_hit, hits_detected, hit_i
    data = data[-HIT_DETECTION_ON_N_SAMPLES:]
    # if len(data) < HIT_DETECTION_ON_N_SAMPLES:
    #    print(error(f"data too short ({len(data)} < {HIT_DETECTION_ON_N_SAMPLES})"))
    start_index = len(audio) - HIT_DETECTION_ON_N_SAMPLES
    filtered_data = lowpass(data, cutoff=CUTOFF_FREQUENCY, sample_rate=SAMPLE_RATE)
    hits_detected = []
    first_hit = True
    for i in range(len(filtered_data)):
        amplitude = filtered_data[i]
        time_since_last_hit = i - last_hit # to avoid bouncing
        if amplitude > AMPLITUDE_THRESHOLD and (time_since_last_hit > MINIMUM_SAMPLE_GAP_BETWEEN_TWO_HITS or first_hit is True):
            first_hit = False
            last_hit = i
            hits_detected.append(samples_to_seconds(last_hit + start_index))            
    return hits_detected


def read_and_store_hits_detected():
    global last_hit_timestamp, nothing_happened_feedback_shown
    if any(hits_detected):
        nothing_happened_feedback_shown = False
        last_hit_timestamp = max(hits_detected)
        led_circle(color=VOID_RGB)
        for hit_timestamp in hits_detected:
            hit_timestamp_str = round(hit_timestamp, 3)
            if (get_record_duration() - hit_timestamp) > 0.2: # to avoid printing twice the same message
                write_event_in_file(event_name="hit", event_timestamp=hit_timestamp)
                print(f"\033[36mHit detected\033[0m - please press a button to label the hit (timestamp: {hit_timestamp_str})")


def start_recording():
    global state, filename, nothing_happened_feedback_shown, audio, samples_counter, green_btn_press_timestamp, red_btn_press_timestamp
    try:
        filename = get_datetime()
        write_csv_row(f"{devices.EVENTS_FILES_FOLDER}{filename}.csv", [0, "on"]) # starts a new csv file
    except Exception as e:
        print(error("failed to start the record"))
        log_journalctl(message=repr(e), options=["-p", "error"])
        log_journalctl(message="Failed to start the record", options=["-p", "debug"])
        error_while_writing_in_storage_device(stop_the_record=False)
        return # cancel the starting procedure if an error occurs

    state = "recording"
    nothing_happened_feedback_shown = True
    reset_audio_variables()
    green_btn_press_timestamp, red_btn_press_timestamp = 0, 0
    stream.start()
    led_fully_white()
    print(
        f"{'~'*77}"
        f"\n  Green button was pressed for {button_press_duration:.2f}s, switching to another state: \033[1;4m{state.upper()}\033[0m "
        f"\n{'~'*77}\n"
        )


def write_files_when_record_stops(event_name: str):
    try:
        if filename:
            write_csv_row(f"{devices.EVENTS_FILES_FOLDER}{filename}.csv", [get_record_duration(str_format=True), event_name])
            save_audio_file(path=devices.EVENTS_FILES_FOLDER, filename=filename, data=audio)
            return True
    
    except Exception as e:
        print(error("failed to write files at the end of the record"))
        log_journalctl(message=repr(e), options=["-p", "error"])
        log_journalctl(message=f"Failed to write files at the end of the record (event: {event_name})", options=["-p", "debug"])
        error_while_writing_in_storage_device(stop_the_record=False)
        return None


def stop_recording(reason="red button long press"):
    global state, audio, samples_counter
    state = "not recording"
    event_name = "off"
    
    if reason == "red button long press":
        if write_files_when_record_stops(event_name): # no error occured while writing files
            print(
                f"\n{'#'*83}"
                f"\n##  Red button was pressed for {button_press_duration:.2f}s, switching to another state: \033[1;4m{state.upper()}\033[0m  ##"
                f"\n##  .csv and .wav files saved as {filename} ({get_record_duration(str_format=True)}s) {' '*(25-len(get_record_duration(str_format=True)))} ##"
                f"\n{'#'*83}\n"
                )
        else: # an error occured while writing files
            print(
                f"\n{'#'*83}"
                f"\n##  Red button was pressed for {button_press_duration:.2f}s, switching to another state: \033[1;4m{state.upper()}\033[0m  ##"
                f"\n##  {red('An error occured while saving files')} {filename} ({get_record_duration(str_format=True)}s) {' '*(18-len(get_record_duration(str_format=True)))} ##"
                f"\n{'#'*83}\n"
                )
        print(comment(f"Press the green button for {LONG_PRESS_DURATION}s to start recording"))

    elif reason == "microphone disconnected":
        event_name = "mic_error"
        write_files_when_record_stops(event_name)
        print(
            f"\n{'#'*78}"
            f"\n##  Microphone was disconnected, switching to another state: \033[1;4m{state.upper()}\033[0m  ##"
            f"\n##  .csv and .wav files saved as {filename} ({get_record_duration(str_format=True)}s) {' '*(20-len(get_record_duration(str_format=True)))} ##"
            f"\n{'#'*78}\n"
            )
    
    elif reason == "error while writing in storage device":
        print(
            f"\n{'#'*88}"
            f"\n##  {red('Error while writing in storage device')}, switching to another state: \033[1;4m{state.upper()}\033[0m  ##"
            f"\n##  Unable to save files {filename} ({get_record_duration(str_format=True)}s) {' '*(38-len(get_record_duration(str_format=True)))} ##"
            f"\n{'#'*88}\n"
            )
    
    elif reason == "storage device disconnected" and stream.active == True:
        print(
            f"\n{'#'*82}"
            f"\n##  Storage device was disconnected, switching to another state: \033[1;4m{state.upper()}\033[0m  ##"
            f"\n##  Unable to save files {filename} ({get_record_duration(str_format=True)}s) {' '*(32-len(get_record_duration(str_format=True)))} ##"
            f"\n{'#'*82}\n"
            )
    
    stream.stop()
    reset_audio_variables()
    led_white_cross()
    # visualize_audio_and_events(filename, AMPLITUDE_THRESHOLD, files_path="events_files")


def start_new_file():
    global audio, samples_counter, filename, green_btn_press_timestamp, red_btn_press_timestamp

    try:
        save_audio_file(path=devices.EVENTS_FILES_FOLDER, filename=filename, data=audio)
    except Exception as e:
        log_journalctl(message=repr(e), options=["-p", "error"])
        log_journalctl(message="Failed to start new file", options=["-p", "debug"])
        error_while_writing_in_storage_device(stop_the_record=True)
        return
    
    print(
        f"\n{'#'*62}"
        f"\n##  The record started {get_record_duration():.2f}s ago, time to make a new one!  ##"
        f"\n##  .csv and .wav files saved as {filename} {' '*8} ##"
        f"\n{'#'*62}\n"
        )
    filename = get_datetime()
    reset_audio_variables()
    green_btn_press_timestamp, red_btn_press_timestamp = 0, 0


def check_microphone(stop_the_record: bool=True):
    global last_screen_shown
    if not(devices.is_microphone_connected()):
        if stop_the_record == True:
            try:
                stop_recording(reason="microphone disconnected")
            except NameError: # if it's not recording
                pass
        last_screen_shown = False
        print(f"\rMicrophone not connected! {' '*100}\r", end="")
        while not(devices.is_microphone_connected()): # show animation on LED screen
            led_error_animation(error="mic")
        # The microphone is connected again
        reset_audio_variables()

    # Show last image on LED screen (always white cross because record stops when an error occurs)
    if last_screen_shown == False:
        reset_audio_variables()
        clear_console_line()
        led_white_cross()
        last_screen_shown = True
        

def read_config():
    global device_name, CUTOFF_FREQUENCY, AMPLITUDE_THRESHOLD, REC_DURATION, SAMPLE_RATE
    global WAITING_DURATION, LONG_PRESS_DURATION, MINIMUM_TIME_GAP_BUTTONS, MINIMUM_SAMPLE_GAP_BETWEEN_TWO_HITS
    print("\nReading config file... ", end="")

    config_file_name = "config.csv"
    config_file = f"{devices.DEVICE_PATH}/{config_file_name}"
    config_file_found = os.path.exists(config_file)
    
    if config_file_found == True:
        error_while_reading_config = False
        try:
            # Read parameters
            parameters = {}
            with open(config_file, mode='r') as csvfile:
                for line in csvfile:
                    parameter, value = [element.strip() for element in line.split(';')]
                    parameters[parameter] = value
            
            # Extract parameters
            'sd.default.device = int(parameters["device"])'
            device_name = parameters["device_name"]
            CUTOFF_FREQUENCY = int(parameters["cutoff_Hz"])
            AMPLITUDE_THRESHOLD = float(parameters["threshold"])
            REC_DURATION = int(parameters["rec_duration_seconds"])
            SAMPLE_RATE = int(parameters["sample_rate_Hz"])
            WAITING_DURATION = int(parameters["waiting_duration_seconds"])
            LONG_PRESS_DURATION = int(parameters["long_press_duration_seconds"])
            MINIMUM_TIME_GAP_BUTTONS = int(parameters["min_time_gap_between_2_button_presses_seconds"])
            MINIMUM_TIME_GAP_BETWEEN_TWO_HITS = int(parameters["min_time_gap_between_2_hits_seconds"])
            MINIMUM_SAMPLE_GAP_BETWEEN_TWO_HITS = int(MINIMUM_TIME_GAP_BETWEEN_TWO_HITS * SAMPLE_RATE)

            print(green("done"))
            print_config(config_file, device_name, CUTOFF_FREQUENCY, AMPLITUDE_THRESHOLD, REC_DURATION, SAMPLE_RATE)
        
        except: # error while reading file
            error_while_reading_config = True

            # Create a copy of the file found
            unreadable_config_file = f"{devices.DEVICE_PATH}/unreadable_{config_file_name}"
            with open(unreadable_config_file, mode='w'):
                pass
            shutil.copy(config_file, unreadable_config_file)
            
    if config_file_found == False or error_while_reading_config == True:
        print(red("failed"))
        try:
            device_name = sd.query_devices()[sd.default.device[0]].get('name')
        except Exception as e:
            log_journalctl(message=repr(e), options=["-p", "warning"])
            log_journalctl(message="sounddevice.query_devices() returns nothing!", options=["-p", "debug"])
            check_microphone(stop_the_record=False)
            
        
        # DEFAULT CONFIG
        CUTOFF_FREQUENCY = 15000   # Hz
        AMPLITUDE_THRESHOLD = 0.3  # between 0 and 1
        REC_DURATION = 60          # new file every [...] seconds
        SAMPLE_RATE = 44100        # samples per second
        WAITING_DURATION = 5       # seconds, time threshold when nothing happens
        LONG_PRESS_DURATION = 1.5  # seconds, for buttons
        MINIMUM_TIME_GAP_BUTTONS = 0.1  # seconds, minimum time between two presses, to avoid bouncing
        MINIMUM_TIME_GAP_BETWEEN_TWO_HITS = 0.5  # seconds, minimum time between two hits
        MINIMUM_SAMPLE_GAP_BETWEEN_TWO_HITS = int(MINIMUM_TIME_GAP_BETWEEN_TWO_HITS * SAMPLE_RATE)
        

        # Logs
        if config_file_found == False:
            print("  |", comment("No config file found"))
        elif error_while_reading_config == True:
            print("  |", comment("Unreadable config copied to another file: unreadable_config.csv"))
        print("  | Creating a new configuration file with default values... ", end="")

        # Create a new file with default config values
        write_config_file_with_default_values(config_file)


def check_storage_device(first_check=False):
    global last_screen_shown
    if devices.is_storage_device_connected() == False:
        # No storage device connected
        try:
            stop_recording(reason="storage device disconnected")
        except NameError: # if stream isn't defined (at the first launch)
            pass
        
        last_screen_shown = False
        while devices.is_storage_device_connected() == False:
            led_error_animation(error="storage")

        # The storage device is connected again
        if first_check == False:
            read_config()
        reset_audio_variables()
    
    if first_check == True:
        read_config()

    # Show last image on LED screen (always white cross because record stops when an error occurs)
    if last_screen_shown == False:
        reset_audio_variables()
        clear_console_line()
        led_white_cross()
        last_screen_shown = True


def audio_callback(indata: np.ndarray, frames, time, status):
    global audio, samples_counter
    audio.extend(indata.reshape(-1))
    samples_counter += len(indata)


## LED SCREEN
RED_RGB = (255, 0, 0)
GREEN_RGB = (0, 255, 0)
VOID_RGB = (0, 0, 0)
WHITE_RGB = (255, 255, 255)


## DEVICES VERIFICATIONS
last_screen_shown = False

# Storage device
devices.listen_udev_events() # start asynchronous udev event observer (device events)
devices.check_if_usb_device_already_connected() # if it's already connected, it wouldn't appear in udev events
check_storage_device(first_check=True)

# Audio device
check_microphone() # doesn't start the stream if there's no audio device


## AUDIO RECORDING
SAMPLE_DURATION = 1/SAMPLE_RATE

sd.default.samplerate = SAMPLE_RATE
sd.default.channels = 1 # 1 for mono, 2 for stereo

stream = sd.InputStream(callback=audio_callback)
stream.abort()

audio = []


## HIT DETECTION : low-pass filter + amplitude threshold
DURATION_BETWEEN_HIT_DETECTION = 0.8 # seconds
OVERLAP_FACTOR = 1.2
HIT_DETECTION_ON_N_SAMPLES = int(DURATION_BETWEEN_HIT_DETECTION * OVERLAP_FACTOR / SAMPLE_DURATION)
last_hit = 0
samples_counter = 0


## BUTTONS
GPIO.setmode(GPIO.BOARD)  # use physical pin numbering
GREEN_BTN_PIN = 38
RED_BTN_PIN = 40

GPIO.setup(GREEN_BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(RED_BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Rising edge detection variables
green_btn_state = read_button(button_pin=GREEN_BTN_PIN)
green_btn_last_state = 1 - green_btn_state
red_btn_state = read_button(button_pin=RED_BTN_PIN)
red_btn_last_state = 1 - red_btn_state

# Events timestamps
green_btn_press_timestamp = 0
red_btn_press_timestamp = 0
last_hit_timestamp = 0


## LAUNCH
state = "not recording"
print(f"\nCurrent state: \033[1;4m{state.upper()}\033[0m\n")
print(comment(f"Press the green button for {LONG_PRESS_DURATION}s to start recording"))


### MAIN LOOP
while True:
    while state == "not recording":
        
        check_microphone()
        check_storage_device()
        
        green_btn_state = read_button(button_pin=GREEN_BTN_PIN)
        
        # Rising edge on the GREEN button
        if green_btn_state != green_btn_last_state:
            button_press_start_time = t.monotonic()
            
        # GREEN button held: start recording if it's a long press
        if green_btn_state == green_btn_last_state:
            button_press_duration = t.monotonic() - button_press_start_time
            if button_press_duration > LONG_PRESS_DURATION:
                start_recording()
        
        green_btn_last_state = green_btn_state
    
    while state == "recording":
        
        check_microphone()
        check_storage_device()
        
        green_btn_state = read_button(button_pin=GREEN_BTN_PIN)
        red_btn_state = read_button(button_pin=RED_BTN_PIN)
        
        # Rising edge on the GREEN button
        enough_time_since_last_press = (get_record_duration()-green_btn_press_timestamp) > MINIMUM_TIME_GAP_BUTTONS
        if green_btn_state != green_btn_last_state and enough_time_since_last_press:
            green_btn_pressed()
        
        # Rising edge on the RED button
        enough_time_since_last_press = (get_record_duration()-red_btn_press_timestamp) > MINIMUM_TIME_GAP_BUTTONS
        if red_btn_state != red_btn_last_state and enough_time_since_last_press:
            red_btn_pressed()
        
        # Red button held: stop recording if it's a long press
        if red_btn_state == red_btn_last_state:
            button_press_duration = get_record_duration() - red_btn_press_timestamp
            if button_press_duration > LONG_PRESS_DURATION:
                stop_recording()
            
        green_btn_last_state = green_btn_state
        red_btn_last_state = red_btn_state
        
        
        # Doing hit detection when DURATION_BETWEEN_HIT_DETECTION is reached
        if samples_to_seconds(samples_counter) > DURATION_BETWEEN_HIT_DETECTION:
#             print(info(f"{samples_counter} samples = {samples_to_seconds(samples_counter):.3f}s"))
            samples_counter = 0
            hit_detection(data=audio)
            read_and_store_hits_detected()
        
        
        # If nothing happens, LEDs are fully white
        last_event_timestamp = max(green_btn_press_timestamp, red_btn_press_timestamp, last_hit_timestamp)
        time_since_last_event = get_record_duration() - last_event_timestamp
        if time_since_last_event > WAITING_DURATION and not(nothing_happened_feedback_shown):
            led_fully_white()
            print(italic(f"\nNothing happened for {time_since_last_event:.2f}s, color feedback set to fully white\n"))
            nothing_happened_feedback_shown = True
            
        
        # Starts a new file every REC_DURATION
        if get_record_duration() >= REC_DURATION:
            start_new_file()

