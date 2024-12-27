import os
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
        for t in participant.owned_tickets.filter_by(event_id=event_id):
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
                                "text": f"claim ticket:{t.id}"
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
        ticket_id = event.message.text.split(':')[-1]
        ticket = EventTicket.query.get(int(ticket_id))
        bubble = {
            'type': 'text',
            'text': f'คุณต้องการระบุว่าเป็นเจ้าของบัตรหมายเลข {ticket.ticket_number} ใช่หรือไม่ บัตรหนึ่งใบสามารถมีเจ้าของได้เพียงคนเดียวเท่านั้น',
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
            ticket.participant.ticket_id = None
            new_owner = EventParticipant.query.filter_by(line_id=event.source.user_id).first()
            new_owner.ticket_id = ticket.id
            db.session.add(ticket.participant)
            db.session.add(new_owner)
            db.session.commit()
            message = TextMessage(text='All set!')
    else:
        message = TextMessage(text=event.message.text)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[message]
            )
        )