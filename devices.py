import os
import pyudev
import subprocess
import sounddevice as sd

from shell_functions import info, error, comment, green, red, bold, italic, log_journalctl

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


def check_folder(folder_name: str, before_print="", print_end="\n"):
    # Create a folder if it doesn't already exists
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f'{before_print}Created folder "{folder_name}"', end=print_end)


def mount_usb_device(device_path, mount_point):
    print(f"  |\n  | Mounting device at {mount_point}... ", end="")

    # Create mount point folder if it doesn't already exists
    check_folder(mount_point, before_print=f"{comment('no folder found')}\n  |   ", print_end="... ")
    
    try:
        # Mount device using linux command 'mount'
        subprocess.run(["sudo", "mount", device_path, mount_point], text=True, capture_output=True, check=True)
        print(green("done"))
        print("  | USB device mounted successfully.\n")
        log_journalctl(message=f"USB device {device_path} mounted successfully at {mount_point}", options=["-p", "debug"])
    
    except subprocess.CalledProcessError as e:
        # Just show if an error occurs
        print(error("error"))
        print(f"  | {red(e)}")
        print(f"  | {comment(e.stderr)}")
        log_journalctl(message=f"Error while mounting {device_path} at {mount_point}", options=["-p", "error"])
        log_journalctl(message=f"Command returned non-zero exit status {e.returncode}", options=["-p", "warning"])
        log_journalctl(message=e.stderr, options=["-p", "warning"])


def unmount_usb_device(mount_point):
    print(f"  |\n  | Unmounting device at {mount_point}... ", end="")
    
    try:
        # Unmount device using linux command 'umount'
        subprocess.run(["sudo", "umount", mount_point], text=True, capture_output=True, check=True)
        print(green("done"))
        print("  | USB device unmounted successfully.\n")
        log_journalctl(message=f"USB device unmounted successfully at {mount_point}", options=["-p", "debug"])
    
    except subprocess.CalledProcessError as e:
        # Just show if an error occurs
        print(error("error"))
        print(f"  | {red(e)}")
        print(f"  | {comment(e.stderr)}")
        log_journalctl(message=f"Error while unmounting device at {mount_point}", options=["-p", "error"])
        log_journalctl(message=f"Command returned non-zero exit status {e.returncode}", options=["-p", "warning"])
        log_journalctl(message=e.stderr, options=["-p", "warning"])


def get_usb_device_info(device):
    print(f"\nUdev event: {italic(device.action)}")
    print("Getting USB device info... ", end="")

    # Get info about device from udev event
    properties = device.properties
    device_type = properties.get('DEVTYPE')
    device_path = properties.get('DEVNAME')
    device_label = properties.get('ID_FS_LABEL_ENC')
    
    # Check if it's a storage device
    if device_type in ["disk", "partition"] and device_path and device_label:
        print(green("done"))
    else:
        print(red("failed"))
        print(comment(f"devtype={device_type} path={device_path} name={device_label}"))
    
    return device_path, device_label


def listen_udev_events():
    # Create context and monitor to check udev events
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block')

    # Loop to listen to udev events
    while True:
        device = monitor.poll()
        if device is not None:
            if device.action == 'add':  # device connected
                device_path, device_label = get_usb_device_info(device)

                if device_path and device_label: # if info about device are available
                    print(f"  |\n  | USB device connected: {bold(device_label)} ({device_path})")
                    
                    # Mount device
                    mount_point = f"/mnt/usb/{device_label}"
                    mount_usb_device(device_path, mount_point)
            
            elif device.action == 'remove': # device disconnected
                device_path, device_label = get_usb_device_info(device)

                if device_path and device_label: # if info about device are available
                    print(f"  |\n  | USB device disconnected: {bold(device_label)} ({device_path})")
                
                    # Unmount device
                    mount_point = f"/mnt/usb/{device_label}"
                    unmount_usb_device(mount_point)
                    
            break  # Exit the loop after processing one event


def check_if_usb_device_already_connected():
    print("\nchecking if an USB device is already connected... ", end="")

    # Wait to be sure the device is detected
    subprocess.run(["sleep", "1.5"])
    
    try:
        output = subprocess.run(["sudo", "blkid"], text=True, check=True, capture_output=True)
        lines = []
        device_path, device_label = None, None
        for line in output.stdout.split("\n"):
            if "bootfs" not in line and "rootfs" not in line and 'TYPE="vfat"' in line:
                lines.append(line)
                # Extract device path and label
                # NB: only the last device will be retained, since only one is needed
                device_path = line.split(':')[0]
                device_label = line.split('LABEL="')[1].split('"')[0]

        print(green("done"))
        print("  |", comment(f"found {len(lines)} device{'s' if len(lines)>1 else ''}"))
        
        if device_path and device_label:
            print(f"  |\n  | USB device connected: {bold(device_label)} ({device_path})")
                    
            # Mount device
            mount_point = f"/mnt/usb/{device_label}"
            mount_usb_device(device_path, mount_point)
    
    except subprocess.CalledProcessError as e:
        print(error("error"))
        print(f"  | {red(e)}")
        print(f"  | {comment(e.stderr)}")
        return []


# check_if_usb_device_already_connected()
# print(comment("\nListening..."))
# import time as t
# while True:
#     listen_udev_events()
#     t.sleep(0.01)



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
    