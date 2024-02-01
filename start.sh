#!/bin/bash
yum install git
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
git clone https://github.com/GokulVSD/CDengVA.git
cd CDengVA/
git pull
python3 -m pip install -r requirements.txt
python3 app.py
