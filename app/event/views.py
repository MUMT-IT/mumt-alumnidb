import os
import uuid
from pprint import pprint

import arrow

import boto3
from datetime import datetime

import requests
from flask import render_template, flash, redirect, url_for, request, make_response, jsonify
from linebot.v3.messaging import ApiClient, MessagingApi, PushMessageRequest, TextMessage, Configuration
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
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                push_message_request = PushMessageRequest(to=participant.line_id, messages=[
                    TextMessage(text='ลงทะเบียนเรียบร้อยแล้ว'), TextMessage(text=f'tickets:{event_id}')])
                try:
                    api_response = line_bot_api.push_message(push_message_request)
                    pprint(api_response)
                except Exception as e:
                    print(f'Exception while sending MessageApi->push_message {e}')
            resp = make_response()
            resp.headers['HX-Trigger'] = 'closeLIFFWindow'
            return resp
    return render_template('event/register_form.html', form=form, event=event)


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
            print('not holding ticket')
            resp.headers['HX-Redirect'] = url_for('event.claim_ticket', event_id=event_id, ticket_number=ticket_number)
        elif participant.holding_ticket.ticket_number != ticket_number:
            print('holding another ticket')
            resp.headers['HX-Redirect'] = url_for('event.show_ticket_detail', event_id=event_id,
                                                  ticket_number=ticket_number)
        else:
            resp.headers['HX-Swap'] = 'none'
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
            pprint(api_response)
        except Exception as e:
            print(f'Exception while sending MessageApi->push_message {e}')
    resp = make_response()
    resp.headers['HX-Trigger'] = 'closeLIFFWindow'
    return resp
    # return redirect(url_for('line_api.confirm_payment', event_id=event_id, participant_id=participant_id))
