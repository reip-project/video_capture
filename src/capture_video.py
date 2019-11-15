import pyinotify
import argparse
import subprocess
import time
import os
import shlex
import threading
import socket
import fcntl
import struct

parser = argparse.ArgumentParser(description='REIP video capture')
parser.add_argument('--indir', type=str, help='Input directory')
parser.add_argument('--outdir', type=str, help='Output directory')
parser.add_argument('--devices', type=str, help='Device path, eg /dev/videoX or USB port path (can be a list for multi camera setups)')
parser.add_argument('--width', type=int, help='Width in pixels')
parser.add_argument('--height', type=int, help='Height in pixels')
parser.add_argument('--fps', type=int, help='Frames per second')
parser.add_argument('--bitrate_kbs', type=int, help='Bitrate in kbps')
parser.add_argument('--file_length_seconds', type=int, help='Output file length in seconds')
parser.add_argument('--eth_name', type=str, help='Name of ethernet adaptor on device or container, eg. eth0')

# Example:
# python2 video_capture.py --indir /home/reip/video_capture/src --outdir /mnt/reipdata --device /dev/video0 --width 2592 --height 1944 --fps 15 --bitrate_kbs 1500 --file_length_seconds 10 --eth_name eth0

wm = pyinotify.WatchManager()

mask = pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE

args = parser.parse_args()

indir = args.indir
outdir = args.outdir
devices = [item for item in args.devices.split(',')]
width = args.width
height = args.height
fps = args.fps
bitrate_kbs = args.bitrate_kbs
file_length_seconds = args.file_length_seconds
eth_name = args.eth_name

file_info = {}


def gethwaddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
    return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1].replace(':', '')

def video_capture(device, width, height, fps, bitrate_kbs, outfname, file_length_seconds):
	gstr = return_gstreamer_string(device, width, height, fps, bitrate_kbs, outfname, file_length_seconds)
	record_proc = subprocess.Popen(shlex.split(gstr), stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
	outs, errs = record_proc.communicate()
	exit()

def get_video_length(filename):
	result = subprocess.Popen(["ffprobe", filename],
    stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
	return [x for x in result.stdout.readlines() if "Duration" in x]


def return_gstreamer_string(device, width, height, fps, bitrate_kbs, outfname, file_length_seconds):
	print(os.path.join(tmp_out_path, outfname))
	gstr = 	'gst-launch-1.0 -e v4l2src device=%s ! ' \
			'"image/jpeg, width=%d, height=%d, framerate=%d/1" ! ' \
			'jpegdec ! ' \
			'nvvidconv ! ' \
			'"video/x-raw(memory:NVMM), format=(string)I420" ! ' \
			'omxh264enc iframeinterval=1 bitrate=%d ! ' \
			'"video/x-h264, stream-format=(string)byte-stream" ! ' \
			'h264parse ! ' \
			'splitmuxsink location=%s/out_%%d.mp4 max-size-time=%d' \
			% (device, width, height, fps, bitrate_kbs * 1024, os.path.join(tmp_out_path, outfname), file_length_seconds * 1000000000)
	return gstr


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        if event.pathname.endswith(".mp4"):
			path_parts = os.path.normpath(event.pathname).split(os.sep)
			dev_dir = path_parts[-2]
			fname = os.path.basename(event.pathname)
			os.rename(event.pathname, os.path.join(sd_out_path, dev_dir, '%s_%.3f.mp4' % (dev_dir, file_info[fname])))
			del file_info[fname]

    def process_IN_CREATE(self, event):
        if event.pathname.endswith(".mp4"):
            fname = os.path.basename(event.pathname)
            file_info[fname] = os.path.getmtime(event.pathname)
            print(file_info)

sd_out_path = os.path.join(outdir, gethwaddr(eth_name))
tmp_out_path = os.path.join(indir, gethwaddr(eth_name))

if __name__ == "__main__":
	
	
	if not os.path.exists(sd_out_path):
		os.makedirs(sd_out_path)

	if not os.path.exists(tmp_out_path):
		os.makedirs(tmp_out_path)

	notifier = pyinotify.AsyncNotifier(wm, EventHandler())
	wdd = wm.add_watch(tmp_out_path, mask, rec=True, auto_add=True)

	print('TMP out path: %s' % tmp_out_path)
	print('SD out path: %s' % sd_out_path)


	dev_idx = 1
	cap_threads = []
	for device in devices:
		outtmpfname = os.path.join(tmp_out_path, 'out_%d' % dev_idx)
		outsdfname = os.path.join(sd_out_path, 'out_%d' % dev_idx)
		if not os.path.exists(outtmpfname):
			os.makedirs(outtmpfname)

		if not os.path.exists(outsdfname):
			os.makedirs(outsdfname)

		dev_idx += 1
		vid_thread = threading.Thread(target = video_capture, args = (device, width, height, fps, bitrate_kbs, outtmpfname, file_length_seconds))
		vid_thread.start()
		cap_threads.append(vid_thread)

	notifier.loop()

	for cap_thread in cap_threads:
		cap_thread.join()

	
	
