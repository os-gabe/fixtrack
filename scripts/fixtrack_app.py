import argparse
import sys

from PyQt5.QtWidgets import QApplication

from fixtrack.frontend.fixtrack_gui import FixtrackWindow

parser = argparse.ArgumentParser()
parser.add_argument("--video", type=str, default=None, help="Video file name")
parser.add_argument("--track", type=str, default=None, help="Track H5 file name")
parser.add_argument("--frame-rate", type=float, default=30.0, help="Frame rate of the video")

args = parser.parse_args()

qApp = QApplication(sys.argv)
aw = FixtrackWindow(args.video, args.track, args.frame_rate)

aw.setWindowTitle("FixTrack")
aw.show()
sys.exit(qApp.exec_())
