from app import db


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    start_datetime = db.Column(db.DateTime(timezone=True), nullable=False, info={'label': 'วันเริ่ม'})
    end_datetime = db.Column(db.DateTime(timezone=True), nullable=False, info={'label': 'วันสิ้นสุด'})
    format = db.Column(db.String(), nullable=False, info={'label': 'รูปแบบ',
                                                          'choices': [(c,c) for c in ('Onsite', 'Online')]})
    location = db.Column(db.String(), nullable=False)
    min_participatants = db.Column(db.Integer(), nullable=False)
    max_participatants = db.Column(db.Integer(), nullable=False)
    register_start_datetime = db.Column(db.DateTime(timezone=True), info={'label': 'วันเปิดลงทะเบียน'})
    register_end_datetime = db.Column(db.DateTime(timezone=True), info={'label': 'วันปิดลงทะเบียน'})
    ticket_price = db.Column(db.Numeric())
    last_ticket_number = db.Column(db.Integer(), default=0, info={'label': 'หมายเลขบัตรสุดท้าย'})

    @property
    def detail(self):
        return f'{self.time} สถานที่ {self.location}'

    @property
    def time(self):
        return f'{self.start_datetime.strftime("%d/%m/%Y %H:%M")} - {self.end_datetime.strftime("%d/%m/%Y %H:%M")}'

    def __str__(self):
        return f'{self.name}: {self.detail}'


class EventParticipant(db.Model):
    __tablename__ = 'event_participants'
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('events.id'))
    event = db.relationship('Event', backref=db.backref('participants', lazy='dynamic', cascade='all, delete-orphan'))
    title = db.Column(db.String(), nullable=True, info={'label': 'คำนำหน้า'})
    firstname = db.Column(db.String(), nullable=False, info={'label': 'ชื่อจริง'})
    lastname = db.Column(db.String(), nullable=False, info={'label': 'นามสกุล'})
    telephone = db.Column(db.String(), info={'label': 'หมายเลขโทรศัพท์'})
    line_id = db.Column(db.String())
    register_datetime = db.Column(db.DateTime(timezone=True))

    def __str__(self):
        return f'{self.title or ""}{self.firstname} {self.lastname}'

    @property
    def total_balance(self):
        return len([ticket for ticket in self.purchased_tickets.filter_by(cancel_datetime=None)]) * self.event.ticket_price

    @property
    def total_amount_due(self):
        return self.total_balance - (len([ticket for ticket in self.purchased_tickets.filter_by(cancel_datetime=None) if ticket.payment_datetime]) * self.event.ticket_price)


class EventTicket(db.Model):
    __tablename__ = 'event_tickets'
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    ticket_number = db.Column(db.String())
    event_id = db.Column(db.Integer(), db.ForeignKey('events.id'))
    event = db.relationship('Event', backref=db.backref('tickets', lazy='dynamic', cascade='all, delete-orphan'))
    participant_id = db.Column(db.Integer(), db.ForeignKey('event_participants.id'))
    participant = db.relationship('EventParticipant', foreign_keys=[participant_id],
                                  backref=db.backref('purchased_tickets',
                                                     lazy='dynamic',
                                                     order_by='EventTicket.create_datetime',
                                                     cascade='all, delete-orphan'))
    create_datetime = db.Column(db.DateTime(timezone=True), info={'label': 'วันที่จอง'})
    payment_datetime = db.Column(db.DateTime(timezone=True), info={'label': 'วันที่จ่ายเงิน'})
    cancel_datetime = db.Column(db.DateTime(timezone=True), info={'label': 'วันที่ยกเลิก'})
    holder_id = db.Column(db.Integer(), db.ForeignKey('event_participants.id'))
    holder = db.relationship('EventParticipant', foreign_keys=[holder_id],
                             backref=db.backref('holding_ticket',
                                                uselist=False,
                                                cascade='all'))
    checkin_datetime = db.Column(db.DateTime(timezone=True))
    note = db.Column(db.String(), info={'label': 'Note'})


class EventTicketPayment(db.Model):
    __tablename__ = 'event_ticket_payments'
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('events.id'))
    event = db.relationship('Event', backref=db.backref('ticket_payments',
                                                        order_by='EventTicketPayment.create_datetime',
                                                        lazy='dynamic',
                                                        cascade='all, delete-orphan'))
    participant_id = db.Column(db.Integer(), db.ForeignKey('event_participants.id'))
    participant = db.relationship('EventParticipant', foreign_keys=[participant_id],
                                  backref=db.backref('payments', lazy='dynamic', cascade='all, delete-orphan'))
    create_datetime = db.Column(db.DateTime(timezone=True), info={'label': 'วันที่จอง'})
    filename = db.Column(db.String())
    key = db.Column(db.Text())
    amount = db.Column(db.Numeric(), info={'label': 'จำนวนเงิน'})
    walkin = db.Column(db.Boolean(), default=False)
    approve_datetime = db.Column(db.DateTime(timezone=True))
    note = db.Column(db.Text())
