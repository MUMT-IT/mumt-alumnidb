import os

from flask import render_template, make_response
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage

from app import db
from app.member import member_blueprint as member
from app.member.forms import MemberInfoForm
from app.member.models import MemberInfo

configuration = Configuration(access_token=os.environ.get('LINE_MESSAGE_ACCESS_TOKEN'))

@member.route('/info/edit', methods=['GET', 'POST'])
def edit_member_info():
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
    return render_template('member/member_info_form.html')


@member.route('/members/line-id/<line_id>/check-info', methods=['GET'])
def load_member_info_form(line_id):
    print(line_id)
    member = MemberInfo.query.filter_by(line_id=line_id).first()
    form = MemberInfoForm(obj=member)
    return render_template('member/partials/member_info_form_part.html',
                           form=form, line_id=line_id)
