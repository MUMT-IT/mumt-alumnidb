import os
import random
from datetime import datetime

from flask import request, abort
from pytz import timezone

from app import app, db
from app.line_api import line_api_blueprint as api
from app.event.models import Event, EventTicket, EventParticipant

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage, FlexMessage, FlexContainer
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

configuration = Configuration(access_token=os.environ.get('LINE_MESSAGE_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_MESSAGE_CHANNEL_SECRET'))


@api.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    if event.message.text == 'upcoming events':
        boxes = []
        for e in Event.query.filter(Event.start_datetime >= datetime.now(tz=timezone('Asia/Bangkok'))):
            box = {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": "https://developers-resource.landpress.line.me/fx/clip/clip10.jpg",
                    "size": "full",
                    "aspectMode": "cover",
                    "aspectRatio": "320:213"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"{e.name}",
                            "weight": "bold",
                            "size": "lg",
                            "wrap": True
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "Venue",
                                            "wrap": True,
                                            "color": "#8c8c8c",
                                            "size": "md",
                                            "flex": 1
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{e.location}",
                                            "wrap": True,
                                            "size": "md",
                                            "flex": 5
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "Time",
                                            "wrap": True,
                                            "color": "#8c8c8c",
                                            "size": "md",
                                            "flex": 1
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{e.time}",
                                            "wrap": True,
                                            "size": "md",
                                            "flex": 5
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    "spacing": "sm",
                    "paddingAll": "13px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                                "type": "uri",
                                "label": "ลงทะเบียน",
                                "uri": f"https://liff.line.me/2006693395-RZwO4OEj/event/events/{e.id}/register"
                            }
                        },
                        {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                                "type": "message",
                                "label": "เช็คบัตรที่จอง",
                                "text": f"tickets:{e.id}"
                            }
                        }
                    ]
                }
            }
            boxes.append(box)
        message = FlexMessage(alt_text=f'Upcoming Events',
                              contents=FlexContainer.from_dict({'type': 'carousel', 'contents': boxes}))
    elif event.message.text.startswith('tickets:'):
        line_id = event.source.user_id
        event_id = event.message.text.split(':')[-1]
        participant = EventParticipant.query.filter_by(line_id=line_id).first()
        tickets = []
        for t in participant.purchased_tickets.filter_by(event_id=event_id):
            ticket = {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": "https://developers-resource.landpress.line.me/fx/clip/clip10.jpg",
                    "size": "full",
                    "aspectMode": "cover",
                    "aspectRatio": "320:213"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"{t.ticket_number}",
                            "weight": "bold",
                            "size": "lg",
                            "wrap": True
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "Purchaser",
                                            "wrap": True,
                                            "color": "#8c8c8c",
                                            "size": "md",
                                            "flex": 2
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{t.participant}",
                                            "wrap": True,
                                            "size": "md",
                                            "flex": 4
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "Purchased",
                                            "wrap": True,
                                            "color": "#8c8c8c",
                                            "size": "md",
                                            "flex": 2
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{t.create_datetime}",
                                            "wrap": True,
                                            "size": "md",
                                            "flex": 4
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "Paid",
                                            "wrap": True,
                                            "color": "#8c8c8c",
                                            "size": "md",
                                            "flex": 2
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{t.payment_datetime or 'pending'}",
                                            "wrap": True,
                                            "size": "md",
                                            "flex": 4
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "Holder",
                                            "wrap": True,
                                            "color": "#8c8c8c",
                                            "size": "md",
                                            "flex": 2
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{t.holder}",
                                            "wrap": True,
                                            "size": "md",
                                            "flex": 4
                                        }
                                    ]
                                }
                            ]
                        },
                    ],
                    "spacing": "sm",
                    "paddingAll": "13px"
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                                "type": "message",
                                "label": "เคลมบัตร",
                                "text": f"claim ticket:{t.ticket_number}"
                            }
                        },
                        {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                                "type": "message",
                                "label": "ยกเลิกบัตร",
                                "text": f"cancel ticket:{t.id}"
                            }
                        }
                    ]
                }
            }
            tickets.append(ticket)
        message = FlexMessage(alt_text=f'Purchased Tickets',
                              contents=FlexContainer.from_dict({'type': 'carousel', 'contents': tickets}))
    elif event.message.text.startswith('claim ticket'):
        ticket_number = event.message.text.split(':')[-1]
        ticket = EventTicket.query.filter_by(ticket_number=ticket_number).first()
        bubble = {
            'type': 'text',
            'text': f'คุณต้องการระบุว่าเป็นเจ้าของบัตรหมายเลข {ticket.ticket_number} ใช่หรือไม่ บัตรหนึ่งใบสามารถมีเจ้าของได้เพียงคนเดียวที่จะใช้เช็คอินเข้างาน',
            'quickReply': {
                'items': [
                    {
                        'type': 'action',
                        'action': {
                            'type': 'message',
                            'label': f'Yes',
                            'text': f'Yes, claim the ticket number {ticket.ticket_number}'
                        }
                    },
                    {
                        'type': 'action',
                        'action': {
                            'type': 'message',
                            'label': 'No.',
                            'text': 'No'
                        }
                    },
                ]
            }
        }
        message = TextMessage.from_dict(bubble)
    elif event.message.text.startswith('Yes, claim the ticket number'):
        ticket_number = event.message.text.split(' ')[-1]
        ticket = EventTicket.query.filter_by(ticket_number=ticket_number).first()
        if ticket:
            holder = EventParticipant.query.filter_by(line_id=event.source.user_id,
                                                      event=ticket.event).first()
            if holder.holding_ticket and holder.holding_ticket == ticket:
                if holder.holding_ticket == ticket:
                    message = TextMessage(text=f'คุณได้คือครองบัตรนี้อยู่แล้ว ')
            else:
                if holder.holding_ticket:
                    holding_message = f'คุณได้ปล่อยบัตรหมายเลข {holder.holding_ticket.ticket_number} แล้ว '
                else:
                    holding_message = ''
                ticket.holder = holder
                db.session.add(ticket)
                db.session.commit()
                msg = 'เรียบร้อย! ' + holding_message + f'บัตรที่คุณถือตอนนี้คือหมายเลข {ticket.ticket_number} คุณต้องการดูรายการบัตรทั้งหมดหรือไม่'
                bubble = {
                    'type': 'text',
                    'text': msg,
                    'quickReply': {
                        'items': [
                            {
                                'type': 'action',
                                'action': {
                                    'type': 'message',
                                    'label': f'Yes',
                                    'text': f'tickets:{ticket.event_id}'
                                }
                            },
                            {
                                'type': 'action',
                                'action': {
                                    'type': 'message',
                                    'label': 'No.',
                                    'text': 'No'
                                }
                            },
                        ]
                    }
                }
                message = TextMessage.from_dict(bubble)
    else:
        fine_responses = ['ได้เลยครับ', 'Ok.', 'ไม่มีปัญหา', 'ยินดีรับใช้ครับ']
        error_responses = [
            'Oops! Sorry. I am just a simple chatbot. Try again.',
            'ขออภัย ผมไม่สามารถทำตามคำสั่งได้',
            'ผมไม่เข้าใจครับ กรุณาลองอีกครั้ง',
            'ผมเป็นบอทที่ทำตามคำสั่งเฉพาะเท่านั้น กรุณาลองใหม่นะครับ'
        ]
        message = TextMessage(text=random.choice(fine_responses) if event.message.text == 'No' else random.choice(error_responses))

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[message]
            )
        )
