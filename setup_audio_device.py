import queue
import sys

from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
import scipy

import tkinter as tk
from tkinter import ttk, filedialog

import multiprocessing as mpr
import ctypes

import csv

sys.path.append('Tests')
from get_input_devices import get_input_devices_list, set_default_device


## Audio processing functions

def lowpass(data: list, cutoff: float, sample_rate: float, poles: int=5):
    sos = scipy.signal.butter(poles, cutoff, 'lowpass', fs=sample_rate, output='sos')
    filtered_data = scipy.signal.sosfiltfilt(sos, data, axis=0, padlen=None)
    return filtered_data

'''
def hit_detection(data, threshold):
    hits_detected = []
    for i in range(len(data)):
        amplitude = data[i, 0]
        if amplitude > threshold:
            hits_detected.append(amplitude)
        else:
            hits_detected.append(0)
    
    return hits_detected'''

## Real time audio visualizing

def audio_callback(indata, frames, time, status):
    q.put(indata[::DOWNSAMPLE, [0]])


def update_plot(frame):
    """
    This is called by matplotlib for each plot update.
    Typically, audio callbacks happen more frequently than plot updates,
    therefore the queue tends to contain multiple blocks of audio data.
    """
    global plotdata
    while True:
        try:
            data = q.get_nowait()
        except queue.Empty:
            break
        shift = len(data)
        plotdata = np.roll(plotdata, -shift, axis=0)
        plotdata[-shift:, :] = data
        
    lines_input.set_ydata(plotdata[:, 0])
    lines_filter.set_ydata(lowpass(plotdata, cutoff=cutoff_value, sample_rate=SAMPLE_RATE)[:, 0])
    threshold_line.set_ydata([threshold_value]*length)
    # lines_output.set_ydata(hit_detection(plotdata, threshold=AMPLITUDE_THRESHOLD))
    
    return [lines_input, threshold_line, lines_filter]#, lines_output]

000000000000000000000000000000000000000.
## Save audio settings
def save_settings_in_file(location=f"/media/pi/USB DAMIEN"):
    config_file_name = "config.csv"
    config_file = f"{location}/{config_file_name}"
    with open(config_file, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerows([
            ["device_name", device_name.value],
            ["cutoff_Hz", int(cutoff.value)],
            ["threshold", float(threshold.value)],
            ["rec_duration_seconds", 60],
            ["sample_rate_Hz", 44100]])

def choose_location_to_save():
    location = filedialog.askdirectory()
    if location:
        return location
    else:
        return None
        dialog.destroy

## Tkinter update functions

def update_cutoff(val):
    global cutoff_value
    cutoff_value = int(slider_cutoff.get())
    cutoff_label.config(text=f"Cutoff: {cutoff_value: ^4} Hz")
    
def update_threshold(val):
    global threshold_value
    threshold_value = slider_threshold.get()
    threshold_label.config(text=f"Threshold: {round(slider_threshold.get(), 2):.2f}")

def update_window_size_label(event):
    size_label.config(text=f"{window.winfo_width()} x {window.winfo_height()} pixels")
    
def device_selection_changed():
    global stream
    device_selected = device_var.get()
    device_selected_id = input_devices_id[input_devices_names.index(device_selected)]
#     print(f"Device selected: {device_selected} (id: {device_selected_id})")
    try:
        stream.stop()
        stream.close()
        stream.abort()
        stream = sd.InputStream(device=device_selected_id, callback=audio_callback)
        stream.start()
    except sd.PortAudioError:
#         print("device selection failed")
        tk.messagebox.showwarning("Error", "An error occurred when changing device.\nPlease try again.")

def close_setup():
    '''
    print(
        "\n----------------------------\n"
        f"\033[1mDevice\033[0m: {device_var.get()}\n"
        f"\033[1mCutoff\033[0m: {int(slider_cutoff.get())} Hz\n"
        f"\033[1mThreshold\033[0m: {round(slider_threshold.get(), 2)}"
        "\n----------------------------"
    )'''
    device.value = input_devices_id[input_devices_names.index(device_var.get())]
    device_name.value = device_var.get()
    cutoff.value = int(slider_cutoff.get())
    threshold.value = slider_threshold.get()

    location = choose_location_to_save()
    if location != None:
        save_settings_in_file(location=location)
    
    stream.stop()
    stream.close()
    plt.close()
    window.destroy()


def validate():    
    config_data = [
        ("Device", device_var.get()),
        ("Cutoff", f"{int(slider_cutoff.get())} Hz"),
        ("Threshold", f"{round(slider_threshold.get(), 2)}")
    ]
    global dialog
    dialog = tk.Toplevel(window, bg=BACKGROUND_COLOR)
    dialog.title("Configuration check")
    
    tree = ttk.Treeview(dialog, columns=["Parameter", "Value"], show="headings")
    tree.heading("Parameter", text="Parameter")
    tree.heading("Value", text="Value")
    
    for param, value in config_data:
        tree.insert("", "end", values=(param, value))
    
    tree.configure(height=len(config_data))
    tree.column("Parameter", width=100)
    tree.column("Value", width=270)
    tree.pack(padx=20, pady=5, fill="both")

    tk.Button(dialog, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=10, pady=10)
    tk.Button(dialog, text="Ok", command=close_setup).pack(side=tk.RIGHT, padx=0, pady=10)
    tk.Label(dialog, text="Continue?", bg=BACKGROUND_COLOR).pack(side=tk.RIGHT, padx=10, pady=10)
    
    return int(slider_threshold.get())
    


### TKINTER INIT ==================================================================================

# Tkinter window and main frame
window = tk.Tk()
SCREEN_WIDTH = window.winfo_screenwidth()
SCREEN_HEIGHT = window.winfo_screenheight()

window.geometry(f'{int(SCREEN_WIDTH*0.8)}x{int(SCREEN_HEIGHT*0.8)}')
window.title("Microphone Test & Calibration")
window.configure(bg='white')
frame = tk.Frame(window, bg='white')
frame.pack(expand=True)

# Display constants
BACKGROUND_COLOR = 'snow2'
FONT = ('Consolas', 12)
style = ttk.Style()
style.configure("Custom.TRadiobutton", background=BACKGROUND_COLOR)

MAX_CUTOFF = 10000
MIN_CUTOFF = 50
cutoff_value = 300
threshold_value = 0.5



### AUDIO =========================================================================================

SAMPLE_RATE = 44100	# samples per second
DOWNSAMPLE = 10 	# display every Nth sample (seconds)
WINDOW = 1000#500 		# visible time slot (milliseconds)
INTERVAL = 30 		# minimum time between plot updates (milliseconds)
CHANNELS = [1] 		# input channels to plot

q = queue.Queue()

length = int(WINDOW * SAMPLE_RATE / (100 * DOWNSAMPLE))
plotdata = np.zeros((length, len(CHANNELS)))

sd.default.channels = max(CHANNELS)
sd.default.samplerate = SAMPLE_RATE
stream = sd.InputStream(callback=audio_callback)



### PLOTS =========================================================================================

# Plot area in the Tkinter window
fig, (ax_input, ax_filter) = plt.subplots(2,1, sharex=True, figsize=(6,6))
fig.tight_layout(pad=2)
canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.draw()

# First subplot: input signal (microphone)
ax_input.set_title("Input signal")
lines_input = ax_input.plot(np.zeros_like(plotdata[:, 0]), label="Microphone signal")[0]
ax_input.legend()

# Second subplot: output of the low pass filter
ax_filter.set_title(f"Filtered signal")
lines_filter = ax_filter.plot(np.zeros_like(plotdata[:, 0]), color="green", label=f"Low pass filter output")[0]
threshold_line = ax_filter.plot([threshold_value]*length, color="orange", linestyle='--', label="Amplitude threshold")[0]
    #ax_filter.axhline(y=threshold_value, color="orange", linestyle='--', label="Amplitude threshold")
ax_filter.legend()

# Third subplot: only detected hits
'''
ax_output.set_title("Output signal")
lines_output = ax_output.plot(np.zeros_like(plotdata[:, 0]), color="red", label="Hits detected")[0]
ax_output.legend()
'''

# Subplots formatting
for ax in [ax_input, ax_filter]: #, ax_output]:
    ax.axis((0, len(plotdata), -1, 1))
    ax.set_yticks([0])
    ax.tick_params(bottom=False, top=False, labelbottom=False, right=False, left=False, labelleft=False)
# ax_output.set_ylim(-0.1, 1.3)
    


### TKINTER WIDGETS ===============================================================================

options_frame = tk.Frame(frame, bg=BACKGROUND_COLOR, borderwidth=1, relief='solid', padx=20, pady=20)

# Cutoff adjustment 
slider_cutoff = tk.Scale(options_frame, from_=MIN_CUTOFF, to=MAX_CUTOFF,
                         length=300, orient=tk.HORIZONTAL, relief='ridge',
                         command=update_cutoff, resolution=50, showvalue=False)
slider_cutoff.set(value=cutoff_value)
cutoff_label = tk.Label(options_frame, text=f"Cutoff: {slider_cutoff.get(): ^4} Hz", font=FONT, bg=BACKGROUND_COLOR)

# Threshold adjustment
slider_threshold = tk.Scale(options_frame, from_=0, to=0.95,
                            length=300, orient=tk.HORIZONTAL, relief='ridge',
                            command=update_threshold, resolution=0.05, showvalue=False)
slider_threshold.set(threshold_value)
threshold_label = tk.Label(options_frame, text=f"Threshold: {round(slider_threshold.get(), 2):.2f}", font=FONT, bg=BACKGROUND_COLOR)

# Device selection

devices_frame = tk.Frame(options_frame, bg=BACKGROUND_COLOR)
input_devices_names, input_devices_id = get_input_devices_list()
device_var = tk.StringVar(value=input_devices_id.index(stream.device))
initial_device = input_devices_names[input_devices_id.index(stream.device)]
device_var.set(initial_device)

for i, device in enumerate(input_devices_names):
    radio_btn = ttk.Radiobutton(devices_frame, text=device,
                                variable=device_var, value=device,
                                command=device_selection_changed, style="Custom.TRadiobutton")
    radio_btn.pack(anchor=tk.W)

ok_button = tk.Button(options_frame, text="Continue with this configuration", command=validate)

# Window size info
size_label = tk.Label(options_frame, text="")
window.bind("<Configure>", update_window_size_label)



### TKINTER FRAMES ================================================================================

# Main frame
options_frame.grid(row=0, column=0, padx=(30,0))
canvas.get_tk_widget().grid(row=0, column=1)

# Options frame
cutoff_label.pack(pady=(5,10))
slider_cutoff.pack()
threshold_label.pack(pady=(40,10))
slider_threshold.pack()
tk.Label(options_frame, text="Device selection", font=FONT, bg=BACKGROUND_COLOR).pack(pady=(40, 10))
devices_frame.pack()
ok_button.pack(pady=(20,0))
# size_label.pack()



### SHARE DATA WITH OTHER PROGRAMS ================================================================
device = mpr.Value('i')
device_name = mpr.Value(ctypes.c_wchar_p)
cutoff = mpr.Value('i')
threshold = mpr.Value('d')



### LOOPS =========================================================================================

ani = FuncAnimation(fig, update_plot, interval=INTERVAL, blit=True, cache_frame_data=False)

with stream:
    window.mainloop()
