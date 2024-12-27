from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms_alchemy import model_form_factory
from wtforms_components import IntegerField, StringField

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


class TicketClaimForm(FlaskForm):
    telephone = StringField('หมายเลขโทรศัพท์', validators=[DataRequired()])
    otp = StringField('OTP')