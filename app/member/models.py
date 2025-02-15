from app import db


class MemberInfo(db.Model):
    __tablename__ = 'member_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    graduate_year = db.Column(db.String(), info={'label': 'ปีที่จบการศึกษา'})
    program = db.Column(db.String(), info={'label': 'สาขา',
                                           'choices': [(c, c) for c in ['เทคนิคการแพทย์', 'รังสีเทคนิค']]})
    line_id = db.Column(db.String(), info={'label': 'Line ID'})
    telephone = db.Column(db.String(), info={'label': 'หมายเลขโทรศัพท์'})
    email = db.Column(db.String(), info={'label': 'อีเมล'})
    work_office = db.Column(db.Text(), info={'label': 'ที่ทำงาน'})
    title = db.Column(db.String(), nullable=True, info={'label': 'คำนำหน้า'})
    firstname = db.Column(db.String(), nullable=False, info={'label': 'ชื่อจริง'})
    lastname = db.Column(db.String(), nullable=False, info={'label': 'นามสกุล'})
    student_class = db.Column(db.String(), info={'label': 'รุ่น'})
    note = db.Column(db.Text())

