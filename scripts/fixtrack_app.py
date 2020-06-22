import argparse
import sys

# import matplotlib
from IPython import get_ipython
from PyQt5.QtWidgets import QApplication

from fixtrack.frontend.gui import FixtrackWindow

# If we are running ipython interactive we have to set the gui to qt5
ipython = get_ipython()
if ipython is not None:
    ipython.magic("%gui qt5")

# # Make sure that we are using QT5
# matplotlib.use('Qt5Agg')

parser = argparse.ArgumentParser()
parser.add_argument("--video", type=str, default=None, help="Video file name")
parser.add_argument("--track", type=str, default=None, help="Track H5 file name")
parser.add_argument("--frame-rate", type=float, default=30.0, help="Frame rate of the video")
parser.add_argument(
    "--estimate-heading",
    action="store_true",
    help="Estimate heading from direction of travel rather than using the value from the track"
)

args = parser.parse_args()

# qApp = QApplication(sys.argv)
# aw = FixtrackWindow(args.video, args.track, args.frame_rate)

# aw.setWindowTitle("FixTrack")
# aw.show()
# sys.exit(qApp.exec_())

app = QApplication(sys.argv)

main_win = FixtrackWindow(
    args.video, args.track, args.frame_rate, estimate_heading=args.estimate_heading
)
main_win.show()
sys.exit(app.exec_())
