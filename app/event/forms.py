from flask_wtf import FlaskForm
from wtforms.fields.simple import BooleanField
from wtforms.widgets.core import CheckboxInput, ListWidget
from wtforms_alchemy import model_form_factory, QuerySelectField, QuerySelectMultipleField
from wtforms_components import IntegerField, SelectField

from app import db
from app.event.models import EventParticipant, EventTicket

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


class ParticipantEditForm(ModelForm):
    class Meta:
        model = EventParticipant


class TicketForm(ModelForm):
    class Meta:
        model = EventTicket


class TicketClaimForm(ModelForm):
    class Meta:
        model = EventParticipant


def create_approve_payment_form(participant: EventParticipant):
    class ApprovePaymentForm(ModelForm):
        tickets = QuerySelectMultipleField('Tickets', query_factory=lambda: participant.purchased_tickets.filter_by(payment_datetime=None),
                                           widget=ListWidget(prefix_label=False),
                                           get_label='ticket_number',
                                           option_widget=CheckboxInput())
    return ApprovePaymentForm