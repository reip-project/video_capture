# import asyncore
import pyinotify
import argparse
import time

parser = argparse.ArgumentParser(description='REIP video capture')
parser.add_argument('--folder', type=str, help='Output folder')

wm = pyinotify.WatchManager()
inclose_mask = pyinotify.IN_CLOSE_WRITE
open_mask = pyinotify.OPEN

args = parser.parse_args()

MONITOR_DIR = args.folder


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        if event.pathname.endswith(".mp4"):
            print("close write")

    def process_OPEN(self, event):
        if event.pathname.endswith(".mp4"):
            print("open write")


if __name__ == "__main__":
    notifier = pyinotify.AsyncNotifier(wm, EventHandler())
    wdd_inclose = wm.add_watch(MONITOR_DIR, inclose_mask, auto_add=True)
    wdd_open = wm.add_watch(MONITOR_DIR, open_mask, auto_add=True)

    # asyncore.loop()
