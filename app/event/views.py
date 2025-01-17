import base64
import io
import os
import uuid

import arrow

import boto3
from datetime import datetime

import pytz
from flask import render_template, flash, redirect, url_for, request, make_response, jsonify, send_file, current_app
from flask_login import login_required
from flask_wtf.csrf import generate_csrf
from linebot.v3.messaging import ApiClient, MessagingApi, PushMessageRequest, TextMessage, Configuration, FlexMessage, \
    FlexContainer
from qrcode.main import QRCode
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import or_
from sqlalchemy.event import Events
from sqlalchemy_utils.types.arrow import arrow

from app import app
from app.member.models import MemberInfo
from app.event import event_blueprint as event
from app.event.forms import ParticipantForm, TicketClaimForm, create_approve_payment_form
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
        member = MemberInfo.query.filter_by(line_id=form.line_id.data).first()
        if not member:
            member = MemberInfo()
        if form.group.data == 'ศิษย์เก่า' and form.consent.data:
            form.populate_obj(member)
            db.session.add(member)
            db.session.commit()
        participant = EventParticipant.query.filter_by(line_id=form.line_id.data,
                                                       event_id=event_id).first()
        if not participant:
            participant = EventParticipant(event_id=event_id)
            form.populate_obj(participant)
            participant.register_datetime = arrow.now('Asia/Bangkok').datetime
            db.session.add(participant)
            event_ = Event.query.get(event_id)
            for i in range(form.number.data):
                purchased_datetime = arrow.now('Asia/Bangkok').datetime
                ticket = EventTicket(event_id=event_id, participant=participant, create_datetime=purchased_datetime)
                event_.last_ticket_number += 1
                ticket.ticket_number = f'{event_.id}-{event_.last_ticket_number:04d}'
                db.session.add(ticket)
                db.session.add(event_)
            db.session.commit()
            tickets = []
            for t in participant.purchased_tickets.filter_by(cancel_datetime=None):
                ticket = {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": f"{url_for('static', filename='img/tickets-resized.png', _external=True, _scheme='https')}",
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


@event.route('/events/<int:event_id>/register-form/line-id/<line_id>', methods=['GET'])
def load_register_form(event_id, line_id):
    participant = EventParticipant.query.filter_by(line_id=line_id, event_id=event_id).first()
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
        return template
    else:
        member = MemberInfo.query.filter_by(line_id=line_id).first()
        form = ParticipantForm(obj=member)
        return render_template('event/partials/register_form_part.html',
                               form=form, event_id=event_id, line_id=line_id)


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
    template_img_path = os.path.join(app.root_path, 'static/img/', 'mumt-rt-party-ticket.png')
    template_img = Image.open(template_img_path)
    I = ImageDraw.Draw(template_img)
    ticket_font = ImageFont.truetype(os.path.join(app.root_path, 'static/fonts/', 'BaiJamjuree-Bold.ttf'),
                                     size=72)
    name_font = ImageFont.truetype(os.path.join(app.root_path, 'static/fonts/', 'BaiJamjuree-Regular.ttf'),
                                   size=60)
    I.text((440, 1000), f'เลขบัตร {ticket.ticket_number}', fill=(0, 0, 0), font=ticket_font)
    holder_name = f'{ticket.holder.title}{ticket.holder.firstname}\n{ticket.holder.lastname}' if ticket.holder else 'ยังไม่ได้ลงทะเบียนผู้ถืิอบัตร'
    I.text((440, 1100), holder_name, fill=(0, 0, 0), font=name_font)
    bangkok = pytz.timezone('Asia/Bangkok')
    payment_datetime = ticket.payment_datetime.astimezone(bangkok).strftime("%d/%m/%Y %X") if ticket.payment_datetime else 'pending'
    I.text((440, 1300), f'PAYMENT {payment_datetime}', fill=(0, 0, 0), font=name_font)

    qr = QRCode(version=1, box_size=20, border=2)
    qr.add_data(ticket_number)
    qr.make()
    qr_img = qr.make_image()

    img_w, img_h = template_img.size
    qr_w, qr_h = qr_img.size

    # The qrcode.image cannot be pasted directly.
    # It has to be saved as PNG and opened using Image.open.
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_img = Image.open(qr_buffer)
    pos = ((img_w - qr_w) // 2, 1500)
    template_img.paste(qr_img, pos)

    buffer = io.BytesIO()
    template_img.save(buffer, format='PNG')
    qr_image_bytes = base64.b64encode(buffer.getvalue()).decode()

    return render_template('event/ticket_detail.html', ticket=ticket, qrcode=qr_image_bytes)


@event.route('/events/<int:event_id>/tickets/<ticket_number>/line-id/<line_id>/check-holder')
def check_ticket_holder(event_id, ticket_number, line_id):
    if request.headers.get('HX-Request') == 'true':
        resp = make_response()
        participant = EventParticipant.query.filter_by(line_id=line_id, event_id=event_id).first()
        if not participant.holding_ticket:
            resp.headers['HX-Reswap'] = 'none'
        else:
            resp.headers['HX-Redirect'] = url_for('event.show_ticket_detail',
                                                  event_id=event_id,
                                                  ticket_number=participant.holding_ticket.ticket_number)
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
                                     event_id=event_id,
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


@event.route('/events')
@login_required
def all_events():
    events = Event.query.order_by(Event.start_datetime.desc())
    return render_template('event/admin/events.html', events=events)


@event.route('/events/<int:event_id>/participants')
@login_required
def list_participants(event_id):
    event = Event.query.get(event_id)
    return render_template('event/admin/participants.html', event=event)


@event.route('/payments/<int:payment_id>/payment-approve-batch', methods=['GET', 'POST'])
@login_required
def approve_payment_batch(payment_id):
    payment = EventTicketPayment.query.get(payment_id)
    ApprovePaymentForm = create_approve_payment_form(payment.participant)
    form = ApprovePaymentForm()
    if request.method == 'GET':
        return render_template('event/admin/approve_payment_form.html', payment=payment, form=form)
    if request.method == 'POST':
        for ticket in form.tickets.data:
            ticket.payment_datetime = payment.create_datetime
            payment.approve_datetime = arrow.now('Asia/Bangkok').datetime
            db.session.add(ticket)
            db.session.add(payment)
            db.session.commit()
            if not current_app.debug:
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    push_message_request = PushMessageRequest(to=ticket.participant.line_id, messages=[
                        TextMessage(text=f'อนุมัติการชำระเงินบัตรหมายเลข {ticket.ticket_number} แล้ว')])
                    try:
                        api_response = line_bot_api.push_message(push_message_request)
                    except Exception as e:
                        print(f'Exception while sending MessageApi->push_message {e}')
                if ticket.holder and ticket.holder != ticket.participant:
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        push_message_request = PushMessageRequest(to=ticket.holder.line_id, messages=[
                            TextMessage(text=f'อนุมัติการชำระเงินบัตรหมายเลข {ticket.ticket_number} แล้ว')])
                        try:
                            api_response = line_bot_api.push_message(push_message_request)
                        except Exception as e:
                            print(f'Exception while sending MessageApi->push_message {e}')
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp


@event.route('/tickets/<int:ticket_id>/payment-approve', methods=['POST'])
@login_required
def approve_payment(ticket_id):
    ticket = EventTicket.query.get(ticket_id)
    ticket.payment_datetime = arrow.now('Asia/Bangkok').datetime
    payment = EventTicketPayment(event_id=ticket.event_id,
                                 create_datetime=ticket.payment_datetime,
                                 participant=ticket.holder,
                                 amount=ticket.event.ticket_price,
                                 walkin=True,
                                 approve_datetime=ticket.payment_datetime,
                                 )
    db.session.add(ticket)
    db.session.add(payment)
    db.session.commit()
    if not current_app.debug:
        line_id = ticket.holder.line_id if ticket.holder else ticket.participant.line_id
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            push_message_request = PushMessageRequest(to=line_id, messages=[
                TextMessage(text=f'อนุมัติการชำระเงินบัตรหมายเลข {ticket.ticket_number} แล้ว')])
            try:
                api_response = line_bot_api.push_message(push_message_request)
            except Exception as e:
                print(f'Exception while sending MessageApi->push_message {e}')
    checkin_url = url_for('event.checkin_ticket', ticket_id=ticket.id)
    template = f'''
    <a class="button is-rounded is-success"
        hx-indicator="this"
        hx-swap="outerHTML"
        hx-confirm="คุณแน่ใจว่าต้องการเช็คอินรายการนี้"
        hx-headers='{{"X-CSRF-Token": "{generate_csrf()}"}}'
        hx-post="{checkin_url}">
    เช็คอินเข้างาน
    </a>
    '''
    return template


@event.route('/tickets/<int:ticket_id>/checkin', methods=['POST'])
@login_required
def checkin_ticket(ticket_id):
    ticket = EventTicket.query.get(ticket_id)
    ticket.checkin_datetime = arrow.now('Asia/Bangkok').datetime
    db.session.add(ticket)
    db.session.commit()
    return ticket.checkin_datetime.strftime('%d/%m/%Y %X')


@event.route('/events/<int:event_id>/payments')
@login_required
def list_payments(event_id):
    event = Event.query.get(event_id)
    approved = request.args.get('approved', 'no')
    ticket_payments = event.ticket_payments
    if approved == 'yes':
        ticket_payments = ticket_payments.filter(EventTicketPayment.approve_datetime!=None)
    else:
        ticket_payments = ticket_payments.filter_by(approve_datetime=None)
    return render_template('event/admin/payments.html',
                           event=event,
                           ticket_payments=ticket_payments,
                           approved=approved)


@event.route('/ticket-payments/<int:participant_id>/check')
@login_required
def check_payment(participant_id):
    participant = EventParticipant.query.get(participant_id)
    return render_template('event/admin/check_payment.html', participant=participant)


@event.route('/ticket-payments/slip-download/<key>')
def download_file(key):
    download_filename = request.args.get('download_filename')
    s3_client = boto3.client('s3', aws_access_key_id=os.environ.get('BUCKETEER_AWS_ACCESS_KEY_ID'),
                             aws_secret_access_key=os.environ.get('BUCKETEER_AWS_SECRET_ACCESS_KEY'),
                             region_name=os.environ.get('BUCKETEER_AWS_REGION'))
    outfile = io.BytesIO()
    s3_client.download_fileobj(os.environ.get('BUCKETEER_BUCKET_NAME'), key, outfile)
    outfile.seek(0)
    return send_file(outfile, download_name=download_filename, as_attachment=True)


@event.route('/admin/events/<int:event_id>/participants/register', methods=['GET', 'POST'])
@login_required
def admin_register_participant(event_id):
    form = ParticipantForm()
    event = Event.query.get(event_id)
    if form.validate_on_submit():
        participant = EventParticipant(event_id=event_id)
        form.populate_obj(participant)
        if form.group.data == 'ศิษย์เก่า' and form.consent.data:
            member = MemberInfo()
            form.populate_obj(member)
            db.session.add(member)
        for i in range(form.number.data):
            purchased_datetime = arrow.now('Asia/Bangkok').datetime
            ticket = EventTicket(event_id=event_id, participant=participant, create_datetime=purchased_datetime)
            event.last_ticket_number += 1
            ticket.ticket_number = f'{event.id}-{event.last_ticket_number:04d}'
            db.session.add(ticket)
            db.session.add(event)
        db.session.commit()
        flash('ลงทะเบียนเรียบร้อยแล้ว กรุณาชำระเงินค่าบัตร', 'success')
        return redirect(url_for('event.check_payment', participant_id=participant.id))
    return render_template('event/admin/register_form.html', form=form, event=event)


@event.route('/admin/participants/<int:participant_id>/payment/new', methods=['GET', 'POST'])
@login_required
def admin_add_payment_record(participant_id):
    participant = EventParticipant.query.get(participant_id)
    if request.method == 'GET':
        return render_template('event/admin/modals/payment_form.html',
                               participant_id=participant_id)
    if request.method == 'POST':
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
                                         event_id=participant.event_id,
                                         amount=float(amount),
                                         key=key,
                                         filename=filename)
            payment.create_datetime = arrow.now('Asia/Bangkok').datetime
            db.session.add(payment)
        db.session.commit()
        resp = make_response()
        resp.headers['HX-Redirect'] = url_for('event.check_payment', participant_id=participant_id)
        return resp


@event.route('/admin/payments/<int:payment_id>/note', methods=['GET', 'POST'])
@login_required
def admin_add_payment_note(payment_id):
    payment = EventTicketPayment.query.get(payment_id)
    if request.method == 'POST':
        form = request.form
        payment.note = form.get('note')
        db.session.add(payment)
        db.session.commit()
        resp = make_response()
        resp.headers['HX-Redirect'] = url_for('event.check_payment', participant_id=payment.participant_id)
        return resp
    return render_template('event/admin/modals/payment_note_form.html', payment_id=payment_id)


@event.route('/admin/tickets/<int:ticket_id>/claim', methods=['GET', 'POST'])
@login_required
def admin_add_ticket_holder(ticket_id, holder_id=None):
    form = TicketClaimForm()
    ticket = EventTicket.query.get(ticket_id)
    holder_id = request.args.get('holder_id', type=int)
    if request.method == 'POST':
        if holder_id:
            holder = EventParticipant.query.get(holder_id)
            if holder.holding_ticket:
                holding_ticket = holder.holding_ticket
                holding_ticket.holder = None
                db.session.add(holding_ticket)
            ticket.holder_id = holder_id
            db.session.add(ticket)
            db.session.commit()
            resp = make_response()
            resp.headers['HX-Redirect'] = url_for('event.check_payment', participant_id=ticket.participant_id)
            return resp
        else:
            holder = EventParticipant(event_id=ticket.event_id)
            form.populate_obj(holder)
            ticket.holder = holder
            db.session.add(holder)
            db.session.add(ticket)
            db.session.commit()
            resp = make_response()
            resp.headers['HX-Redirect'] = url_for('event.check_payment', participant_id=ticket.participant_id)
            return resp
    return render_template('event/admin/claim_ticket.html', form=form, ticket=ticket)


@event.route('/admin/events/<int:event_id>/participants/search')
@login_required
def search_participant(event_id):
    ticket_id = request.args.get('ticket_id', type=int)
    query = request.args.get('name')
    matches = 0
    template = '''
    <thead>
    <th>คำนำหน้า</th>
    <th>ชื่อ</th>
    <th>นามสกุล</th>
    <th>บัตร</th>
    <th></th>
    </thead>
    <tbody>
    '''
    if query:
        for p in EventParticipant.query.filter_by(event_id=event_id)\
                .filter(or_(EventParticipant.firstname.like(f'%{query}%'),
                            EventParticipant.lastname.like(f'%{query}%'))):
            url = url_for('event.admin_add_ticket_holder', ticket_id=ticket_id, holder_id=p.id)
            matches += 1
            template += f'''
           <tr>
           <td>{p.title}</td>
           <td>{p.firstname}</td>
           <td>{p.lastname}</td>
           <td>{p.holding_ticket.ticket_number if p.holding_ticket else "ไม่มีบัตร"}</td>
           <td><a hx-post="{url}" class="button is-rounded" hx-headers='{{"X-CSRF-Token": "{ generate_csrf() }" }}' hx-confirm="ท่านแน่ใจว่าจะเคลมบัตรนี้ บัตรเดิมถ้ามีอยู่จะถูกยกเลิกการถือครองโดยอัตโนมัติ">add</a>
           </tr>
           '''
    template += '</tbody>'
    if matches > 0:
        return template
    else:
        return 'No matches.'


@event.route('/admin/participants/<int:participant_id>/add-ticket', methods=['POST'])
@login_required
def admin_add_ticket(participant_id):
    participant = EventParticipant.query.get(participant_id)
    event = participant.event
    purchased_datetime = arrow.now('Asia/Bangkok').datetime
    ticket = EventTicket(event_id=event.id, participant=participant, create_datetime=purchased_datetime)
    event.last_ticket_number += 1
    ticket.ticket_number = f'{event.id}-{event.last_ticket_number:04d}'
    db.session.add(ticket)
    db.session.commit()
    resp = make_response()
    resp.headers['HX-Redirect'] = url_for('event.check_payment', participant_id=participant.id)
    return resp
