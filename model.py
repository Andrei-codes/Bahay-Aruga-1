from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    acc_type = db.Column(db.Boolean)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    province = db.Column(db.String(255), nullable=False)
    municipality = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    @classmethod
    def auth_user(cls, email, password):
        user = cls.query.filter_by(email=email).first()
        if not user:
            return None
        if not user.password==password:
            return None
        return user
    
    @classmethod
    def insert_user(cls, acc_type, name, email, province, municipality, password):
        check_user = cls.query.filter_by(email=email).first()
        if check_user:
            return False
        user_entry = cls(acc_type=acc_type,
                        name=name,
                        email=email,
                        province=province,
                        municipality=municipality,
                        password=password)
        db.session.add(user_entry)
        db.session.commit()
        return True
    
    @classmethod
    def get_user_by_id(cls, id):
        target_user = cls.query.filter_by(id=id).first()
        if not target_user:
            return None
        return target_user
    
class Patients(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(255), nullable=False)
    cancer_type = db.Column(db.String(255), nullable=False)

    user = db.relationship('Users', backref=db.backref('patients', lazy=True))

    @classmethod
    def insert_patient(cls, user_id, age, sex, cancer_type):
        target_patient = cls.query.filter_by(user_id=user_id).first()
        if target_patient:
            return False
        patient_entry = cls(user_id=user_id,
                            age=age,
                            sex=sex,
                            cancer_type=cancer_type)
        db.session.add(patient_entry)
        db.session.commit()
        return True
    
    @classmethod
    def fetch_patients(cls):
        all_patients = cls.query.all()
        return all_patients
    
    @classmethod
    def get_patient_by_user_id(cls, user_id):
        target_patient = cls.query.filter_by(user_id=user_id).first()
        if not target_patient:
            return None
        return target_patient
    
    @classmethod
    def get_patient_by_id(cls, id):
        target_patient = cls.query.filter_by(id=id).first()
        if not target_patient:
            return None
        return target_patient

    

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    reservation_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.SmallInteger, nullable=False, comment="0=pending, 1=on-progress, 2=priority, 3=completed")

    patient = db.relationship('Patients', backref=db.backref('reservations', lazy=True))

    @classmethod
    def insert_reservations(cls, patient_id, reservation_date):
        check_reservation = cls.query.filter_by(patient_id=patient_id).first()
        if check_reservation:
            return False
        reservation_entry = cls(patient_id=patient_id, reservation_date=reservation_date, status=0)
        db.session.add(reservation_entry)
        db.session.commit()
        return True

    @classmethod
    def fetch_reservations(cls):
        all_reservations = cls.query.all()
        return all_reservations
    
    @classmethod
    def get_reservation_by_patient_id(cls, id):
        target_reservation = cls.query.filter_by(patient_id=id).first()
        return target_reservation
    
    @classmethod
    def get_reservation_by_id(cls, id):
        target_reservation = cls.query.filter_by(id=id).first()
        return target_reservation
    
class Completed(db.Model):
    __tablename__ = 'completed'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(255), nullable=False)
    cancer_type = db.Column(db.String(255), nullable=False)
    reservation_date = db.Column(db.Date, nullable=False)

    @classmethod
    def insert_completed(cls, name, email, province, municipality, age, sex, cancer_type, reservation_date):
        address = f"{municipality}, {province}"
        completed_entry = cls(name=name,
                              email=email,
                              address=address,
                              age=age,
                              sex=sex,
                              cancer_type=cancer_type,
                              reservation_date=reservation_date)
        db.session.add(completed_entry)
        db.session.commit()
        return True
    
    @classmethod
    def get_completed_by_id(cls, id):
        target_completed = cls.query.filter_by(id=id).first()
        return target_completed

    @classmethod
    def fetch_completed(cls):
        all_completed = cls.query.all()
        return all_completed