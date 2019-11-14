import pyinotify
import argparse
import subprocess
import time
import os
import shlex
import threading

parser = argparse.ArgumentParser(description='REIP video capture')
parser.add_argument('--indir', type=str, help='Input directory')
parser.add_argument('--outdir', type=str, help='Output directory')
parser.add_argument('--device', type=str, help='Device path, eg /dev/videoX or USB port path')
parser.add_argument('--width', type=int, help='Width in pixels')
parser.add_argument('--height', type=int, help='Height in pixels')
parser.add_argument('--fps', type=int, help='Frames per second')
parser.add_argument('--bitrate_kbs', type=int, help='Bitrate in kbps')
parser.add_argument('--file_length_seconds', type=int, help='Output file length in seconds')

# Example:
# python2 video_capture.py --indir /home/reip/video_capture/src --outdir /mnt/reipdata --device /dev/video0 --width 2592 --height 1944 --fps 15 --bitrate_kbs 1500 --file_length_seconds 10

wm = pyinotify.WatchManager()

mask = pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE

args = parser.parse_args()

indir = args.indir
outdir = args.outdir
device = args.device
width = args.width
height = args.height
fps = args.fps
bitrate_kbs = args.bitrate_kbs
file_length_seconds = args.file_length_seconds

file_info = {}


def video_capture(device, width, height, fps, bitrate_kbs, outfname, file_length_seconds):
	gstr = return_gstreamer_string(device, width, height, fps, bitrate_kbs, outfname, file_length_seconds)
	record_proc = subprocess.Popen(shlex.split(gstr), stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
	outs, errs = record_proc.communicate()

def get_video_length(filename):
	result = subprocess.Popen(["ffprobe", filename],
    stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
	return [x for x in result.stdout.readlines() if "Duration" in x]


def return_gstreamer_string(device, width, height, fps, bitrate_kbs, outfname, file_length_seconds):
	gstr = 	'gst-launch-1.0 -e v4l2src device=%s ! ' \
			'"image/jpeg, width=%d, height=%d, framerate=%d/1" ! ' \
			'jpegdec ! ' \
			'nvvidconv ! ' \
			'"video/x-raw(memory:NVMM), format=(string)I420" ! ' \
			'omxh264enc iframeinterval=1 bitrate=%d ! ' \
			'"video/x-h264, stream-format=(string)byte-stream" ! ' \
			'h264parse ! ' \
			'splitmuxsink location=%s%%d.mp4 max-size-time=%d' \
			% (device, width, height, fps, bitrate_kbs * 1000, outfname, file_length_seconds * 1000000000)
	return gstr


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        if event.pathname.endswith(".mp4"):
			fname = os.path.basename(event.pathname)
			os.rename(event.pathname, 'out_%d.mp4' % file_info[fname])
			del file_info[fname]

    def process_IN_CREATE(self, event):
        if event.pathname.endswith(".mp4"):
            fname = os.path.basename(event.pathname)
            file_info[fname] = os.path.getmtime(event.pathname)
            print(file_info)


if __name__ == "__main__":
	notifier = pyinotify.AsyncNotifier(wm, EventHandler())
	wdd = wm.add_watch(indir, mask)
	
	outfname = 'out_1'
	cap_thread_1 = threading.Thread(target = video_capture, args = (device, width, height, fps, bitrate_kbs, outfname, file_length_seconds))
	cap_thread_1.start()

	notifier.loop()
	cap_thread_1.join()
    
