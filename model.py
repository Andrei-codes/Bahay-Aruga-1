from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    acc_type = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    province = db.Column(db.String(255), nullable=False)
    municipality = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    @classmethod
    def auth_user(cls, email, password):
        user = cls.query.filter_by(email=email).first()
        if not user:
            return False
        if not user.password==password:
            return False
        return True