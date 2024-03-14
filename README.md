# Introduction
## Context
This project is a sound-based quality control tool designed for a roof tiles production line.<br>
It takes the form of a box which:
- is connected to a microphone in order to record audio
- has a little LED screen for giving the user some feedback
- has two push buttons (a red one and a green one) which are the user input
 
<img src="./images/project summary.png" alt="images of the components" width="800">



## Table of Contents
<!-- TOC -->

- [Introduction](#introduction)
  - [Context](#context)
  - [Table of Contents](#table-of-contents)
- [How to setup this project](#how-to-setup-this-project)
  - [Hardware requirements](#hardware-requirements)
  - [Software configuration](#software-configuration)
    - [1. Install Raspberry Pi OS Lite (64-bit)](#1-install-raspberry-pi-os-lite-64-bit)
    - [2. Set up remote access via SSH](#2-set-up-remote-access-via-ssh)
    - [3. Enable I2C](#3-enable-i2c)
    - [4. Install Git](#4-install-git)
    - [5. Get the project and the dependencies](#5-get-the-project-and-the-dependencies)
- [How to use this project](#how-to-use-this-project)
  - [User feedback - LED screen](#user-feedback---led-screen)
    - [Normal use](#normal-use)
    - [Edge cases](#edge-cases)
  - [User input - push buttons](#user-input---push-buttons)
  - [Custom settings](#custom-settings)

<!-- /TOC -->


# How to setup this project
## Hardware requirements

- a Raspberry Pi (I’m using a [Pi 4 model B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/))
    - a USB-C cable for power supply
    - a micro HDMI cable and a screen for configuration
- a [Raspberry Sense HAT](https://www.raspberrypi.com/products/sense-hat/)
- a microphone with a USB interface, here’s my setup:
    - I’m using the [MEK 600 Shotgun Microphone](https://www.sennheiser.com/en-us/catalog/products/microphones/mke-600/mke-600-505453) from Sennheiser
    - I’m also using a 18V AC phantom supply (the [MPS 500 Dual Phantom Supply](https://www.bax-shop.fr/alimentation-fantome/devine-mps-500-alimentation-fantome) from Devine)
    - 2 female male XLR cables (like [this one](https://www.bax-shop.fr/cables-xlr/devine-mic100-1-5-cable-micro-signal-xlr-1-5-metre))
    - a XLR to USB converter (I’m using the [MicCon interface XLR - USB](https://www.bax-shop.fr/carte-son-externe/devine-miccon-interface-xlr-usb) also from Devine)
- 2 push buttons
- a USB storage device (I’m using a classic USB stick)

---

## Software configuration

### 1. Install Raspberry Pi OS Lite (64-bit)

1. Format the SD card using the [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Downloading the OS image (you can find it [here](https://www.raspberrypi.com/software/operating-systems/))
3. Still on the Raspberry Pi Imager, while selecting OS, chose “Use custom” and select the image you just downloaded
4. Select “Change settings”. From there you can already configure WiFi and enable SSH (select “Use a password for authentication”). I also recommend to set a username and a password (keep these somewhere!).

### 2. Set up remote access via SSH

> For this part you will need a screen connected to your Pi
> 
1. Connect the screen and power the Pi
2. To find the IP address, run
    
    ```bash
    hostname -I
    
    # Other way to find the IP address:
    ip a 
    # search for “wlan0”, then next to “inet” you have the IP address
    ```
    
    Note that address!
    
    > If you didn’t configure WiFi with the Raspberry Pi Imager, you can still do it now :
    > 
    > 1. Run
    >     
    >     ```bash
    >     sudo raspi-config
    >     ```
    >     
    > 2. Go to “Interface Options”
    > 3. Go to “System Options”
    > 4. Go to “Wireless LAN”
    > 5. Follow the instructions
    > 6. Check if your WiFi network has been added correctly by running
    >     
    >     ```bash
    >     iwconfig
    >     ```
    >     
    >     You should see it among the list.
    >     
    
    > Same if you didn’t enable SSH with the Raspberry Pi Imager :
    > 
    > 1. Run
    >     
    >     ```bash
    >     sudo raspi-config
    >     ```
    >     
    > 2. Go to “Interface Options”
    > 3. Go to “SSH”
    > 4. Follow the instructions to enable SSH
3. Check if you can access your Pi via SSH
    
    Open a terminal and run
    
    ```bash
    ssh username@ip_address # replace with your info
    ```
    

If you have trouble while setting up the remote access, check [the official documentation](https://www.raspberrypi.com/documentation/computers/remote-access.html).

Once remote access is set up, you don’t need a screen for the Pi anymore, everything can be done remotely.

### 3. Enable I2C

> I2C interface needs to be enable in order to communication with the [Sense HAT](https://www.raspberrypi.com/products/sense-hat/)
> 
1. Run
    
    ```bash
    sudo raspi-config
    ```
    
2. Go to “Interface Options”
3. Go to “I2C”
4. Follow th instruction to enable I2C

### 4. Install Git

Start by

```bash
sudo apt update
sudo apt upgrade
```

Then run

```bash
sudo apt install git
```

Check if git is correctly installed

```bash
git --version
```

### 5. Get the project and the dependencies

Install the development tools

```bash
sudo apt-get install python3-dev

# Check if it's installed
apt list --installed
```

Clone the git repository

```bash
git clone --recursive https://github.com/Damien-Bureau/roof-tiles-quality-control.git
```

Create a virtual environment and install the dependencies

```bash
# Go to the project folder
cd roof-tiles-quality-control

# Create a python venv named "venv"
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the dependencies
pip install -r requirements.txt
```

The [RTIMU library](https://github.com/RPi-Distro/RTIMULib), which is a dependency of [Sense HAT](https://sense-hat.readthedocs.io/en/latest/), needs manual setup

```bash
cd venv
git clone --recursive https://github.com/RPi-Distro/RTIMULib.git

cd RTIMULib/Linux/python
python setup.py build
python setup.py install
```

Same for PortAudio, which is a dependency of [sounddevice](https://python-sounddevice.readthedocs.io/en/0.4.6/#), needs manual operations

```bash
# Go to the portaudio folder
cd
cd roof-tiles-quality-control/portaudio

# Operations
./configure && make
sudo make install
sudo ldconfig

# Go back to the project main folder
cd ..

```
> Source [here](https://stackoverflow.com/questions/59006083/how-to-install-portaudio-on-pi-properly)

# How to use this project

## User feedback - LED screen

### Normal use

### Edge cases


## User input - push buttons


## Custom settings
[setup_audio_device.py](./setup_audio_device.py)
<br>
`config.csv`
