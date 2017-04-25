# ======================= FACEBOOK MESSENGER ToDoList Bot =======================

import sys, json, traceback, requests
from time import strptime
from flask import Flask, request
from utils import *


# ======================= System configuration =======================
application = Flask(__name__)
app = application

PageAccessToken = 'EAAGa5ZB7WAScBAKsdOXmLZCwjOA4rGwqv209VnUutSZCPDerAIr6u1k86KlpTDgtZBLAW1rZC8RWHGbrpMk9PB1atLFtosDLwjx7tTs4MkgC0p8YO0I0dqv6P4aJZCM6aS8X0F1zsbsmhkUcf6DcOXeXqUK3Kskj6o0a0TLdZBZAXwbtjWSjWDQv'
VerificationToken = 'Mountain Viewer'

deadline_db = dict()
info_shown = set()


# ======================= Verification =======================
@app.route('/', methods=['GET'])
def handle_verification():
  print("Handling Verification.")

  if request.args.get('hub.verify_token', '') == VerificationToken:
    print("Webhook verified!")
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
      traceback.print_exc()
  return "ok"


info_message1 = """
  This is the TODO-list bot by Mountain Viewer.\n\n"""
info_message2 = """
Use the following commands to put in order your deadlines:\n
  1) 'add <deadline name> dd/mm/yy' -- to put new deadline into list\n
  2) 'remove <deadline id>' -- to remove an existing deadline\n
  3) 'list' -- to show all existing deadlines\n
  4) 'rename <deadline id> <new name>' -- to rename an existing deadline\n
  5) 'set_deadline <deadline id> dd/mm/yy' -- to set new date for an existing deadline\n
  6) 'done <deadline id>' -- to mark an existing deadline as completed\n\n
"""
info_message3 = """
And remember: it is in your interest to watch the correct work of the bot - so there is
no need to try break it! :)
"""

def update_deadlines(user_id, response):
  
  if user_id not in info_shown:
    send_message(PageAccessToken, user_id, info_message1)
    send_message(PageAccessToken, user_id, info_message2)
    send_message(PageAccessToken, user_id, info_message3)
    info_shown.add(user_id)

  parsed_response = response.decode('UTF-8').split()

  if parsed_response[0].lower() == 'add':

    title = parsed_response[1]
    for i in range(2, len(parsed_response) - 1):
      title += " " + parsed_response[i]

    if deadline_db.get(user_id) == None:
      deadline_db[user_id] = DeadlineCollection()

    status = deadline_db[user_id].add(title, strptime(parsed_response[len(parsed_response) - 1], "%d/%m/%y"))

    return "Your deadline has been added." if status else "Operation could not be executed."
  elif parsed_response[0].lower() == 'remove':
    status = deadline_db[user_id].remove(int(parsed_response[1]))
    return "Your deadline has been removed." if status else "Operation could not be executed."
  elif parsed_response[0].lower() == 'list':
    deadline_db[user_id].sort()
    return deadline_db[user_id].list()
  elif parsed_response[0].lower() == 'rename':

    title = parsed_response[2]
    for i in range(3, len(parsed_response)):
      title += " " + parsed_response[i]

    status = deadline_db[user_id].rename(int(parsed_response[1]), title)

    return "Your deadline has been renamed." if status else "Operation could not be executed."
  elif parsed_response[0].lower() == 'set_deadline':
    status = deadline_db[user_id].set_deadline(int(parsed_response[1]), strptime(parsed_response[2], "%d/%m/%y"))
    return "Your deadline has been rescheduled." if status else "Operation could not be executed."
  elif parsed_response[0].lower() == 'done':
    status = deadline_db[user_id].done(int(parsed_response[1]))
    return "Your deadline has been marked as completed." if status else "Operation could not be executed."
  else:
    return "Incorrect request!"

def process_incoming(message):
  if message['type'] == 'text':
    message_text = message['data']
    return message_text
  else:
    return "*scratch my head*"


def send_message(token, user_id, text):
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
    print(r.text)


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
  if len(sys.argv) == 2:  # Allow running on customized ports
    app.run(port=int(sys.argv[1]))
  else:
    app.run()  # Default port 5000
