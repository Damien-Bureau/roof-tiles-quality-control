import sounddevice as sd


def error(message):
    print(f"\033[97;101m {message} \033[0m")

def info(message):
    print(f"\033[97;46m {message} \033[0m")

def clear_console_line():
    print(f"\r{' '*100}\r", end="")


def print_config(device_name, CUTOFF_FREQUENCY, AMPLITUDE_THRESHOLD, REC_DURATION, SAMPLE_RATE):
    print(
        "----------------------------\n"
        f"\033[1mConfigured audio device\033[0m: {device_name}\n"
        f"\033[1mCurrent audio device\033[0m: default\n"
        f"\033[1mCutoff\033[0m: {CUTOFF_FREQUENCY} Hz\n"
        f"\033[1mThreshold\033[0m: {AMPLITUDE_THRESHOLD}\n"
        f"\033[1mRecord duration\033[0m: {REC_DURATION} seconds\n"
        f"\033[1mSample rate\033[0m: {SAMPLE_RATE} Hz"
        "\n----------------------------\n"
    )
# sd.query_devices()[stream.device]['name']
# sd.query_devices()[sd.default.device[0]]['name']

def print_storage_device(storage_device_name):
    print(
        "\n----------------------------\n"
        f"\033[1mStorage device\033[0m: {storage_device_name}"
        "\n----------------------------\n"
    )
