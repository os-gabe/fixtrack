import argparse
import sys

from IPython import get_ipython
from PyQt5.QtWidgets import QApplication

from fixtrack.frontend.gui import FixtrackWindow

# If we are running ipython interactive we have to set the gui to qt5
ipython = get_ipython()
if ipython is not None:
    ipython.magic("%gui qt5")

parser = argparse.ArgumentParser()
parser.add_argument("--video", type=str, default=None, help="Video file name")
parser.add_argument("--track", type=str, default=None, help="Track H5 file name")

args = parser.parse_args()

app = QApplication(sys.argv)

main_win = FixtrackWindow(args.video, args.track)
main_win.show()
sys.exit(app.exec_())
