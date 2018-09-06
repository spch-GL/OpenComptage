#!/usr/bin/env bash
Xvfb :1 -screen 0 1024x768x16 &
DISPLAY=:1.0
export DISPLAY
find / -type d -name 'QGIS' >> /tests/find.txt 
echo "Launching QGIS with startup script"
qgis --version-migration --nologo --code /tests/test.py &
echo "Wait 10s to let QGIS start"
sleep 10
echo "Take screenshot"
import -display :1 -window root /tests/screenshot.png
