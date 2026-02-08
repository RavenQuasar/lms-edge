#!/bin/bash
if ! pgrep -f "python3 app_api.py" > /dev/null; then
    cd /home/raven/lms-edge/backend
    nohup python3 app_api.py > /tmp/lms_game.log 2>&1 &
    echo "Flask restarted at $(date)" >> /tmp/flask_monitor.log
fi
