import os
import shutil
import sounddevice as sd
import subprocess


def error(message):
    return f"\033[97;101m {message} \033[0m"

def info(message):
    return f"\033[97;46m {message} \033[0m"

def comment(message):
    return f"\033[2m{message}\033[0m"

def green(message):
    return f"\033[92m{message}\033[0m"

def red(message):
    return f"\033[91m{message}\033[0m"

def bold(message):
    return f"\033[1m{message}\033[0m"

def italic(message):
    return f"\033[3m{message}\033[0m"

def clear_console_line():
    print(f"\r{' '*100}\r", end="")

def log_journalctl(message, options=[""]):
    command = ["logger"]
    for option in options:
        command.append(option)
    command.append(message)
    subprocess.run(command)


def print_config(config_file, device_name, CUTOFF_FREQUENCY, AMPLITUDE_THRESHOLD, REC_DURATION, SAMPLE_RATE):
    _, _, free = shutil.disk_usage(os.path.dirname(config_file))
    print(
        "\n----------------------------\n"
        f"{bold('Configured audio device')}: {device_name}\n"
        f"{bold('Current audio device')}: default\n"
        f"{bold('Cutoff')}: {CUTOFF_FREQUENCY} Hz\n"
        f"{bold('Threshold')}: {AMPLITUDE_THRESHOLD}\n"
        f"{bold('Record duration')}: {REC_DURATION} seconds\n"
        f"{bold('Sample rate')}: {SAMPLE_RATE} Hz"
        "\n----------------------------\n"
        f"{italic(f'Free space: {free/1000000:.3f} Mo ({os.path.dirname(config_file)})')}"
        "\n----------------------------\n"
    )
# sd.query_devices()[stream.device]['name']
# sd.query_devices()[sd.default.device[0]]['name']

def print_storage_device(storage_device_name):
    print(
        "\n----------------------------\n"
        f"{bold('Storage device')}: {storage_device_name}"
        "\n----------------------------\n"
    )
