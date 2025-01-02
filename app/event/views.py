import os
import uuid

import arrow

import boto3
from datetime import datetime

from flask import render_template, flash, redirect, url_for, request, make_response, jsonify
from linebot.v3.messaging import ApiClient, MessagingApi, PushMessageRequest, TextMessage, Configuration, FlexMessage, \
    FlexContainer
from sqlalchemy_utils.types.arrow import arrow

from app.event import event_blueprint as event
from app.event.forms import ParticipantForm, TicketClaimForm
from app.event.models import *

configuration = Configuration(access_token=os.environ.get('LINE_MESSAGE_ACCESS_TOKEN'))


@event.route('/upcoming')
def list_upcoming_events():
    events = Event.query.filter(Event.start_datetime >= datetime.now()).all()
    return render_template('event/upcoming.html', events=events)


@event.route('/events/<int:event_id>/register', methods=['GET', 'POST'])
def register_event(event_id):
    event = Event.query.get(event_id)
    form = ParticipantForm()
    if form.validate_on_submit():
        participant = EventParticipant.query.filter_by(line_id=form.line_id.data,
                                                       event_id=event_id).first()
        if not participant:
            participant = EventParticipant(event_id=event_id)
            form.populate_obj(participant)
            db.session.add(participant)
            for i in range(form.number.data):
                purchased_datetime = arrow.now('Asia/Bangkok').datetime
                ticket = EventTicket(event_id=event_id, participant=participant, create_datetime=purchased_datetime)
                ticket.generate_ticket_number(event)
                db.session.add(ticket)
            db.session.commit()
            tickets = []
            for t in participant.purchased_tickets.filter_by(cancel_datetime=None):
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
                                                "text": f"{t.create_datetime.strftime('%d/%m/%Y %H:%M')}",
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
                                                "text": "Payment",
                                                "wrap": True,
                                                "color": "#8c8c8c",
                                                "size": "md",
                                                "flex": 2
                                            },
                                            {
                                                "type": "text",
                                                "text": f"{t.payment_datetime.strftime('%d/%m/%Y %H:%M') if t.payment_datetime else 'pending'}",
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
                                    "text": f"cancel ticket:{t.ticket_number}"
                                }
                            },
                            {
                                "type": "button",
                                "style": "link",
                                "height": "sm",
                                "action": {
                                    "type": "clipboard",
                                    "label": "คัดลอกเพื่อส่งต่อให้เพื่อน",
                                    "clipboardText": f"https://liff.line.me/2006693395-RZwO4OEj/event/events/{t.event_id}/tickets/{t.ticket_number}/claim"
                                }
                            }
                        ]
                    }
                }
                tickets.append(ticket)
            bubble = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "INVOICE" if participant.total_amount_due else "RECEIPT",
                            "weight": "bold",
                            "color": "#1DB446",
                            "size": "sm"
                        },
                        {
                            "type": "text",
                            "text": "ยอดจองบัตร",
                            "weight": "bold",
                            "size": "xxl",
                            "margin": "md"
                        },
                        {
                            "type": "separator",
                            "margin": "xxl"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "xxl",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "margin": "xxl",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "ITEMS",
                                            "size": "sm",
                                            "color": "#555555"
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{participant.purchased_tickets.filter_by(cancel_datetime=None).count()}",
                                            "size": "sm",
                                            "color": "#111111",
                                            "align": "end"
                                        }
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "TOTAL",
                                            "size": "sm",
                                            "color": "#555555"
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{participant.total_balance}",
                                            "size": "sm",
                                            "color": "#111111",
                                            "align": "end"
                                        }
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "BALANCE DUE",
                                            "size": "sm",
                                            "color": "#555555"
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{participant.total_amount_due}",
                                            "size": "sm",
                                            "color": "#111111",
                                            "align": "end"
                                        }
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "PAID",
                                            "size": "sm",
                                            "color": "#555555"
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{participant.total_balance - participant.total_amount_due}",
                                            "size": "sm",
                                            "color": "#111111",
                                            "align": "end"
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "separator",
                            "margin": "xxl"
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "margin": "md",
                            "contents": [
                                {
                                    "type": "button",
                                    "style": "link",
                                    "height": "sm",
                                    "action": {
                                        "type": "uri",
                                        "label": "ชำระเงิน",
                                        "uri": f"https://liff.line.me/2006693395-RZwO4OEj/event/events/{event_id}/participants/{participant.id}/ticket-payment"
                                    }
                                },
                            ]
                        }
                    ]
                },
                "styles": {
                    "footer": {
                        "separator": True
                    }
                }
            }
            tickets.append(bubble)
            message = FlexMessage(alt_text=f'Purchased Tickets',
                                  contents=FlexContainer.from_dict({'type': 'carousel', 'contents': tickets}))
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                push_message_request = PushMessageRequest(to=participant.line_id, messages=[
                    TextMessage(text='ลงทะเบียนเรียบร้อยแล้ว'), message])
                try:
                    api_response = line_bot_api.push_message(push_message_request)
                except Exception as e:
                    print(f'Exception while sending MessageApi->push_message {e}')
            resp = make_response()
            resp.headers['HX-Trigger'] = 'closeLIFFWindow'
            return resp

    return render_template('event/register_form.html', form=form, event=event)


@event.route('/events/<int:event_id>/participants/<int:participant_id>/add-ticket', methods=['GET'])
def add_ticket(event_id, participant_id):
    participant = EventParticipant.query.get(participant_id)
    bubble = {
        'type': 'text',
        'text': f'คุณได้ลงทะเบียนแล้ว คุณต้องการจองบัตรเพิ่มจำนวนเท่าใด',
        'quickReply': {
            'items': [
                {
                    'type': 'action',
                    'action': {
                        'type': 'message',
                        'label': 'ไม่ต้องการ',
                        'text': 'No'
                    }
                },
                {
                    'type': 'action',
                    'action': {
                        'type': 'message',
                        'label': f'1',
                        'text': f'add ticket:{event_id}:1'
                    }
                },
                {
                    'type': 'action',
                    'action': {
                        'type': 'message',
                        'label': f'2',
                        'text': f'add ticket:{event_id}:2'
                    }
                },
                {
                    'type': 'action',
                    'action': {
                        'type': 'message',
                        'label': f'3',
                        'text': f'add ticket:{event_id}:3'
                    }
                },
                {
                    'type': 'action',
                    'action': {
                        'type': 'message',
                        'label': f'4',
                        'text': f'add ticket:{event_id}:4'
                    }
                },
                {
                    'type': 'action',
                    'action': {
                        'type': 'message',
                        'label': f'5',
                        'text': f'add ticket:{event_id}:5'
                    }
                },
            ]
        }
    }
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        push_message_request = PushMessageRequest(to=participant.line_id,
                                                  messages=[TextMessage.from_dict(bubble)])
        try:
            api_response = line_bot_api.push_message(push_message_request)
        except Exception as e:
            print(f'Exception while sending MessageApi->push_message {e}')
    resp = make_response()
    resp.headers['HX-Trigger'] = 'closeLIFFWindow'
    return resp


@event.route('/events/<int:event_id>/line-id/<line_id>/check-participant', methods=['GET'])
def check_participant(event_id, line_id):
    participant = EventParticipant.query.filter_by(line_id=line_id, event_id=event_id).first()
    resp = make_response()
    if participant:
        add_ticket_url = url_for('event.add_ticket', event_id=event_id, participant_id=participant.id)
        template = f"""
            <h1 class='title has-text-centered'>คุณได้ลงทะเบียนแล้ว</h1>
            <p>
            คุณได้ทำการจองบัตรไว้เป็นจำนวน {participant.purchased_tickets.filter_by(cancel_datetime=None).count()} ใบ
            </p>
            <div class='buttons is-centered'>
                <button onclick='closeLIFFWindow()' class='button is-medium'>ปิดหน้าต่าง</button>
                <button hx-get='{add_ticket_url}' class='button is-medium is-info'>จองบัตรเพิ่ม</button>
            </div>
            """
        resp = make_response(template)
        return resp
    else:
        resp.headers['HX-Reswap'] = 'none'
    return resp


@event.route('/events/<int:event_id>/check-tickets')
def check_tickets(event_id):
    telephone = request.args.get('telephone')
    participant = EventParticipant.query.filter_by(telephone=telephone, event_id=event_id).first()
    if participant:
        return redirect(url_for('event.show_tickets', event_id=event_id, participant_id=participant.id))
    else:
        flash('ไม่พบรายการลงทะเบียนในกิจกรรมนี้', 'danger')
        return redirect(url_for('event.register_event', event_id=event_id))


@event.route('/events/<int:event_id>/participants/<int:participant_id>/ticket-payment')
def ticket_payment(event_id, participant_id):
    event = Event.query.get(event_id)
    participant = EventParticipant.query.get(participant_id)
    return render_template('event/tickets.html', event=event, participant=participant)


@event.route('/events/<int:event_id>/tickets/<ticket_number>/claim', methods=['GET', 'POST'])
def claim_ticket(event_id, ticket_number):
    form = TicketClaimForm()
    ticket = EventTicket.query.filter_by(ticket_number=ticket_number).first()
    event = Event.query.get(event_id)
    if form.validate_on_submit():
        participant = EventParticipant.query.filter_by(event_id=event_id,
                                                       line_id=form.line_id.data).first()
        if not participant:
            participant = EventParticipant(event_id=event_id)
            form.populate_obj(participant)
            participant.holding_ticket = ticket
            db.session.add(participant)
            db.session.commit()
        else:
            if not participant.holding_ticket:
                participant.holding_ticket = ticket
                db.session.add(participant)
                db.session.commit()
            else:
                message = TextMessage(text='คุณได้ถือบัตรอยู่แล้วหนึ่งใบ')
        resp = make_response()
        resp.headers['HX-Redirect'] = url_for('event.show_ticket_detail', event_id=event_id,
                                              ticket_number=ticket_number)
        return resp
    return render_template('event/claim_ticket.html', event=event, ticket_number=ticket_number, form=form)


@event.route('/events/<int:event_id>/tickets/<ticket_number>/detail')
def show_ticket_detail(event_id, ticket_number):
    ticket = EventTicket.query.filter_by(ticket_number=ticket_number).first()
    return render_template('event/ticket_detail.html', ticket=ticket)


@event.route('/events/<int:event_id>/tickets/<ticket_number>/line-id/<line_id>/check-holder')
def check_ticket_holder(event_id, ticket_number, line_id):
    if request.headers.get('HX-Request') == 'true':
        resp = make_response()
        participant = EventParticipant.query.filter_by(line_id=line_id, event_id=event_id).first()
        if not participant.holding_ticket:
            resp.headers['HX-Reswap'] = 'none'
        else:
            resp.headers['HX-Redirect'] = url_for('event.show_ticket_detail', event_id=event_id,
                                                  ticket_number=ticket_number)
        return resp


@event.route('/events/<int:event_id>/participants/<int:participant_id>/payments/slip', methods=['POST'])
def upload_payment_slip(event_id, participant_id):
    s3_client = boto3.client('s3', aws_access_key_id=os.environ.get('BUCKETEER_AWS_ACCESS_KEY_ID'),
                             aws_secret_access_key=os.environ.get('BUCKETEER_AWS_SECRET_ACCESS_KEY'),
                             region_name=os.environ.get('BUCKETEER_AWS_REGION'))
    _file = request.files['file']
    amount = request.form.get('amount')
    if _file:
        filename = _file.filename
        key = uuid.uuid4()
        s3_client.upload_fileobj(_file, os.environ.get('BUCKETEER_BUCKET_NAME'), str(key))
        payment = EventTicketPayment(participant_id=participant_id,
                                     amount=float(amount),
                                     key=key,
                                     filename=filename)
        payment.create_datetime = arrow.now('Asia/Bangkok').datetime
        db.session.add(payment)
    db.session.commit()
    participant = EventParticipant.query.get(participant_id)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        push_message_request = PushMessageRequest(to=participant.line_id, messages=[
            TextMessage(text='ได้รับข้อมูลเรียบร้อยแล้วกรุณารอการตรวจสอบ')])
        try:
            api_response = line_bot_api.push_message(push_message_request)
        except Exception as e:
            print(f'Exception while sending MessageApi->push_message {e}')
    resp = make_response()
    resp.headers['HX-Trigger'] = 'closeLIFFWindow'
    return resp
    # return redirect(url_for('line_api.confirm_payment', event_id=event_id, participant_id=participant_id))
