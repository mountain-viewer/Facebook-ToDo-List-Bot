# ======================= FACEBOOK MESSENGER ToDoList Bot =======================

import os, sys, json, traceback, requests
import time, operator, logging
from flask import Flask, request

from tokens import *
from utils import *
from billing import *

# ======================= System messages ======================
INFO_MESSAGE1 = """
  This is the TODO-list bot by Mountain Viewer.\n\n"""

INFO_MESSAGE2 = """
    Use the following commands to put in order your deadlines:\n
    1) 'add <deadline name> dd/mm/yy' -- to put new deadline into list\n
    2) 'remove <deadline id>' -- to remove an existing deadline\n
    3) 'list' -- to show all existing deadlines\n
    4) 'rename <deadline id> <new name>' -- to rename an existing deadline\n
    5) 'set_deadline <deadline id> dd/mm/yy' -- to set new date for an existing deadline\n
    6) 'done <deadline id>' -- to mark an existing deadline as completed\n\n
    7) 'help' -- to show the commands"""

INFO_MESSAGE3 = """
    And remember: it is in your interest to see the correct work of the bot - so there is no need to try to break it! :)"""

# ======================= System configuration =======================
app = Flask(__name__)

deadline_db = dict()
user_db = set()

# ======================= Logging =======================

logging.basicConfig(filename='system.log',level=logging.DEBUG)

# ======================= Scheduling and Retrieval =======================
def dump():
    logging.info("Dumping to databases.")
    write_to_storage(deadline_db)
    write_to_users(list(user_db))

if os.stat(users_db).st_size != 0:
    user_db = set(read_from_users())

if os.stat(storage_db).st_size != 0:
    deadline_db = read_from_storage()

# start timer
timer = RepeatedTimer(1200, dump)

# ======================= Verification =======================
@app.route('/', methods=['GET'])
def handle_verification():
    logging.info("Webhook Verification.")

    if request.args.get('hub.verify_token', '') == VerificationToken:
        logging.info("Webhook verified!")

        return request.args.get('hub.challenge', '')
    else:
        return "Wrong verification token!"


# ======================= Bot processing ===========================
@app.route('/', methods=['POST'])
def handle_messages():
    payload = request.get_data()

    # Handle messages
    for sender_id, message in messaging_events(payload):
        # Start processing valid requests
        try:
            if message is None:
                continue

            response = process_incoming(message)
            result = update_deadlines(sender_id, response)

            if result is not None:
                send_message(PageAccessToken, sender_id, result)
            else:
                send_message(PageAccessToken, sender_id, "Sorry I don't understand that")
        except Exception:
            logging.exception(traceback.format_exc)

    return "ok"

def update_deadlines(user_id, response):
    logging.info("Operating with user: {0}.".format(user_id))

    if user_id not in user_db:
        send_message(PageAccessToken, user_id, INFO_MESSAGE1)
        send_message(PageAccessToken, user_id, INFO_MESSAGE2)
        send_message(PageAccessToken, user_id, INFO_MESSAGE3)
        user_db.add(user_id)

    parsed_response = response.decode('UTF-8').split()

    if parsed_response[0].lower() == 'add':
        title = parsed_response[1]
        for i in range(2, len(parsed_response) - 1):
            title += " " + parsed_response[i]

        if user_id not in deadline_db:
            deadline_db[user_id] = []

        deadline = dict()

        deadline["title"] = title
        deadline["id"] = len(deadline_db[user_id]) + 1
        deadline["deadline"] = time.mktime(time.strptime(parsed_response[len(parsed_response) - 1], "%d/%m/%y"))

        deadline_db[user_id].append(deadline)

        return "Your deadline has been added."
    elif parsed_response[0].lower() == 'remove':
        status = False
        index = -1

        if user_id in deadline_db:
            for i in range(len(deadline_db[user_id])):
                if deadline_db[user_id][i]["id"] == int(parsed_response[1]):
                    index = i
                    status = True
                    break

        if status:
            deadline_db[user_id].pop(index)

        return "Your deadline has been removed." if status else "There is no deadline with {0} id.".format(parsed_response[1])
    elif parsed_response[0].lower() == 'list':
        if user_id in deadline_db:
            deadline_db[user_id].sort(key=operator.itemgetter("deadline"))
            return Response(deadline_db[user_id])
        return []
    elif parsed_response[0].lower() == 'rename':
        title = parsed_response[2]
        for i in range(3, len(parsed_response)):
            title += " " + parsed_response[i]

        status = False

        if user_id in deadline_db:
            for i in range(len(deadline_db[user_id])):
                if deadline_db[user_id][i]["id"] == int(parsed_response[1]):
                    deadline_db[user_id][i]["title"] = title
                    status = True
                    break

        return "Your deadline has been renamed." if status else "There is no deadline with {0} id.".format(parsed_response[1])
    elif parsed_response[0].lower() == 'set_deadline':
        status = False

        if user_id in deadline_db:
            for i in range(len(deadline_db[user_id])):
                if deadline_db[user_id][i]["id"] == int(parsed_response[1]):
                    deadline_db[user_id][i]["deadline"] = time.mktime(time.strptime(parsed_response[2], "%d/%m/%y"))
                    status = True
                    break

        return "Your deadline has been rescheduled." if status else "There is no deadline with {0} id.".format(parsed_response[1])
    elif parsed_response[0].lower() == 'done':
        status = False
        index = -1

        if user_id in deadline_db:
            for i in range(len(deadline_db[user_id])):
                if deadline_db[user_id][i]["id"] == int(parsed_response[1]):
                    index = i
                    status = True
                    break

        if status:
            deadline_db[user_id].pop(index)
        return "Your deadline has been marked as completed." if status else "There is no deadline with {0} id.".format(parsed_response[1])
    elif parsed_response[0].lower() == 'help':
        return INFO_MESSAGE2
    else:
        return "Incorrect request!"

def process_incoming(message):
    if message['type'] == 'text':
        message_text = message['data']
        return message_text
    else:
        return "*scratch my head*"


def send_message(token, user_id, text):
    logging.info("Sending a message to user {0}.".format(user_id))
    """Send the message text to recipient with id recipient.
        """
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                        params={"access_token": token},
                        data=json.dumps({
                                    "recipient": {"id": user_id},
                                    "message": {"text": str(text)}
                                    }),
                        headers={'Content-type': 'application/json'})

    if r.status_code != requests.codes.ok:
        logging.warning(r.text)

# ======================= Notification System =======================

def notify():
    logging.info("Notification Center is working.")
    for user in deadline_db.keys():
        deadline_db[user].sort(key=operator.itemgetter("deadline"))
        send_message(PageAccessToken, user, "Your deadlines in the future.")
        send_message(PageAccessToken, user, Response(deadline_db[user]))

notification_center = RepeatedTimer(600, notify)

# Generate tuples of (sender_id, message_text) from the provided payload.
# This part technically clean up received data to pass only meaningful data to processIncoming() function
def messaging_events(payload):
    data = json.loads(payload.decode('UTF-8'))
    messaging_events = data["entry"][0]["messaging"]

    for event in messaging_events:
        sender_id = event["sender"]["id"]

        # Not a message
        if "message" not in event:
            yield sender_id, None

        # Pure text message
        if "message" in event and "text" in event["message"] and "quick_reply" not in event["message"]:
            data = event["message"]["text"].encode('unicode_escape')
            yield sender_id, {'type': 'text', 'data': data, 'message_id': event['message']['mid']}

# Allows running with simple `python <filename> <port>`
if __name__ == '__main__':
    logging.info("Starting of the bot.")
    if len(sys.argv) == 2:  # Allow running on customized ports
        app.run(port=int(sys.argv[1]))
    else:
        app.run()  # Default port 5000
