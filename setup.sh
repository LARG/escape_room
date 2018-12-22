#!/usr/bin/env bash
set -e

#rm -rf ~/panda
#git clone git@github.com:jmenashe/panda3d.git ~/panda
cd ~/panda

### Installation steps taken from Panda3D readme

# Dependencies
sudo apt-get install build-essential pkg-config python-dev libpng-dev libjpeg-dev libtiff-dev zlib1g-dev libssl-dev libx11-dev libgl1-mesa-dev libxrandr-dev libxxf86dga-dev libxcursor-dev bison flex libfreetype6-dev libvorbis-dev libeigen3-dev libopenal-dev libode-dev libbullet-dev nvidia-cg-toolkit libgtk2.0-dev

# Build

python makepanda/makepanda.py --everything --installer --no-egl --no-gles --no-gles2 --no-opencv --threads=$NUM_PROCS

# Install

sudo dpkg -i panda3d*.deb

# Project-specific

sudo pip install gitpython redis parse tensorflow keras-rl gym pyyaml matplotlib

sudo apt-get install -y python-gi-cairo python-tk
