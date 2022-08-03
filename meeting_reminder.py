from secrets import secrets
import time
import adafruit_display_text.label
from adafruit_bitmap_font import bitmap_font
import displayio
import adafruit_requests as requests
import microcontroller

class MeetingReminder:
    def __init__(self, display_group):
        font = bitmap_font.load_font("tom-thumb.bdf")
        self.fetch_url = secrets['led_panel_service_host'] + "/api/get-next-meetings"
        self.message = "null"
        self.display_width = 64
        self.display_height = 32
        self.text = adafruit_display_text.label.Label(
            font,
            color=0x0000ff,
            text=self.message,
            x=0,
            y=self.display_height - 6 + 3)
        group = displayio.Group()
        group.append(self.text)
        display_group.append(group)

    def scroll_text(self):
        text_width = self.text.bounding_box[2]
        if text_width > self.display_width:
            self.text.x = self.text.x - 1
            if self.text.x < -text_width:
                self.text.x = self.display_width
        else:
            self.text.x = 0

    def update(self):
        self.text.text += '...'
        try:
            response = requests.get(self.fetch_url)
            self.message = response.text
        except RuntimeError as e:
            self.text.text = 'e: ' + str(e)
            time.sleep(3)
            microcontroller.reset()
        response.close()
        self.text.text = self.message
