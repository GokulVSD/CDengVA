#!/bin/bash
yum install git
git clone https://github.com/GokulVSD/CDengVA.git
cd CDengVA
git pull
python3 -m pip install -r requirements.txt
python3 app.py
