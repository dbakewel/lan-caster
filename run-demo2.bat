CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -game demo2 -verbose -test
start "Client for Java" cmd /K py -3 src/startclient.py -game demo2 -player "Scout" -width 1000
start "Client for Java" cmd /K py -3 src/startclient.py -game demo2 -player "Java"  -width 1000