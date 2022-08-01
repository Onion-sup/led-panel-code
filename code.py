# SPDX-FileCopyrightText: 2020 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# This example implements a simple two line scroller using
# Adafruit_CircuitPython_Display_Text. Each line has its own color
# and it is possible to modify the example to use other fonts and non-standard
# characters.

import time
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_requests as requests
import board
from digitalio import DigitalInOut
import displayio
import framebufferio
import rgbmatrix
import busio
from pipeline_status_watcher import *
from secrets import secrets
from get_a_message import GetAMessage

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=128, height=64, bit_depth=1,
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2
    ],
    addr_pins=[
        board.MTX_ADDRA,
        board.MTX_ADDRB,
        board.MTX_ADDRC,
        board.MTX_ADDRD
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE,
    tile=2
    )
# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

print("Connecting to AP...")
while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)

socket.set_interface(esp)
requests.set_socket(socket, esp)

# # Associate the RGB matrix with a Display so that we can use displayio features
display = framebufferio.FramebufferDisplay(matrix)
display_group = displayio.Group()
pipeline_status_watcher = PipelineStatusWatcher(display_group)
get_a_message = GetAMessage(display_group)
display.show(display_group)

elapsed_t = 0

scroll_pipeline_period = 0.5
scroll_message_period = 0.05
update_period = 6
display_refresh_period = 0.01

cnt_scroll_pipeline = 0
cnt_scroll_message = 0
cnt_update = 0

while True:

    if cnt_scroll_pipeline >= scroll_pipeline_period/display_refresh_period:
        pipeline_status_watcher.scroll()
        cnt_scroll_pipeline = 0

    if cnt_scroll_message >= scroll_message_period/display_refresh_period:
        get_a_message.scroll_text()
        cnt_scroll_message = 0
        
    if cnt_update >= update_period/display_refresh_period:
        pipeline_status_watcher.update()
        get_a_message.update()
        cnt_update = 0

    cnt_scroll_pipeline += 1
    cnt_scroll_message += 1
    cnt_update += 1

    time.sleep(display_refresh_period)
