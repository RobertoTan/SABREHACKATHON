import requests
import telegram.ext as tele
import telegram.bot as bots
import api_keys as apis
import logging
import os.path
import sys
import json
from pprint import pprint
import apiai
import computer_vision as cv
import main

CLIENT_ACCESS_TOKEN = apis.ai_key
updater = tele.Updater(token=apis.telegram_key)
SESSION_ID = 0
send_image = False
tag_collection = []
location_votes = {}
my_locations = []
final_loc_list = []
final_loc = ""
final_date = ""
final_duration = ""
final_price = ""
final_pax  = ""
going_from = ""
phase_2 = False
phase_3 = False #Date
phase_4 = False #Price
phase_5 = False #Pax
phase_6 = False #Duration


def start(bot, update):
  bot.sendMessage(chat_id=update.message.chat_id, text="Hi, I'm Hermes, your group travel planner")

def parse(text,sessionId=0):
  # where x is text from user
  # sessionId is default 0 - get sessionId from response for subsequent parses
  ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
  request = ai.text_request()
  request.lang = 'en' 
  request.query = text
  request.session_id = sessionId
  response = json.load(request.getresponse())
  return response

def send_to_ai(bot,update):
  global SESSION_ID
  global send_image
  global phase_2
  global final_date
  global final_duration
  global final_price
  global final_pax
  global going_from
  global my_locations
  global tag_collection
  ai_reply = parse(update.message.text,SESSION_ID)
  print ai_reply
  if 'new_session' in ai_reply['result']['parameters']:
    my_locations = []
    tag_collection = []
  SESSION_ID = ai_reply['sessionId']
  if ai_reply['result']['fulfillment']['speech'] and not phase_2:
    bot.sendMessage(chat_id=update.message.chat_id,text = ai_reply['result']['fulfillment']['speech'])
  if phase_2:
    print "VOTED"
    collate_phase2_voting(update.message.text)
  if send_image and 'location_keywords' in ai_reply['result']['parameters']:
    print ai_reply
    for x in ai_reply['result']['parameters']['location_keywords']:
      collate_voting(x) 
  elif 'image_incoming' in ai_reply['result']['parameters']:
    send_image = ai_reply['result']['parameters']['image_incoming']
  # elif 'date' in ai_reply['result']['parameters']:

  # elif 'duration' in ai_reply['result']['parameters']:
  # elif 'pax' in ai_reply['result']['parameters']:
  # elif 'price' in ai_reply['result']['parameters']:
  elif 'is_completed' in ai_reply['result']['parameters']:
    # global final_loc
    # goingFrom,price,goingWhen,goingWhere,duration
    finals = {}
    if ai_reply['result']['parameters']['is_completed']:
      for x in ai_reply['result']['contexts']:
        print x['name']
        if x['name']== 'recommend_yesno':
          finals=x['parameters']

      # finals = ai_reply['result']['contexts'][1]['parameters']
      print finals
      # print ai_reply['result']['contexts'][2]['parameters']['origin']['geo-city']
      # bot.sendMessage(chat_id=update.message.chat_id,text = ai_reply['result']['fulfillment']['speech'])
      final_string = main.returnFlights(finals['origin']['geo-city'],finals['price']['unit-currency']['amount'],finals['date']['date'],final_loc,finals['duration']['duration']['amount'])
      bot.sendMessage(chat_id=update.message.chat_id,text = final_string)




def handle_images(bot,update):
  print update
  file_id = update['message']['photo'][0]['file_id']
  send_image_to_microsoft(file_id,bot,update)

def handle_documents(bot,update):
  print update
  file_id = update['message']['document']['file_id']
  send_image_to_microsoft(file_id,bot,update)


def send_image_to_microsoft(id,bot,update):
  global SESSION_ID
  global send_image
  print id
  mybot = bots.Bot(token=apis.telegram_key)
  r = mybot.getFile(id)
  if send_image:
    wordlist = cv.analyzeImages(r['file_path'])
    converted_wordlist = parse(",".join(wordlist),SESSION_ID)
    print converted_wordlist
    bot.sendMessage(chat_id=update.message.chat_id,text = converted_wordlist['result']['fulfillment']['speech'])
    for x in converted_wordlist['result']['parameters']['location_keywords']:
     collate_voting(x)

def terminate_voting(bot,update):
  global send_image
  global tag_collection
  global location_votes
  global phase_2
  global final_loc
  print tag_collection
  if not phase_2:
    ai_reply = parse('exit_open_floor',SESSION_ID)
    bot.sendMessage(chat_id=update.message.chat_id,text = ai_reply['result']['fulfillment']['speech'])
    start_location_vote(bot,update,main.findLocation(tag_collection))
    send_image = False
  else:
    print location_votes
    global my_locations
    ai_reply = parse('begin_standard_planning',SESSION_ID)
    print my_locations
    final_loc = my_locations[int(max(location_votes.iterkeys(), key=(lambda key: location_votes[key])))-1]
    # print final_loc
    # bot.sendMessage(chat_id=update.message.chat_id,text = "Voting has ended! "+ final_loc +" has won!")
    bot.sendMessage(chat_id=update.message.chat_id,text = ai_reply['result']['fulfillment']['speech'])
    phase_2 = False


def start_location_vote(bot,update,locations):
  global phase_2 
  global my_locations
  phase_2 = True
  message = ""
  counter = 1
  my_locations = locations
  for x in locations:
    message += str(counter)+") "+x +"\n"
    counter += 1
  bot.sendMessage(chat_id=update.message.chat_id,text = "Please reply with the number of the destination you wish to vote for:\n"+message)

def collate_phase2_voting(loc_id):
  global location_votes
  if loc_id in location_votes:
    location_votes[loc_id] +=1
  else:
    location_votes[loc_id] = 1

def collate_voting(tag):
  global tag_collection
  tag_collection += [tag]

def open_floor_voting(bot,update):
  global SESSION_ID
  global send_image
  ai_reply = parse('open floor',SESSION_ID)
  send_image = True
  bot.sendMessage(chat_id=update.message.chat_id,text = ai_reply['result']['fulfillment']['speech'])  



dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
start_handler = tele.CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()

image_handler = tele.MessageHandler([tele.Filters.photo],handle_images)
dispatcher.add_handler(image_handler)
document_handler = tele.MessageHandler([tele.Filters.document],handle_documents)
dispatcher.add_handler(document_handler)
text_handler = tele.MessageHandler([tele.Filters.text], send_to_ai)
dispatcher.add_handler(text_handler)
terminate_handler = tele.CommandHandler('endvoting', terminate_voting)
dispatcher.add_handler(terminate_handler)
open_floor_handler = tele.CommandHandler('startvoting', open_floor_voting)
dispatcher.add_handler(open_floor_handler)







# print parse("hello")["result"]["fulfillment"]["speech"]