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


class EventParticipant(db.Model):
    __tablename__ = 'event_participants'
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer(), db.ForeignKey('events.id'))
    event = db.relationship('Event', backref=db.backref('participants', lazy='dynamic', cascade='all, delete-orphan'))
    title = db.Column(db.String(), nullable=True)
    firstname = db.Column(db.String(), nullable=False)
    lastname = db.Column(db.String(), nullable=False)
    telephone = db.Column(db.String())


class EventTicket(db.Model):
    __tablename__ = 'event_tickets'
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    ticket_number = db.Column(db.String())
    event_id = db.Column(db.Integer(), db.ForeignKey('events.id'))
    event = db.relationship('Event', backref=db.backref('tickets', lazy='dynamic', cascade='all, delete-orphan'))

