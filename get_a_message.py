from secrets import secrets
import adafruit_display_text.label
from adafruit_bitmap_font import bitmap_font
import displayio
import adafruit_requests as requests

class GetAMessage:
    def __init__(self, display_group):
        font = bitmap_font.load_font("tom-thumb.bdf")
        self.fetch_url = "https://"+ secrets['led_panel_service_host'] + "/api/post-a-message/get"
        self.message = "null"
        self.text = adafruit_display_text.label.Label(
            font,
            color=0x0000ff,
            text=self.message,
            x=0,
            y=32 - 5 + 3)
        group = displayio.Group()
        group.append(self.text)
        display_group.append(group)

    def update(self):
        try:
            response = requests.get(self.fetch_url)
            self.message = response.text
        except Exception as e:
            self.message = 'e:{}'.format(e)
        self.text.text = self.message
