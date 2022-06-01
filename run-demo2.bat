CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -game demo2
start "Client for Java" cmd /K py -3 src/startclient.py -game demo2 -player "Scout"
start "Client for Java" cmd /K py -3 src/startclient.py -game demo2 -player "Java"
start "Client for Java" cmd /K py -3 src/startclient.py -game demo2 -player "Callisto"
start "Client for Java" cmd /K py -3 src/startclient.py -game demo2 -player "Jackson"
start "Client for Java" cmd /K py -3 src/startclient.py -game demo2 -player "Rosco"
start "Client for Java" cmd /K py -3 src/startclient.py -game demo2 -player "Todi"
start "Client for Java" cmd /K py -3 src/startclient.py -game demo2 -player "China"
start "Client for Java" cmd /K py -3 src/startclient.py -game demo2 -player "Tucker"