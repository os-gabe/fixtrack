# Fixtrack
A fish tracking tool built on PyQt5 and VisPy.

**Languages**  
Python 3

### Clone
This README assumes the fixtrack repository is located on your computer under `~/code`. Clone this repo something like this
```bash
mkdir ~/code
cd ~/code
git clone git@github.com:os-gabe/fixtrack.git  # note, this will create ~/code/fixtrack
```

### Build

**Ubuntu Setup**

These instruction are for Ubuntu 18.04.

Install system wide dependencies; you'll probably need `sudo`.
```bash
apt update
apt upgrade
apt install python3-tk libsm6 pkg-config libpq-dev \
    libavformat-dev libavcodec-dev libavdevice-dev \
    libavutil-dev libswscale-dev libswresample-dev \
    libavfilter-dev libblas-dev ffmpeg python3-dev
```
I don't think all of these system dependencies are actually necessary but I have not had time to figure out which ones are or not. On a mac you would install these with Homebrew package manager https://brew.sh/ rather than apt.

**Python Environment**

Install virtualenvwrapper
```bash
apt install virtualenvwrapper
```
Set up virtualenvwrapper and your python paths by putting these at the end of your ~/.bashrc file. On a Mac you would edit `~/.bash_profile` rather than `~/.bashrc`.
Don't forget to source it or open a new terminal afterwards.
```
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
export WORKON_HOME=~/Envs

export CODE=~/code
export FIXTRACK=$CODE/fixtrack
export PYTHONPATH=$PYTHONPATH:$FIXTRACK
export WORKON_FIXTRACK="workon fixtrack"

alias cdfixtrack="cd $FIXTRACK"
alias wf=$WORKON_FIXTRACK

```

Once virtualenvwrapper is installed, you can create the virtual environment
called `fixtrack` by follow these instructions.
```bash
mkvirtualenv --python=/usr/bin/python3 fixtrack
```
Or on a Mac
```bash
mkvirtualenv --python=/usr/local/bin/python3 fixtrack
```

(Note that the name of the virtualenv created is fixtrack, which is independent of the repo name fixtrack, but convenient.)

Now activate your virtual environment (it may already be active):
```
workon fixtrack
```

Then actually install the python dependencies into the `fixtrack` virtual environment:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Note that you can leave your virtual environment by running
```bash
deactivate
```
And delete it entirely with
```bash
rmvirtualenv fixtrack
```
**Run Tests**

In your virtual environment:
```bash
python -m pytest
```

### Run
You can now launch the application with something like the following
```bash
python scripts/fixtrack_app.py -h
```
A concrete example of launching would look like
```bash
python scripts/fixtrack_app.py --video data/group_8_2_morning_1227_vidGPGP040121_compressed.mov --track data/trackfile_new.h5
```
Right now the keyboard commands are
```
Space      Start/stop video
Left/Right Move forward/back one video frame
C          Switch between 2D and 3D cameras
V          Toggle the video visibility
1-9        Start following fish number 1-9 (clicking on a fish also starts following it)
0          Stop following fish
```

### Development
**Issues/Questions**

Please feel free to use the github issue tracker to submit issues or ask questions. The code is not very well documented and there are still many things unimplemented.

**requirements.txt**

`requrements.txt` lists exact versions of all Python packages used, to prevent dependency issues.  However, manually updating versions is tedious, so I use `requirements_dev.txt` to semi-automatically generate `requrements.txt`.  When running, always install from `requrements.txt`.  If modifying the requirements, do so using `requriements_dev.txt`.

**Pre-Commit**

Testing, linting, and file formatting are managed by pre-commit: https://pre-commit.com/

Install on the system using
```bash
apt install pre-commit
```

After cloning, in the repo directory, run
```bash
pre-commit install
```
When you commit or push, the code will be tested, linted, and formatted.

Configuration is managed in the following files:
```
.pre-commit-config.yaml
.style.yapf
.flake8
```
