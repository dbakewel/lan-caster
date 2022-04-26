CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -game "helloworld"
start "Client for Java" cmd /K py -3 src/startclient.py -game "helloworld" -player "Doug"

