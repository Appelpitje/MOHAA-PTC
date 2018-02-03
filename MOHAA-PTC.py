import threading
import win32con
import win32gui
import socket
import requests
import ctypes
import configparser
from datetime import timedelta
from functools import update_wrapper

from flask import Flask, request, jsonify, make_response, current_app

app = Flask(__name__)


import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def readConfig():
    config = configparser.RawConfigParser()
    try:
        config.read('settings.cfg')
        settings["MOHPTC_port"] = config.get('MOHPTC-server', 'port')
        settings["server_game"] = config.get('MOH-server', 'game')
        settings["server_ip"] = config.get('MOH-server', 'IP')
        settings["server_port"] = int(config.get('MOH-server', 'port'))
        settings["server_rconpassword"] = config.get('MOH-server', 'rconpassword')
        handleGame()
    except:
        print('Error with the config, please check if the config file exists and is in correct format.')


def handleGame():
    settings["server_windows"] = ""
    if settings["server_game"] == "AA":
        settings["server_windows"] = "MOHAA WinConsole"
    else:
        settings["server_windows"] = "MOHTA WinConsole"


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def read_console():
    print('Reading server console data...')
    threading.Timer(1.0, read_console).start()
    global kills
    try:
        #Find the MOH console window
        hwnd = win32gui.FindWindow(settings["server_windows"], None)
        console = win32gui.GetDlgItem(hwnd, 100)
        clearBtn = win32gui.FindWindowEx(hwnd, None, "Button", "clear")

        buffer = win32gui.PyMakeBuffer(25555)
        length = win32gui.SendMessage(console, win32con.WM_GETTEXT, 25555, buffer)
        result = buffer[0:length * 2].tobytes().decode("UTF-16")

        #Click the clear button
        win32gui.SendMessage(clearBtn, win32con.WM_LBUTTONDOWN, 0, 0)
        win32gui.SendMessage(clearBtn, win32con.WM_LBUTTONUP, 0, 0)

        #split on newline
        splitted = result.splitlines()
        print(splitted)
        cmd = ""

        kills = []
        how = [" was rifled by ", " was machine-gunned by ", " was bashed by ", " was gunned down by ", " was sniped by ", " was crushed by ", " was clubbed by ", " was sniped by ", " was perforated by ", " pumped full of buckshot by "]
        for index, value in enumerate(splitted):
            if any(x in value for x in how):
                kills.append(value)

        print(kills)

        # Split kills
        # for index, value in enumerate(kills):
        #    for y in how:
        #       kills[index] = kills[index].replace(str(y),'')

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
                rcon(settings["server_ip"], settings["server_port"], settings["server_rconpassword"], cmd)

    except Exception as e:
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
        rcon(settings["server_ip"], settings["server_port"], settings["server_rconpassword"], message)


def joke():
    r = requests.get('https://icanhazdadjoke.com/', headers={'Accept': 'application/json'})
    jokedata = r.json()
    try:
        return str(jokedata['joke'])
    except:
        return str("Oops something went wrong! Try again!")


@app.route('/kills')
@crossdomain(origin='*')
def handle_kills():
    return jsonify(kills)


@app.route('/')
def main():
        return "Choo choo, nothing to see here!"


if __name__ == '__main__':
    global settings
    settings = {}
    readConfig()
    ctypes.windll.kernel32.SetConsoleTitleA("MOHAA Python Total Control [port " + settings["MOHPTC_port"] + "]")
    print("Starting MOHPTC on port: " + settings["MOHPTC_port"])
    read_console()
    consoleMessages()
    app.run(threaded=True, debug=False, use_evalex=False, host='0.0.0.0', port=int(settings["MOHPTC_port"]))
