import os
import pyudev
import subprocess as sp
import sounddevice as sd

from shell_functions import info, error, comment, green, red, bold, log_journalctl

# Audio device functions --------------------------------------------------------------------------

def get_input_devices_list():
    devices = sd.query_devices()
    input_devices_names = []
    input_devices_id = []

    #print()
    for device in devices:
        if device.get('max_input_channels') > 0 and device.get('name') != 'pulse':
            device_id = device.get('index')
            device_name = device.get('name')
            #print(f"Input Device {device_id} - {device_name}")
            input_devices_names.append(device_name)
            input_devices_id.append(device_id)
    #print()
    
    return input_devices_names, input_devices_id


def set_default_audio_input_device(device_index):
    devices = sd.query_devices()
    old_default_device = devices[sd.default.device[0]].get('name')
    sd.default.device = device_index
    print(f"\nOld default device: {old_default_device}")
    print(f"New default device: {devices[sd.default.device[0]].get('name')}\n")



def is_microphone_connected():
    mic_name = "USB_PnP_Sound_Device" # to change if a different microphone is used
    mic_connected = False

    context = pyudev.Context()
    for device in context.list_devices():
        if mic_name in str(device.get('ID_MODEL')):
            mic_connected = True
    
    return mic_connected



# Storage device functions ------------------------------------------------------------------------


def check_folder(folder_name: str, print_end="\n"):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f'Created folder "{folder_name}"', end=print_end)


def mount_usb_device(device_path, mount_point):
    print("  |\n  | mounting device...", end="")
    check_folder(mount_point, print_end="")
    try:
        output = sp.run(["sudo", "mount", device_path, mount_point], text=True, capture_output=True, check=True)
        print(green("done"))
        print("  | USB device mounted successfully.")
        log_journalctl(message=f"USB device {device_path} mounted successfully at {mount_point}", options=["-p", "debug"])
    except sp.CalledProcessError as e:
        print(error("error"))
        print(f"  | {red(e)}")
        print(f"  | {comment(e.stderr)}")
        log_journalctl(message=f"Error while mounting {device_path} at {mount_point}", options=["-p", "error"])
        log_journalctl(message=e.stderr, options=["-p", "warning"])


def unmount_usb_device(mount_point):
    print("\n  | Unmounting device...", end="")
    try:
        output = sp.run(["sudo", "umount", mount_point], text=True, capture_output=True, check=True)
        print(green("done"))
        print("  | USB device unmounted successfully.")
        log_journalctl(message=f"USB device unmounted successfully at {mount_point}", options=["-p", "debug"])
    except sp.CalledProcessError as e:
        print(error("error"))
        print(f"  | {red(e)}")
        print(f"  | {comment(e.stderr)}")
        log_journalctl(message=f"Error while unmounting device at {mount_point}", options=["-p", "error"])
        log_journalctl(message=e.stderr, options=["-p", "warning"])



def get_usb_device_info():
    print("\n\ngetting usb device info... ", end="")
    sp.run(["sleep", "1.5"])
    try:
        output = sp.run(["sudo", "blkid"], text=True, check=True, capture_output=True)
        lines = []
        for line in output.stdout.split('\n'):
            if "bootfs" not in line and "rootfs" not in line and 'TYPE="vfat"' in line:
                lines.append(line)
        
        print(green("done"))
        print(comment(f"found {len(lines)} device{'s' if len(lines)>1 else ''}"))
        return lines
    except sp.CalledProcessError as e:
        print(red("error"))
        print(error(f"\nError with command 'sudo blkid': {e}"))
        return []


def extract_device_info(device_info):
    print("\n  | extracting device info... ", end="")
    try:
        # Extract device path and label
        device_path = device_info.split(':')[0]
        device_label = device_info.split('LABEL="')[1].split('"')[0]
        print(green("done"))
        return device_path, device_label
    except IndexError:
        print(red("error"))
        print(error(f"\n | Error while extracting device info: {device_info}"))
        return None, None


def listen_udev_events():
    # Create context and monitor to check udev events
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='usb')

    # Loop to listen to udev events
    while True:
        device = monitor.poll()
        if device is not None:
            # Device connected
            if device.action == 'add':
                device_info_list = get_usb_device_info()
                for device_info in device_info_list:
                    global device_label
                    device_path, device_label = extract_device_info(device_info)
                    print(f"  | USB device connected: {bold(device_label)} ({device_path})")
                    
                    # Mount device
                    mount_point = f"/mnt/usb/{device_label}"
                    mount_usb_device(device_path, mount_point)
            

            # Device disconnected
            elif device.action == 'remove':
                device_info_list = get_usb_device_info()
                for device_info in device_info_list:
                    device_path, device_label = extract_device_info(device_info)
                    print(f"  | USB device disconnected: {bold(device_label)} ({device_path})")
                
                # Unmount device
                mount_point = f"/mnt/usb/{device_label}"
                unmount_usb_device(mount_point)
                    
            break  # Exit the loop after processing one event


print(comment("\nListening..."))
import time as t
while True:
    listen_udev_events()
    t.sleep(0.01)



def find_storage_device():
    '''
    context = pyudev.Context()
    devices = []
    for device in context.list_devices(subsystem='block'):
        if device.get('ID_BUS') == "usb":
            devices.append(device.device_node)
    return devices

    '''
    devices_folders = os.listdir("/mnt/usb/") # "/media/pi")
    if any(devices_folders):
        return "USB_DAMIEN/" #devices_folders[0]
    else:
        return None
    