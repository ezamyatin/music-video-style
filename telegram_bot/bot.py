#!/usr/bin/python3
import random

import requests
import json
import time
import datetime
import pickle
import logging
import sys
import urllib.request
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import main_with_list_args as make_style
# def make_style(args, callback):
#     for i in range(100):
#         callback(i)
#         time.sleep(0.5)


URL_TELEGRAM = "https://api.telegram.org/"
URL_TELEGRAM_BOT = URL_TELEGRAM + "bot"
TOKEN = "376252610:AAHQdNgobYzUjAjIGijmKsseCvTqHXjIj4Y"
# TOKEN = "347354478:AAFU8is7V_KN-9IvVFBzphwgT3RCq0cBQQo"
BOT_NAME = "VideoST_bot"
DOWNLOAD_PATH = os.getcwd() + "/downloads/"


def create_request_url(request):
    return URL_TELEGRAM_BOT + TOKEN + "/" + request


updates_url = create_request_url("getUpdates")
send_message_url = create_request_url("sendMessage")
send_video_url = create_request_url("sendVideo")
get_file_url = create_request_url("getFile")
download_file_url = URL_TELEGRAM + "file/bot" + TOKEN + "/"  # + file_path
reply_keyboard_url = create_request_url("ReplyKeyboardMarkup")
edit_message_url = create_request_url("editMessageText")


def get_updates(offset=0):
    payload = {"offset": offset}
    response = requests.get(updates_url, json=payload)
    json_response = json.loads(response.text)

    if not json_response["ok"]:
        dump("so sorry, response updates: {}".format(json_response))

    return json_response["result"]


def get_file(chat_id, file_id):
    dump("get_file from chat_id = {}".format(chat_id))
    payload = {"file_id": file_id}
    response = requests.post(get_file_url, json=payload)
    json_response = json.loads(response.text)

    dump("got responce: {}", json_response)

    res_path = None

    if "result" in json_response:
        result = json_response["result"]

        if "file_path" in result:
            file_path = result["file_path"]

            url_for_download_video = download_file_url + file_path

            _, video_extension = os.path.splitext(file_path)
            res_path = DOWNLOAD_PATH + str(chat_id) + video_extension

            dump("start downloading video from url: {}; to: {}".format(url_for_download_video, res_path))
            message_id = send_message(chat_id, "start downloading video")

            urllib.request.urlretrieve(url_for_download_video, res_path)

            dump("download completed")
            message_id = edit_message(chat_id, message_id, "the download completed")
            message_id = edit_message(chat_id, message_id, "Creating stylish video: 0% completed")

            return res_path, message_id

    return None


def send_message(chat_id, text):
    dump("send to chat_id = {}, text = {}".format(chat_id, text))

    payload = {"chat_id": chat_id,
               "text": text,
               "parse_mode": "HTML"
               }

    response = requests.post(send_message_url, json=payload)
    json_response = json.loads(response.text)

    if "error_code" in json_response:
        dump("error SEND: {}".format(response.text))

        try:
            existing_chats.remove(chat_id)
        except:
            pass

        return -1
    else:
        dump("SEND: {}".format(response.text))

        if not json_response["ok"]:
            dump("so sorry, response: {}".format(json_response))
            return -1

        return json_response["result"]["message_id"]


def edit_message(chat_id, message_id, new_text):
    dump("edit_message to chat_id = {}, message_id = {}, new_text = {}".format(chat_id, message_id, new_text))

    payload = {"chat_id": chat_id,
               "message_id": message_id,
               "text": new_text,
               "parse_mode": "HTML"
               }

    response = requests.post(edit_message_url, json=payload)
    json_response = json.loads(response.text)

    dump("{}".format(json_response))

    if "error_code" in json_response:
        dump("error SEND: {}".format(response.text))

        return message_id # because edit message return Bad request if message not modified
    else:
        dump("SEND: {}".format(response.text))

        if not json_response["ok"]:
            dump("so sorry, response: {}".format(json_response))
            return -1

        return json_response["result"]["message_id"]


def send_reply_keyboard(chat_id, buttons):
    pass


#     dump("send to reply_keyboard to chat_id = {}, text = {}".format(chat_id, text))
#
#     payload = {"chat_id": chat_id,
#                "text": text,
#                "parse_mode": "HTML"}
#
#     response = requests.post(send_message_url, json=payload)
#     json_response = json.loads(response.text)
#
#     if "error_code" in json_response:
#         dump("error SEND: {}".format(response.text))
#
#         try:
#             existing_chats.remove(chat_id)
#         except:
#             pass
#
#         return -1
#     else:
#         dump("SEND: {}".format(response.text))
#
#         if not json_response["ok"]:
#             dump("so sorry, response: {}".format(json_response))
#
#         return 0


def send_video(chat_id, path_to_video):
    dump("start sending video to chat_id: {}, with path: {}".format(chat_id, path_to_video))
    with open(path_to_video, 'rb') as video_file:
        payload = {"video": video_file}
        send_url = "{}?chat_id={}".format(send_video_url, chat_id)
        response = requests.post(send_url, files=payload)
        json_response = json.loads(response.text)

        dump("video was sent: {}", json_response)


def start_cmd(chat_id):
    global existing_chats

    dump("in start_cmd")

    send_message(chat_id, "Hi, I can make your video better")
    existing_chats.add(chat_id)


def stop_cmd(chat_id):
    global existing_chats

    dump("in stop_cmd")
    send_message(chat_id, "No")

    existing_chats.remove(chat_id)


def dump_users(*_):
    global last_dumped_time
    last_dumped_time = datetime.datetime.now()

    dump("dump users")
    with open("users.txt", "wb") as u:
        pickle.dump(existing_chats, u)
        pickle.dump(last_update_id, u)
        pickle.dump(g_chat_id, u)
        pickle.dump(video_sizes, u)
        pickle.dump(video_styles, u)


def load_users(*_):
    global existing_chats
    global last_update_id
    global g_chat_id
    global video_sizes
    global video_styles

    dump("load_users")
    try:
        with open("users.txt", "rb") as u:
            existing_chats = pickle.load(u)
            last_update_id = pickle.load(u)
            g_chat_id = pickle.load(u)
            video_sizes = pickle.load(u)
            video_styles = pickle.load(u)

            dump(existing_chats)
    except Exception as e:
        dump("users.txt doesn't exist")
        dump(e)


def setup_logger():
    global dump

    formatter = logging.Formatter('%(asctime)s (%(threadName)-10s) %(message)s', datefmt='%H:%M:%S')
    file_handler = logging.FileHandler("videoST.log", mode='w')
    file_handler.setFormatter(formatter)

    logger = logging.getLogger("videoST")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    dump = logger.debug


def duplicate_commands_with_bot_name():
    global commands

    new_commands = {}
    for name, cmd in commands.items():
        new_commands[name + "@" + BOT_NAME] = cmd

    commands.update(new_commands)


def shut_down(chat_id, *_):
    global proceed

    # for deleting recent shut_down request
    unused = get_updates(last_update_id)
    send_message(chat_id, "shut down :(")

    dump("shut_donw")
    dump_users()
    proceed = False


current_style = 'wave'


def handle_text(text, chat_id):
    if text in commands:
        dump("command, chat_id: {} {}".format(text, chat_id))
        commands[text](chat_id)
    else:
        for pref_cmd, fun_cmd in prefix_commands.items():
            n = len(pref_cmd)
            if pref_cmd == text[:n]:
                fun_cmd(chat_id, text[n + 1:], pref_cmd)
                break


def notify_user_unrecognized_cmd(chat_id, text, cmd_name):
    ret_msg = help_user_txt[cmd_name]
    if text:
        ret_msg = "unrecognized value: " + text + "; " + ret_msg

    send_message(chat_id, ret_msg)


def handle_set_style(chat_id, text, cmd_name):
    global video_styles

    dump("got set_style: {}".format(text))

    text = text.strip()
    if text in supported_styles:
        video_styles[chat_id] = text

        send_message(chat_id, "Current video style: {}".format(text))
    else:
        notify_user_unrecognized_cmd(chat_id, text, cmd_name)


def handle_set_video_size(chat_id, text, cmd_name):
    global video_sizes

    dump("got set_video_size: {}".format(text))

    text = text.strip()
    if text in supported_sizes:
        video_sizes[chat_id] = text

        send_message(chat_id, "Current video size: {}".format(text))
    else:
        notify_user_unrecognized_cmd(chat_id, text, cmd_name)


def update_during_stylish(chat_id, message_id):
    def callback(percentage):
        nonlocal message_id
        nonlocal chat_id

        message_id = edit_message(chat_id, message_id, "Creating stylish video: " + str(int(percentage)) + "% completed")

    return callback

def handle_doc(document, chat_id):
    dump("get doc: {}".format(document))

    (res_path, message_id) = get_file(chat_id, document["file_id"])

    if res_path is not None:
        base_name, extension = os.path.splitext(res_path)
        output_path = base_name + "_out" + extension

        video_style = video_styles.get(chat_id, supported_styles[0])
        video_size = video_sizes.get(chat_id, supported_sizes[0])

        path_to_model = "data/models/"
        if "nemchenko" in os.getcwd():
            path_to_model = "/home/evgeny/music-video-style/data/models/"

        args = ["--video=" + res_path,
                "--neural=" + path_to_model + video_style,
                "--size=" + video_size,
                "--output=" + output_path]

        dump("make_style")
        dump("args: {}".format(args))
        make_style(args, update_during_stylish(chat_id, message_id))

        message_id = edit_message(chat_id, message_id, "stylish video was created")
        dump("stylish video was created")

        send_video(chat_id, output_path)

        message_id = edit_message(chat_id, message_id, "Work done")


def handle_message(msg):
    global g_chat_id

    g_chat_id = msg["chat"]["id"]

    for attr, handler in attributes_for_request.items():
        if attr in msg:
            handler(msg[attr], g_chat_id)
            break


proceed = True
existing_chats = set()

# TODO: move this to config
supported_styles = ["wave", "stained-glass", "flames", "udnie", "cossacks"]
video_styles = {}

# TODO: move this to config
supported_sizes = ["256", "512", "1024"]
video_sizes = {}

help_user_txt = {
    "/set_style": "Please pass one of this styles: {}; <b> e.g. /set_style {} </b>"
        .format(", ".join(supported_styles), supported_styles[0]),

    "/set_video_size": "Please pass one of this sizes: {}; <b> e.g. /set_video_size {} </b>"
        .format(", ".join(supported_sizes), supported_sizes[0])
}

last_update_id = 0
g_chat_id = 0
last_dumped_time = datetime.datetime.now()

commands = {"/start": start_cmd,
            "/stop": stop_cmd,
            "/shut_down": shut_down
            }

prefix_commands = {"/set_style": handle_set_style,
                   "/set_video_size": handle_set_video_size
                   }

attributes_for_request = {"text": handle_text,
                          "document": handle_doc,
                          "video": handle_doc
                          }

valid_requests = {"message": handle_message
                  # , "inline_request": handle_inline_request
                  }

if __name__ == "__main__":
    setup_logger()
    load_users()
    duplicate_commands_with_bot_name()

    while proceed:
        try:
            json_response = get_updates(last_update_id)

            for entry in json_response:
                dump("got entry: {}".format(entry))

                last_update_id = max(last_update_id, entry["update_id"] + 1)
                dump("last_update_id = {}".format(last_update_id))

                for req, handler in valid_requests.items():
                    if req in entry:
                        handler(entry[req])
                        break

            time.sleep(1)

            cur = datetime.datetime.now()

            if cur - last_dumped_time > datetime.timedelta(minutes=1):
                dump_users()
        except Exception as e:
            dump_users()
            dump(e)
