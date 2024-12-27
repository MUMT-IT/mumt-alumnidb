import os
import uuid
import arrow

import boto3
from datetime import datetime

import requests
from flask import render_template, flash, redirect, url_for, request
from sqlalchemy_utils.types.arrow import arrow

from app.event import event_blueprint as event
from app.event.forms import ParticipantForm, TicketClaimForm
from app.event.models import *


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
                ticket = EventTicket(event_id=event_id, participant=participant)
                ticket.generate_ticket_number(event)
                db.session.add(ticket)
            db.session.commit()
            flash('You have successfully registered.', 'success')
        return redirect(url_for('event.show_tickets', event_id=event_id, participant_id=participant.id))
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


@event.route('/events/<int:event_id>/participants/<int:participant_id>/tickets')
def show_tickets(event_id, participant_id):
    event = Event.query.get(event_id)
    participant = EventParticipant.query.get(participant_id)
    return render_template('event/tickets.html', event=event, participant=participant)


@event.route('/events/<int:event_id>/tickets/<int:ticket_id>/claim', methods=['GET', 'POST'])
def claim_ticket(event_id, ticket_id):
    form = TicketClaimForm()
    if request.method == 'GET':
        return render_template('event/modals/ticket_claim.html', event_id=event_id, ticket_id=ticket_id, form=form)
    if form.validate_on_submit():
        participant = EventParticipant.query.filter_by(event_id=event_id,
                                                       telephone=form.telephone.data).first()
        if participant:
            ticket = EventTicket.query.get(ticket_id)
            participant.ticket = ticket
            db.session.add(participant)
            db.session.commit()
            flash('คุณแจ้งความประสงค์ใช้บัตรเข้างานนี้แล้ว', 'success')
            return redirect(url_for('event.show_tickets', event_id=event_id, participant_id=participant.id))


@event.route('/api/otp')
def get_otp():
    telephone = request.args.get('telephone')
    requests.post(os.environ['BLOWERIO_URL'] + '/messages',
                  data={'to': f'+66{telephone}', 'message': 'Hello from Blower.io'})
    return f'''
    <span>ส่ง OTP เรียบร้อยแล้ว</span>
    <input type="text" name="otp" id="otp-input" class="input" placeholder="OTP"/>
    '''


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
    return redirect(url_for('event.show_tickets', event_id=event_id, participant_id=participant_id))
