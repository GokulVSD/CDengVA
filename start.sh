#!/bin/bash
yum install git
curl -O https://bootstrap.pypa.io/get-pip.py
sudo python3 get-pip.py
git clone https://github.com/GokulVSD/CDengVA.git
cd CDengVA/
git pull
sudo python3 -m pip install -r requirements.txt
sudo python3 app.py
