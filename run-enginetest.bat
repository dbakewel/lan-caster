CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -game "enginetest" -fps 60 -test -verbose
start "Client" cmd /K py -3 src/startclient.py -game "enginetest" -fps 60 -player "Bob" -verbose

