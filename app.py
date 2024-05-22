from flask import Flask, render_template, session, request, redirect, url_for
from model import db, Users, Patients, Reservation
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = "kagaguhan"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///sqlite.db"
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/login_page', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    session_user = get_session_user()
    if session_user.acc_type==0:
        return redirect(url_for('patient_dashboard'))
    return render_template('admin/dashboard.html')

@app.route('/patient/dashboard', methods=['GET'])
def patient_dashboard():
    session_user = get_session_user()
    if session_user.acc_type==1:
        return redirect(url_for('admin_dashboard'))
    return render_template('patient/dashboard.html')

@app.route('/patient/schedule', methods=['GET'])
def patient_schedule():
    session_user = get_session_user()
    return render_template('patient/schedule.html', session_user=session_user)

@app.route('/patient/reservation', methods=['GET'])
def patient_reservation():
    check_session()
    return render_template('patient/reservation.html')

@app.route('/patient/save', methods=['POST', 'GET'])
def patient_save():
    session_user = get_session_user()
    if session_user.acc_type==1:
        return redirect(url_for('admin_dashboard'))
    age, sex, type = request.form['age'], request.form['sex'], request.form['type']
    patient_insert = Patients.insert_patient(session_user.id, age, sex, type)
    if not patient_insert:
        return redirect(url_for('patient_dashboard'))
    return redirect(url_for('patient_schedule'))

@app.route('/register-user', methods=['POST', 'GET'])
def register_user():
    check_session()
    acc_type, name, email, province, municipality, password, password2 = request.form['acc_type'], request.form['name'], request.form['email'], request.form['province'], request.form['municipality'], request.form['password'], request.form['password_2']
    if not (name and email and password and password2):
        return "fill out all fields", 400
    if password != password2:
        return "password not matched", 400
    user_insert = Users.insert_user(bool(acc_type), name, email, province, municipality, password)
    if not user_insert: 
        return redirect(url_for('index'))
    return redirect(url_for('login_page'))

@app.route('/auth-user', methods=['POST', 'GET'])
def auth_user():
    email, password = request.form['email'], request.form['password']
    current_user = Users.auth_user(email.strip(), password.strip())
    if not (email and password):
        return "fill out all fields", 400
    if not current_user:
        return "false", 400
    session['user_email'] = str(email)
    if not current_user.acc_type==0:
        return redirect(url_for('patient_dashboard'))
    return redirect(url_for('admin_dashboard'))

def get_session_user():
    check_session()
    current_user = Users.query.filter_by(email=str(session.get('user_email', ""))).first()
    if not current_user:
        return None
    return current_user

def check_session():
    if 'user_email' not in session:
        return redirect(url_for('index'))
    pass

if __name__ == "__main__":
    app.run(debug=True)