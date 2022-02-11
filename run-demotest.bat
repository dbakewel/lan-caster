CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -test -pause 3 -verbose
start "Client for Java" cmd /K py -3 src/startclient.py -player "Java" -pause 0 -verbose
start "Client for Scout" cmd /K py -3 src/startclient.py -player "Scout" -pause 6 -verbose
start "Client for River" cmd /K py -3 src/startclient.py -player "River" -pause 9 -verbose

