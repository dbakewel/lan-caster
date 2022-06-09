CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -game demo3 -test
start "Client for Java" cmd /K py -3 src/startclient.py -game demo3 -player "Scout"