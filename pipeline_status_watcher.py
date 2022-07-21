import time
import displayio
import adafruit_display_text.label
from adafruit_bitmap_font import bitmap_font
import adafruit_requests as requests
from secrets import secrets
import microcontroller

BLACK = 'black'
PENDING = "pending"
RUNNING = 'running'
SUCCESS = 'success'
FAILED = 'failed'
CANCELED = 'canceled'

BLACK_COLOR = 0x000000
PENDING_COLOR = 0xffff00
RUNNING_COLOR = 0x0000ff
SUCCESS_COLOR = 0x00ff00
FAILED_COLOR = 0xff0000
CANCELED_COLOR = 0xffffff

color_index_map = {
    BLACK: 0,
    PENDING: 1,
    RUNNING: 2,
    SUCCESS: 3,
    FAILED: 4,
    CANCELED: 5
}
class PipelineStatusWatcher:
    def __init__(self, display_group):
        self.cnt = 0
        self.prev_fetch_update_counter = -1
        # Initialize a requests object with a socket and esp32spi interface
        self.fetch_url = secrets['led_panel_service_host'] + "/api/gitlab-pipeline"

        # JSON_GET_URL = "http://httpbin.org/get"

        # # Define a custom header as a dict.
        # headers = {"user-agent": "blinka/1.0.0"}

        # print("Fetching JSON data from %s..." % JSON_GET_URL)
        # response = requests.get(JSON_GET_URL, headers=headers)
        # print("-" * 60)

        # json_data = response.json()
        # headers = json_data["headers"]
        # print("Response's Custom User-Agent Header: {0}".format(headers["User-Agent"]))
        # print("-" * 60)

        # # Read Response's HTTP status code
        # print("Response HTTP Status Code: ", response.status_code)
        # print("-" * 60)
        # response.close()

        # Create a bitmap with two colors
        font = bitmap_font.load_font("tom-thumb.bdf")

        # Create a two color palette
        palette = displayio.Palette(len(color_index_map))
        palette[color_index_map[BLACK]] = BLACK_COLOR
        palette[color_index_map[PENDING]] = PENDING_COLOR
        palette[color_index_map[RUNNING]] = RUNNING_COLOR
        palette[color_index_map[SUCCESS]] = SUCCESS_COLOR
        palette[color_index_map[FAILED]] = FAILED_COLOR
        palette[color_index_map[CANCELED]] = CANCELED_COLOR

        self.repository_name_text = adafruit_display_text.label.Label(
            font,
            color=0xffffff,
            text="null")
        self.repository_name_text.x = 0
        self.repository_name_text.y = 3

        self.branch_name_text = adafruit_display_text.label.Label(
            font,
            color=0xffffff,
            text="null")
        self.branch_name_text.x = 0
        self.branch_name_text.y = 10
        self.jobs_lists = []
        x_jobs_status_tile_grid = 0
        y_jobs_status_tile_grid = 15
        width_jobs_status_tile_grid = 64
        height_jobs_status_tile_grid = 32-y_jobs_status_tile_grid-7
        self.display_width = 64
        self.jobs_status_tile_grid = JobsStatusTileGrid(x_jobs_status_tile_grid, y_jobs_status_tile_grid, width_jobs_status_tile_grid, height_jobs_status_tile_grid, palette)

        # Put each line of text into a Group, then show that group.
        pipeline_watcher_group = displayio.Group()
        pipeline_watcher_group.append(self.jobs_status_tile_grid.tile_grid)
        pipeline_watcher_group.append(self.repository_name_text)
        pipeline_watcher_group.append(self.branch_name_text)
        display_group.append(pipeline_watcher_group)

    def scroll(self):
        # text_width = self.repository_name_text.bounding_box[2]
        # if text_width > self.display_width:
        #     self.repository_name_text.x = self.repository_name_text.x - 1
        #     if self.repository_name_text.x < -text_width:
        #         self.repository_name_text.x = self.display_width
        # else:
        #     self.repository_name_text.x = 0
        # text_width = self.branch_name_text.bounding_box[2]
        # if text_width > self.display_width:
        #     self.branch_name_text.x = self.branch_name_text.x - 1
        #     if self.branch_name_text.x < -text_width:
        #         self.branch_name_text.x = self.display_width
        # else:
        #     self.branch_name_text.x = 0
        self.jobs_status_tile_grid.scroll()


    def update(self):
        prev_jobs_lists = self.jobs_lists
        self.cnt += 1
        self.repository_name_text.text += '...'
        try:
            response = requests.get(self.fetch_url)
            json_data = response.json()
        except RuntimeError as e:
            self.repository_name_text.text = 'e: ' + str(e)
            time.sleep(3)
            microcontroller.reset()
        print("[update] {} {}".format(response.status_code, json_data))
        response.close()
        self.repository_name_text.text = json_data['repository_name']
        self.branch_name_text.text = json_data['branch_name'] + ' ' + str(self.cnt)
        self.jobs_lists = []
        for stage in json_data['stages'].values():
            jobs = [Job(list(job.values())[0]) for job in stage]
            self.jobs_lists.append(jobs)
        if self.prev_fetch_update_counter == json_data['update_counter']:
            self.repository_name_text.text = 'server'
            self.branch_name_text.text = 'did not update'
        self.prev_fetch_update_counter = json_data['update_counter']

        self.jobs_status_tile_grid.clean_jobs(prev_jobs_lists)
        self.jobs_status_tile_grid.render(self.jobs_lists)
            
class JobsStatusTileGrid:
    def __init__(self, x, y, width, height, palette):
        self.width = width
        self.height = height
        self.bitmap = displayio.Bitmap(width, height, len(color_index_map))
        # Create a TileGrid using the Bitmap and Palette
        self.tile_grid = displayio.TileGrid(self.bitmap, pixel_shader=palette)
        self.tile_grid.x = x
        self.tile_grid.y = y
        self.job_pellet_width = 2
        self.job_pellet_height = 1
        self.horiz_space = 2
        self.vert_space = 3
        self.jobs_lists = None
        self.scroll_x = 0
        self.scroll_y = 0

    def clean_jobs(self, jobs_lists):
        x_shift = self.job_pellet_width + self.horiz_space
        y_shift = self.job_pellet_height + self.vert_space
        for stage_index in range(len(jobs_lists)):
            for job_index in range(len(jobs_lists[stage_index])):
                for x in range(job_index*x_shift, job_index*x_shift + self.job_pellet_width):
                    for y in range(stage_index*y_shift, stage_index*y_shift + self.job_pellet_height):
                        x += self.scroll_x
                        y += self.scroll_y
                        if x >=0 and x < self.width and y >=0 and y < self.height:
                            self.bitmap[x, y] = color_index_map[BLACK]


    def render(self, jobs_lists):
        self.jobs_lists = jobs_lists
        x_shift = self.job_pellet_width + self.horiz_space
        y_shift = self.job_pellet_height + self.vert_space
        for stage_index in range(len(jobs_lists)):
            for job_index in range(len(jobs_lists[stage_index])):
                for x in range(job_index*x_shift, job_index*x_shift + self.job_pellet_width):
                    for y in range(stage_index*y_shift, stage_index*y_shift + self.job_pellet_height):
                        x += self.scroll_x
                        y += self.scroll_y
                        if x >=0 and x < self.width and y >=0 and y < self.height:
                            self.bitmap[x, y] = color_index_map[jobs_lists[stage_index][job_index].status]

    def scroll(self):
        if self.jobs_lists == None:
            return
        self.clean_jobs(self.jobs_lists)
        width_jobs_x = max([(self.job_pellet_width + self.horiz_space) * len(jobs) for jobs in self.jobs_lists])
        width_jobs_y = (self.job_pellet_height + self.vert_space) * len(self.jobs_lists)
        if width_jobs_x > self.width:
            self.scroll_x -= 1
            if self.scroll_x < -self.width:
                self.scroll_x = self.width
        else:
            self.scroll_x = 0
        if width_jobs_y > self.height:
            self.scroll_y -= 1
            if self.scroll_y < -self.height:
                self.scroll_y = self.height
        else:
            self.scroll_y = 0

        self.render(self.jobs_lists)

class Job:
    def __init__(self, status):
        self.status = status
