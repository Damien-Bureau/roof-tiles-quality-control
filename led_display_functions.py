import time as t
from sense_hat import SenseHat # LED matrix

RED_RGB = (255, 0, 0)
GREEN_RGB = (0, 255, 0)
ORANGE_RGB = (255, 100, 0)
VOID_RGB = (0, 0, 0)
WHITE_RGB = (255, 255, 255)

sense = SenseHat()
sense.clear()
sense.low_light = True


def led_fully_white():
    sense.set_pixels([WHITE_RGB]*64)

def led_fully_red():
    sense.set_pixels([RED_RGB]*64)

def led_white_cross():
    sense.clear()
    for i in range(8):
        sense.set_pixel(i,i, 255,255,255)
        sense.set_pixel(7-i,i, 255,255,255)


def led_circle(color):
    O = WHITE_RGB
    X = color
    matrix = [
        O, O, O, O, O, O, O, O,
        O, O, O, O, O, O, O, O,
        O, O, O, X, X, O, O, O,
        O, O, X, X, X, X, O, O,
        O, O, X, X, X, X, O, O,
        O, O, O, X, X, O, O, O,
        O, O, O, O, O, O, O, O,
        O, O, O, O, O, O, O, O]
    sense.set_pixels(matrix)


def led_outline(color):
    X = VOID_RGB
    O = WHITE_RGB
    C = color
    matrix = [
        O, O, O, O, O, O, O, O,
        O, O, C, C, C, C, O, O,
        O, C, C, X, X, C, C, O,
        O, C, X, X, X, X, C, O,
        O, C, X, X, X, X, C, O,
        O, C, C, X, X, C, C, O,
        O, O, C, C, C, C, O, O,
        O, O, O, O, O, O, O, O]
    sense.set_pixels(matrix)


def led_no_mic():
    X = RED_RGB
    O = VOID_RGB
    C = WHITE_RGB
    matrix = [
        O, O, O, C, C, O, O, X,
        O, O, O, C, C, O, X, O,
        O, C, O, C, C, X, C, O,
        O, C, O, C, X, O, C, O,
        O, C, O, X, O, O, C, O,
        O, O, X, C, C, C, O, O,
        O, X, O, C, C, O, O, O,
        X, O, C, C, C, C, O, O]
    sense.set_pixels(matrix)


def led_no_storage_device():
    X = RED_RGB
    O = VOID_RGB
    C = WHITE_RGB
    matrix = [
        O, O, O, C, C, O, O, X,
        O, O, O, C, C, O, X, O,
        O, O, O, C, C, X, O, O,
        O, C, O, C, X, O, C, O,
        O, O, C, X, C, C, O, O,
        C, O, X, C, C, O, O, C,
        C, X, O, O, O, O, O, C,
        X, C, C, C, C, C, C, C]
    sense.set_pixels(matrix)


def led_writing_error():
    X = ORANGE_RGB
    O = VOID_RGB
    C = WHITE_RGB
    matrix = [
        O, O, O, C, C, O, O, O,
        O, O, O, C, C, O, O, O,
        O, O, O, C, C, O, O, O,
        O, C, O, C, C, O, C, O,
        O, O, C, C, C, C, O, O,
        X, O, O, C, C, O, O, X,
        X, O, O, O, O, O, O, X,
        X, X, X, X, X, X, X, X]
    sense.set_pixels(matrix)


def led_error_animation(error):
    if error == "mic":
        image = led_no_mic
    elif error == "storage":
        image = led_no_storage_device
    elif error == "writing":
        image = led_writing_error
    led_fully_red()
    t.sleep(0.5)
    image()
    t.sleep(1)
