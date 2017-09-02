import socket
import threading
import win32gui
from datetime import timedelta
from functools import update_wrapper
import requests
import win32con

##Server settings for RCON
IP = "127.0.0.1"
port = 12203
rconpassword = "rconpass"

def read_console():
    #Check console every second
    threading.Timer(1.0, read_console).start()

    try:
        ##Find the MOH console window,
        #For AA set it to: "MOHAA WinConsole"
        #For SH set it to: "MOHTA WinConsole"
        #For BT set it to: "MOHTA WinConsole"
        hwnd = win32gui.FindWindow("MOHAA WinConsole", None)
        console = win32gui.GetDlgItem(hwnd, 100)
        clearBtn = win32gui.FindWindowEx(hwnd, None, "Button", "clear")

        buffer = win32gui.PyMakeBuffer(25555)
        length = win32gui.SendMessage(console, win32con.WM_GETTEXT, 25555, buffer)
        result = buffer[:length]

        #Click the clear button
        win32gui.SendMessage(clearBtn, win32con.WM_LBUTTONDOWN, 0, 0)
        win32gui.SendMessage(clearBtn, win32con.WM_LBUTTONUP, 0, 0)

        #Split on newline
        splitted = result.splitlines()

        ##CHATCOMMANDS
        #Define you commands first
        filter = ["!help", "!admin", "!ss", "!site", "!joke"]

        cmd = ""

        for index, value in enumerate(splitted):
            if any(x in value for x in filter):
                if "!help" in value:
                    cmd = "say [help] Available commands: !site (Shows our clansite); !joke (Gets a random joke); !help shows this message."
                if "!admin" in value:
                    cmd = "say [Admin] Called for an admin! If an admin is online he/she will come!"
                if "!site" in value:
                    cmd = "say [Site] test-clan.com"
                if "!joke" in value:
                    cmd = "say [Joke] " + joke()
                rcon(IP, port, rconpassword, cmd)

    except win32gui.error, e:
        print("Error: " + str(e))

def rcon(ip, port, password, command):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.8)
        sock.connect((ip, port))

        sock.send("\xFF\xFF\xFF\xFF\x02rcon " + password + " " + command)
        sock.close()
    except:
        print("Connection timeout.")
        sock.close()

def consoleMessages():
    #Show messages every 120sec
    threading.Timer(120.0, consoleMessages).start()
    messages = ["say [Info] Here is text1!", "say [Info] Here is text2!", "say [Info] Here is text3!"]
    for message in messages:
        rcon(IP, port, rconpassword, message)

def joke():
    r = requests.get('https://icanhazdadjoke.com/', headers={'Accept': 'application/json'})
    jokedata = r.json()
    try:
        return str(jokedata['joke'].decode("latin1"))
    except:
        return str("Oops something went wrong! Try again!")

if __name__ == '__main__':
    read_console()
    consoleMessages()