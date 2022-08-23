from curses.ascii import isdigit
import os
import re
import json
import random
# from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
from influxdb import InfluxDBClient
from pyquery import PyQuery
from datetime import datetime, timedelta


"""
init DB
"""


class DB():
    def __init__(self, ip, port, user, password, db_name):
        self.client = InfluxDBClient(ip, port, user, password, db_name)
        print('Influx DB init.....')

    def insertData(self, data):
        """
        [data] should be a list of datapoint JSON,
        "measurement": means table name in db
        "tags": you can add some tag as key
        "fields": data that you want to store
        """
        if self.client.write_points(data):
            return True
        else:
            print('Falied to write data')
            return False

    def queryData(self, query):
        """
        [query] should be a SQL like query string
        """
        return self.client.query(query)


db = DB('127.0.0.1', 8086, 'root', '', 'accounting_db')
# load_dotenv()  # Load your local environment variables

# CHANNEL_TOKEN = os.environ.get('LINE_TOKEN')
# CHANNEL_SECRET = os.getenv('LINE_SECRET')

CHANNEL_TOKEN = 'r0aiE8HapBxBhxZbTXKWl9rn45ZA4cOb3rrPytENhIkwlvQHv+TTzjwZOEnnZplUE2q0ivdq6gyiXmNZQjlId3gopVDAFleDw8kvqlIyCHGA+cdz99wbplQARWmvGyynnB7dpt2u4KmLb2d/0JkD6gdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = '11e237d228b4a906c76158f8db6315bf'

app = FastAPI()


# Connect Your API to Line Developer API by Token
My_LineBotAPI = LineBotApi(CHANNEL_TOKEN)
# Event handler connect to Line Bot by Secret key
handler = WebhookHandler(CHANNEL_SECRET)

# Events for msg reply
my_event = ['#note', '#report', '#delete', '#sum']

# Line Developer Webhook Entry Point


@app.post('/')
async def callback(request: Request):
    body = await request.body()  # Get request
    # Get message signature from Line Server
    signature = request.headers.get('X-Line-Signature', '')
    try:
        # Handler handle any message from LineBot and
        handler.handle(body.decode('utf-8'), signature)
    except InvalidSignatureError:
        raise HTTPException(404, detail='LineBot Handle Body Error !')
    return 'OK'

# All message events are handling at here !


@handler.add(MessageEvent, message=TextMessage)
def handle_textmessage(event):
    ''' Basic Message Reply
    message = TextSendMessage(text= event.message.text)
    My_LineBotAPI.reply_message(
        event.reply_token,
        message
    )
    '''
    # Split message by white space
    recieve_message = str(event.message.text).split(' ')
    # Get first splitted message as command
    case_ = recieve_message[0].lower().strip()

    # Case 1 : #note [event] [+/-] [money]
    if re.match(my_event[0], case_):
        event_ = recieve_message[1]
        op = recieve_message[2]
        money = int(recieve_message[3])
        # process +/1
        if op == '-':
            money *= -1
        # get user ID
        user_id = event.source.user_id

        # build data
        data = [
            {
                "measurement": "accounting_items",
                "tags": {
                    "user": str(user_id),
                },
                "fields": {
                    "event": str(event_),
                    "money": money
                }
            }
        ]
        if db.insertData(data):
            # successed
            My_LineBotAPI.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="Write to DB Successfully!"
                )
            )

    # Case 2 : #report list all records
    elif re.match(my_event[1], case_):
        user_id = event.source.user_id
        query_str = """
        SELECT * FROM accounting_items 
        """
        result = db.queryData(query_str)
        points = result.get_points(tags={'user': str(user_id)})

        reply_text = ''
        for i, point in enumerate(points):
            time = point['time']
            event = point['event']
            money = point['money']
            reply_text += f'[{i}] -> [{time}] : {event_} {money}\n'

        My_LineBotAPI.reply_message(
            event.reply_token,
            TextSendMessage(
                text=reply_text
            )
        )

    # Case 3 : #delete [item]
    elif re.match(my_event[2], case_):
        item = recieve_message[1]

        db.queryData(
            f"SELECT * INTO remain_items FROM accounting_items WHERE \"event\"!='{item}\'group by *")
        db.queryData("DROP measurement accounting_items")
        result = db.queryData(
            "SELECT * INTO accounting_items FROM remain_items group by *")
        db.queryData("DROP measurement remain_items")

        My_LineBotAPI.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"Delete {item} from DB Successfully!"
            )
        )

    # Case 4 : #sum [time shift]
    elif re.match(my_event[3], case_):
        time_shift = recieve_message[1]
        d = datetime.utcnow() - timedelta(days=int(time_shift))
        user_id = event.source.user_id

        query_str = f"SELECT * FROM accounting_items WHERE time>=\'{d}\'"
        result = db.queryData(query_str)
        points = result.get_points(tags={'user': str(user_id)})

        sum = 0
        for i, point in enumerate(points):
            sum += point['money']

        My_LineBotAPI.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"Total balance in {time_shift} is {sum}."
            )
        )

# Line Sticker Class


class My_Sticker:
    def __init__(self, p_id: str, s_id: str):
        self.type = 'sticker'
        self.packageID = p_id
        self.stickerID = s_id


'''
See more about Line Sticker, references below
> Line Developer Message API, https://developers.line.biz/en/reference/messaging-api/#sticker-message
> Line Bot Free Stickers, https://developers.line.biz/en/docs/messaging-api/sticker-list/
'''
# Add stickers into my_sticker list
my_sticker = [My_Sticker(p_id='446', s_id='1995'), My_Sticker(p_id='446', s_id='2012'),
              My_Sticker(p_id='446', s_id='2024'), My_Sticker(
                  p_id='446', s_id='2027'),
              My_Sticker(p_id='789', s_id='10857'), My_Sticker(
                  p_id='789', s_id='10877'),
              My_Sticker(p_id='789', s_id='10881'), My_Sticker(
                  p_id='789', s_id='10885'),
              ]

# Line Sticker Event


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    # Random choice a sticker from my_sticker list
    ran_sticker = random.choice(my_sticker)
    # Reply Sticker Message
    My_LineBotAPI.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=ran_sticker.packageID,
            sticker_id=ran_sticker.stickerID
        )
    )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app='main:app', reload=True, host='0.0.0.0', port=8787)
