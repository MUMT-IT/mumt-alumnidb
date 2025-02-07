import base64
import io
import os

import qrcode
from aenum import Member
from flask import render_template, make_response, url_for, request, flash, redirect
from flask_login import login_required
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage
from sqlalchemy import or_

from app import db
from app.member import member_blueprint as member
from app.member.forms import MemberInfoForm
from app.member.models import MemberInfo
from app.event.models import EventTicket

configuration = Configuration(access_token=os.environ.get('LINE_MESSAGE_ACCESS_TOKEN'))


@member.route('/info/qrcode/tickets/<ticket_no>')
@login_required
def create_qrcode_for_member_info_edit_from_ticket(ticket_no):
    buffer = io.BytesIO()
    img = qrcode.make(url_for('member.edit_member_info_from_ticket_holder',
                              ticket_no=ticket_no, _external=True, _scheme='https'))
    img.save(buffer, format="PNG")
    qrcode_data = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    return render_template('member/modals/edit_member_info_qrcode.html',
                           qrcode_data=qrcode_data, ticket_no=ticket_no)


@member.route('/info/edit/tickets/<ticket_no>', methods=['GET', 'POST'])
def edit_member_info_from_ticket_holder(ticket_no):
    method = request.args.get('method', 'manual')
    form = MemberInfoForm()
    ticket = EventTicket.query.filter_by(ticket_number=ticket_no).first()
    member = None
    line_id = None
    if ticket and ticket.holder:
        member = MemberInfo.query.filter(or_(MemberInfo.line_id==ticket.holder.line_id,
                                             MemberInfo.telephone==ticket.holder.telephone)).first()
        if member and member.line_id:
            line_id = member.line_id
    if request.method == 'GET':
        if member:
            form = MemberInfoForm(obj=member)
        else:
            form = MemberInfoForm(firstname=ticket.holder.firstname,
                                  lastname=ticket.holder.lastname,
                                  telephone=ticket.holder.telephone,
                                  title=ticket.holder.title)
        if method == 'manual':
            return render_template('member/member_info_manual_edit_form.html',
                                   form=form, event_id=ticket.event_id, line_id=line_id)
        else:
            return render_template('member/member_info_form.html')

    if request.method == 'POST':
        if form.validate_on_submit():
            if not member:
                member = MemberInfo()
            form.populate_obj(member)
            db.session.add(member)
            db.session.commit()
            flash('Member info has been updated.', 'success')
            return redirect(url_for('event.list_participants', event_id=ticket.event_id))
        else:
            print(form.errors)
            return render_template('member/member_info_manual_edit_form.html',
                                   form=form, event_id=ticket.event_id)


@member.route('/info/edit', methods=['GET', 'POST'])
def edit_member_info():
    ticket_no = request.args.get('ticket_no')
    form = MemberInfoForm()
    if form.validate_on_submit():
        member = MemberInfo.query.filter_by(line_id=form.line_id.data).first()
        if not member:
            member = MemberInfo()
        form.populate_obj(member)
        db.session.add(member)
        db.session.commit()
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            push_message_request = PushMessageRequest(to=form.line_id.data, messages=[
                TextMessage(text='บันทึกข้อมูลเรียบร้อยแล้ว')])
            try:
                api_response = line_bot_api.push_message(push_message_request)
            except Exception as e:
                print(f'Exception while sending MessageApi->push_message {e}')
        resp = make_response()
        resp.headers['HX-Trigger'] = 'closeLIFFWindow'
        return resp
    return render_template('member/member_info_form.html', ticket_no=ticket_no)


@member.route('/members/line-id/<line_id>/check-info', methods=['GET'])
def load_member_info_form(line_id):
    ticket_no = request.args.get('ticket_no')
    form = MemberInfoForm()
    member = MemberInfo.query.filter_by(line_id=line_id).first()
    if member:
        form = MemberInfoForm(obj=member)
    else:
        if ticket_no:
            ticket = EventTicket.query.filter_by(number=ticket_no).first()
            if ticket and ticket.holder:
                form = MemberInfoForm(firstname=ticket.holder.firstname,
                                      lastname=ticket.holder.lastname,
                                      title=ticket.holder.title,
                                      telephone=ticket.holder.telephone,
                                      )
    return render_template('member/partials/member_info_form_part.html',
                           form=form, line_id=line_id)
