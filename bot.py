from telegram.ext import (
  Updater,
  CommandHandler,
  MessageHandler,
  ConversationHandler,
  CallbackQueryHandler,
  Filters )
  
from telegram import (
     InlineKeyboardButton,
     InlineKeyboardMarkup,
     ReplyKeyboardRemove )
     
from telegram.utils.helpers import mention_markdown
import psycopg2
from decouple import config
import logging
import sys
import datetime

TOKEN=config("TOKEN")
APP_URL=config("APP_URL","")
PORT = config("PORT",5000)
ADMIN_CHAT_ID=config("ADMIN_CHAT_ID")
DATABASE_URL=config ("DATABASE_URL")

CON = psycopg2.connect(DATABASE_URL)
CURS = CON.cursor()
CHOOSED_QUES={}
##Logging##
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

SELECTOR,SUBMIT=range(2)

def insert_query(q,val=None):
  CURS.execute(q,val)
  CON.commit()
  return 1
def fetch_database(q):
  CURS.execute(q)
  print(q)
  return CURS.fetchall()
  
def start(update,context):
  update.message.reply_text(f"""
Hello {update.message.from_user.first_name }!!
I am Binex Bot ,I am here to help you to submit your coding solutions very easily. To submit your solution send /submit_code
OurChannel: <a href='https://t.me/Bin_Ex'>Binex - Channel</a>
Telegram group: <a href='https://t.me/Bin_Ex_group'>Binex - Group</a>
Quora Space: <a href='https://quora.com/q/binex'>Binex - Quora</a>
  """,parse_mode="HTML")
##############################

def show_challenges(update,context):
  print("show_challenges")
  challenges = fetch_database("SELECT * FROM challenges")
  keyboard= [[InlineKeyboardButton(i[1],callback_data=i[0])] for i in challenges]
  reply_markup = InlineKeyboardMarkup(keyboard)
  if update.message:
    update.message.reply_text("List of all challenges",reply_markup=reply_markup)
  else:
    update.callback_query.answer()
    update.callback_query.edit_message_text("List of all challenges",reply_markup=reply_markup)
  return SELECTOR


def show_ques(update, context):
  print("show_ques")
  query=update.callback_query
  query.answer()
  challenge_id = query.data
  questions = fetch_database(f"SELECT * FROM problems WHERE challenge_id={challenge_id}")
  keyboard =[]
  for pid,name,code,stmt,cid,link in questions:
    keyboard.append([InlineKeyboardButton(name,callback_data=code)])
  keyboard.append([InlineKeyboardButton("Back",callback_data="back")])
  reply_markup = InlineKeyboardMarkup(keyboard)
  query.edit_message_text("Select a question",reply_markup=reply_markup)
  return SELECTOR
  
def submit_code(update, context):
  print("submit_code")
  query = update.callback_query
  prob_code = query.data
  CHOOSED_QUES[query.from_user.id] = prob_code
  prob_name = fetch_database(f"SELECT problem_name from problems WHERE problem_code='{prob_code}'")
  query.edit_message_text(f"Please Send the solution of Problem: {prob_name} ({prob_code})")
  return SUBMIT
  
def submitted(update,context):
  print("Submitting")
  solution=update.message.text
  user = update.message.from_user
  user_id=user.id 
  name = user.first_name+" "+user.last_name
  time = datetime.datetime.now()
  username=user.username
  prob_code=CHOOSED_QUES[user_id]
  prob_link,prob_name=fetch_database(f"SELECT problem_link,problem_name from problems WHERE problem_code='{prob_code}'")[0]
  print(prob_link)
  try:
    insert_query("INSERT INTO solution")
  except:
    pass
  text = f"Solution by: {mention_markdown(int(user_id),name)}\nProblem: [{prob_name}]({prob_link})\n{solution}"
  update.message.reply_text("Your code has been submitted",)
  context.bot.sendMessage(ADMIN_CHAT_ID,text=text,parse_mode="Markdown",disable_web_page_preview=True)
  return ConversationHandler.END
  

def cancel (update,context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I would like to meet you again', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END
def deep_link(update, context):
  text = update.message.text.split()
  if len(text)==1:
    start(update,context)
  else:
    prob_code = text[1]
    update.message.reply_text("Please Send the solution of Problem: "+prob_code)
    CHOOSED_QUES[update.message.from_user.id] = prob_code
    return SUBMIT
def main():
  updater = Updater(TOKEN)
  dispatcher = updater.dispatcher
  
  solution_handler = ConversationHandler(
    entry_points=[CommandHandler("submit_code",show_challenges),
      CommandHandler("start",deep_link)
],
    states={
    SELECTOR:[
    CallbackQueryHandler(show_ques,pattern="^[0-9]+$"),
    CallbackQueryHandler(submit_code,pattern="([0-9]+)([A-Za-z])+"),
    CallbackQueryHandler(show_challenges,pattern="back")
    ],
  #  SELECTOR:CallbackQueryHandler(callback)
      SUBMIT:[MessageHandler(Filters.text&(~Filters.command), submitted)]
      },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True
    )
    
    
  dispatcher.add_handler(solution_handler)
  if len(sys.argv)>1 and sys.argv[1]=="-p":
     updater.start_polling()
  else:
    updater.start_webhook(listen='0.0.0.0',port=int(PORT),url_path=TOKEN)
    updater.bot.setWebhook(APP_URL+TOKEN)
  updater.idle()
  
if __name__=='__main__':
  main()