source ../venv/bin/activate
nohup python manage.py subscribe_location_update > location_event.log 2>&1 &
echo $! > nohup_pid.txt
