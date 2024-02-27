


def error(message):
    print(f"\033[97;101m {message} \033[0m")

def info(message):
    print(f"\033[97;46m {message} \033[0m")

def clear_console_line():
    print(f"\r{' '*100}\r", end="")


def print_audio_settings(device_name, CUTOFF_FREQUENCY, AMPLITUDE_THRESHOLD):
    print(
        "----------------------------\n"
        f"\033[1mAudio device\033[0m: {device_name}\n"
        f"\033[1mCutoff\033[0m: {CUTOFF_FREQUENCY} Hz\n"
        f"\033[1mThreshold\033[0m: {AMPLITUDE_THRESHOLD}"
        "\n----------------------------\n"
    )

def print_storage_device(storage_device_name):
    print(
        "\n----------------------------\n"
        f"\033[1mStorage device\033[0m: {storage_device_name}"
        "\n----------------------------\n"
    )
