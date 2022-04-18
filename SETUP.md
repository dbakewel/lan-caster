[ [ABOUT](README.md) | **SETUP and RUN** | [CREATE A GAME](CREATE.md) | [TUTORIALS](TUTORIALS.md) | [CONTRIBUTING](CONTRIBUTING.md) ]

# LAN-Caster - Setup and Run

## Setup

The following items need to be installed to run LAN-Caster.

### Install Python 3.6 or higher

LAN-Caster uses Python 3.6 or higher (tested on python 3.10) which can be installed from [https://www.python.org/downloads/](https://www.python.org/downloads/).

> If multiple versions of python are installed, ensure you are running python 3.6+, not python 3.5 or python 2. The examples in this README use the "python" command assuming python 3.6+ is the default. The command "python3" (Linux) or "py -3" (Windows) may be required to force the correct version.

### Install Python Modules
LAN-Caster requires two added python modules to be installed.
1) Pygame is used by the clients to open the game window, render graphics, and collect player input. 
2) Msgpack is used to encode and decode messages between the server and clients.

To install pygame and msgpack on Windows use:
```
py -3 -m pip install pygame msgpack
```

To install pygame and msgpack on Linux use:
```
pip3 install pygame msgpack
```

Note, if a computer is only running the LAN-Caster server then the pygame module is not required.

### Download LAN-Caster Code

The LAN-Caster code can be cloned with git from: [https://github.com/dbakewel/lan-caster.git](https://github.com/dbakewel/lan-caster.git) or downloaded in zip form from: [https://github.com/dbakewel/lan-caster/archive/master.zip](https://github.com/dbakewel/lan-caster/archive/master.zip)


## Run the Demo

On windows, **double click "run-demo.bat"** in the root of the LAN-Caster directory.

> If this does not work, open a command window (cmd), cd into the directory containing run-demo.bat and type "rundemo.bat".

The rundemo script will start 4 processes on the local computer: 1 server and 3 clients. Normally, each client would run on a different computer and be used by a different player. The run-demo.bat allows one user to move back and forth between all 3 clients and play all the players at once.

## Running on Separate Computers

For example:

Assuming:
*   computer 1 has IP address of 192.168.1.10
*   computer 2 has IP address of 192.168.1.11
*   computer 3 has IP address of 192.168.1.22
*   computer 4 has IP address of 192.168.1.33

The server can be run on computer 1 with: 

```
py -3 src/startserver.py -game "demo"
```

The server will listen on 127.0.0.1 and 192.168.1.10

A client can be run on Computer 2, 3, and 4 with: 

```
py -3 src/startclient.py -game "demo" -sip 192.168.1.10
```

> Note, if you want to run LAN-Caster across a network then the ports you choose must be open in the OS and network firewalls for two way UDP traffic. By default, LAN-Caster uses ports of  20000 and above but any available UDP ports can be used.

## Command Line Help

The server and client allow some customization with command line switches. Use the **-h** switch to display help. For example:

```
d:\lan-caster>py -3 src/startserver.py -h
usage: startserver.py [-h] [-game dir] [-register name] [-ch hostname] [-cp port] [-sip ipaddr] [-sp port] [-fps fps]
                      [-busy secs] [-pause secs] [-test] [-profile] [-verbose] [-debug]

options:
  -h, --help      show this help message and exit
  -game dir       Directory to load game from (default: demo)
  -register name  Experimental: Register with connector as name (False == do not register) (default: False)
  -ch hostname    Experimental: Connector hostname or IP address (default: lan-caster.net)
  -cp port        Experimental: Connector port number (default: 20000)
  -sip ipaddr     Server IP address (default: 0.0.0.0)
  -sp port        Server port number (default: 20001)
  -fps fps        Target frames per second (aka steps/sec) (default: 30)
  -busy secs      Seconds between logging percent busy (default: 60)
  -pause secs     Duration to pause in seconds before starting server (for testing) (default: 0)
  -test           Start server in test mode (default: False)
  -profile        Print function performance profile on exit. (default: False)
  -verbose        Print VERBOSE level log messages (default: False)
  -debug          Print DEBUG level log messages (includes -verbose) (default: False)
```

```
d:\lan-caster>py -3 src/startclient.py -h
pygame 2.1.2 (SDL 2.0.18, Python 3.10.4)
Hello from the pygame community. https://www.pygame.org/contribute.html
usage: startclient.py [-h] [-game dir] [-player name] [-connect name] [-ch hostname] [-cp port] [-sip ipaddr]
                      [-sp port] [-ip ipaddr] [-p port] [-width width] [-height height] [-fps fps] [-busy secs]
                      [-pause secs] [-profile] [-verbose] [-debug]

options:
  -h, --help      show this help message and exit
  -game dir       Directory to load game from (default: demo)
  -player name    Player's name to display in game (default: anonymous)
  -connect name   Experimental: Connect to server using connector. "name" must match server's "-register name" (if
                  False then use -sip and -sp to connect to server) (default: False)
  -ch hostname    Experimental: Connector hostname or IP address (default: lan-caster.net)
  -cp port        Experimental: Connector port number (default: 20000)
  -sip ipaddr     Server IP address (default: 127.0.0.1)
  -sp port        Server port number (default: 20001)
  -ip ipaddr      Client IP address (default: 0.0.0.0)
  -p port         Client port number (client will search for an available port starting with this number.) (default:
                  20002)
  -width width    Window width (default: 640)
  -height height  Window height (default: 640)
  -fps fps        Target frames per second (default: 30)
  -busy secs      Seconds between logging percent busy (default: 60)
  -pause secs     Duration to pause in seconds before starting client (for testing) (default: 0)
  -profile        Print function performance profile on exit. (default: False)
  -verbose        Print VERBOSE level log messages (default: False)
  -debug          Print DEBUG level log messages (includes -verbose) (default: False)
```


## Additional Information

### Install Connector Systemd Service on Linux (Experimental)
Assuming lan-caster has been installed under a linux user name 'lan-caster' with home dir '/home/lan-caster'
```
cd /home/lan-caster/lan-caster/systemd
sudo cp connector.service /lib/systemd/system/
sudo systemctl enable connector.service
```

