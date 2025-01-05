from flask_wtf import FlaskForm
from wtforms.fields.simple import BooleanField
from wtforms_alchemy import model_form_factory
from wtforms_components import IntegerField, SelectField

from app import db
from app.event.models import EventParticipant

BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session


class ParticipantForm(ModelForm):
    class Meta:
        model = EventParticipant

    number = IntegerField('จำนวนบัตร', default=1)
    group = SelectField('ประเภท',
                        choices=[(c, c) for c in ('ศิษย์เก่า', 'ศิษย์ปัจจุบัน', 'บุคคลทั่วไป')])
    consent = BooleanField('ยินยอมให้บันทึกข้อมูล', default=False)


class TicketClaimForm(ModelForm):
    class Meta:
        model = EventParticipant