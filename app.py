from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from model import db, Users, Patients, Reservation, Completed
from flask_migrate import Migrate
from datetime import datetime

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
    session.clear()
    return render_template('login.html')

@app.route('/admin/api/get-patient/<int:id>', methods=['GET'])
def admin_api_get_schedule(id):
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    target_patient = Patients.get_patient_by_id(id)
    if not target_patient:
        return jsonify({"message": "User not found"}), 404
    target_user = Users.get_user_by_id(target_patient.user_id)
    data = {
        "name": target_user.name,
        "email": target_user.email,
        "province": target_user.province,
        "municipality": target_user.municipality,
        "age": target_patient.age,
        "sex": target_patient.sex,
        "cancer_type": target_patient.cancer_type,
    }
    return jsonify(data)
    
@app.route('/admin/completed/delete/<int:id>', methods=['POST'])
def admin_completed_delete(id):
    target_completed = Completed.get_completed_by_id(id)
    if not target_completed:
        return "<script>alert('No completed reservations found');location.href='/admin/schedule'</script>"
    db.session.delete(target_completed)
    db.session.commit()
    return "<script>alert('Item deleted from completed records!');location.href='/admin/schedule'</script>"

@app.route('/admin/schedule/alter-status/', methods=['POST'])
def admin_schedule_alter_status():
    patient_id = request.form['patient_id']
    target_reservation = Reservation.get_reservation_by_patient_id(patient_id)
    if not target_reservation:
        return "<script>alert('No reservations found');location.href='/admin/schedule'</script>"
    if "promote" in request.form:
        if target_reservation.status==2:
            return redirect(url_for('admin_schedule'))
        target_reservation.status+=1
        db.session.commit()
        return redirect(url_for('admin_schedule'))
    if "demote" in request.form:
        if target_reservation.status==0:
            return redirect(url_for('admin_schedule'))    
        target_reservation.status-=1
        db.session.commit()
        return redirect(url_for('admin_schedule'))
    if "delete" in request.form:
        db.session.delete(target_reservation)
        db.session.commit()
        return redirect(url_for('admin_schedule'))
    if "complete" in request.form:
        target_patient = Patients.get_patient_by_id(patient_id)
        target_user = Users.get_user_by_id(target_patient.id)
        if not (target_patient or target_user):
            return "<script>alert('Failed! Cannot find record');location.href='/admin/schedule'</script>"

        completed_insert = Completed.insert_completed(target_user.name,
                                                      target_user.email,
                                                      target_user.province,
                                                      target_user.municipality,
                                                      target_patient.age,
                                                      target_patient.sex,
                                                      target_patient.cancer_type,
                                                      target_reservation.reservation_date,
                                                      )
        if not completed_insert:
            return "<script>alert('Failed to insert');location.href='/admin/schedule'</script>"
        db.session.delete(target_reservation)
        db.session.commit()
        return "<script>alert('Item added to completed records!');location.href='/admin/schedule'</script>"
    return redirect(url_for('admin_schedule'))

@app.route('/admin/schedule/edit', methods=['POST', 'GET'])
def admin_schedule_edit():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if not session_user.acc_type==1:
        return redirect(url_for('patient_dashboard'))
    
    patient_id, reservation_date = request.form['patient_id'], datetime.strptime(request.form['reservation_date'], '%Y-%m-%d').date()
    target_reservation = Reservation.get_reservation_by_patient_id(patient_id)
    if not target_reservation:
        return "none"
    target_reservation.reservation_date = reservation_date
    db.session.commit()
    return redirect(url_for('admin_schedule'))

@app.route('/admin/schedule/save', methods=['POST', 'GET'])
def admin_schedule_save():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if not session_user.acc_type==1:
        return redirect(url_for('patient_dashboard'))
    patient_id, reservation_date = request.form['patient_id'], datetime.strptime(request.form['reservation_date'], '%Y-%m-%d').date()
    if not (patient_id or reservation_date):
        return "please fill up all the fields"
    reservation_insert = Reservation.insert_reservations(patient_id, reservation_date)
    if not reservation_insert:
        return "<script>alert('Failed! This account already have a reservation record');location.href='/admin/dashboard'</script>"
    return "<script>alert('Success! Schedule reservation has been saved');location.href='/admin/schedule'</script>"

@app.route('/admin/schedule')
def admin_schedule():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type==0:
        return redirect(url_for('patient_dashboard'))
    all_patients = db.session.query(Patients.id, Users.name).join(Users, Patients.user_id == Users.id).all()
    available_patients = []   
    for i, x in all_patients:
        reservation_obj = Reservation.get_reservation_by_patient_id(i)
        if not reservation_obj:
            available_patients.append((i, x))
    all_reservations = Reservation.fetch_reservations()
    all_completed = Completed.fetch_completed()
    return render_template('admin/schedule.html', 
                           session_user=session_user,
                           all_reservations=all_reservations,
                           available_patients=available_patients,
                           all_completed=all_completed
                           )

@app.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type==0:
        return redirect(url_for('patient_dashboard'))
    return render_template('admin/dashboard.html')

@app.route('/patient/dashboard', methods=['GET'])
def patient_dashboard():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type==1:
        return redirect(url_for('admin_dashboard'))
    return render_template('patient/dashboard.html')

@app.route('/patient/schedule', methods=['GET'])
def patient_schedule():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type==1:
        return redirect(url_for('admin_dashboard'))
    current_patient = Patients.get_patient_by_user_id(session_user.id)
    if not current_patient:
        return redirect(url_for('patient_reservation'))
    current_reservation = Reservation.get_reservation_by_patient_id(current_patient.id)
    return render_template('patient/schedule.html', 
                           session_user=session_user,
                           current_patient=current_patient,
                           current_reservation=current_reservation)

@app.route('/patient/reservation', methods=['GET'])
def patient_reservation():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type==1:
        return redirect(url_for('admin_dashboard'))
    return render_template('patient/reservation.html', session_user=session_user)

@app.route('/patient/schedule/edit', methods=['POST', 'GET'])
def patient_schedule_edit():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type==1:
        return redirect(url_for('admin_dashboard'))

    target_patient = Patients.get_patient_by_user_id(session_user.id)
    target_user = Users.get_user_by_id(target_patient.user_id)
    target_reservation = Reservation.get_reservation_by_patient_id(target_patient.id)

    if not (target_patient or target_reservation or target_user):
        return redirect(url_for('patient_dashboard'))

    if 'delete' in request.form:
        db.session.delete(target_patient)
        db.session.delete(target_reservation)
        db.session.commit()
        return redirect(url_for('patient_schedule'))
    if 'submit' not in request.form:
        return redirect(url_for('patient_dashboard'))
    
    reservation_date = datetime.strptime(request.form['reservation_date'], '%Y-%m-%d').date()
    name = request.form['name']
    age = request.form['age']
    sex = request.form['sex']
    type = request.form['type']
    province = request.form['province']
    municipality = request.form['municipality']
    
    target_reservation.reservation_date = reservation_date
    target_user.name = name
    target_patient.age = age
    target_patient.sex = sex
    target_patient.cancer_type = type
    target_user.province = province
    target_user.municipality = municipality
    
    db.session.commit()
    return redirect(url_for('patient_schedule'))

@app.route('/patient/schedule/save', methods=['POST'])
def patient_schedule_save():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type==1:
        return redirect(url_for('admin_dashboard'))
    target_patient = Patients.get_patient_by_user_id(session_user.id)
    if not target_patient:
        return redirect(url_for('patient_dashboard'))
    reservation_date = datetime.strptime(request.form['reservation_date'], '%Y-%m-%d').date()
    reservation_insert = Reservation.insert_reservations(target_patient.id, reservation_date)
    if not reservation_insert:
        return "<script>alert('Failed! Your account already have a reservation record');location.href='/patient/dashboard'</script>"
    return "<script>alert('Success! Schedule reservation has been sent to admin');location.href='/patient/dashboard'</script>"

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
    acc_type, name, email, province, municipality, password, password2 = request.form['acc_type'], request.form['name'], request.form['email'], request.form['province'], request.form['municipality'], request.form['password'], request.form['password_2']
    if not (name and email and password and password2):
        return "fill out all fields", 400
    if password != password2:
        return "password not matched", 400
    if acc_type == '1':
        acc_type = True
    if acc_type == '0':
        acc_type = False
    user_insert = Users.insert_user(acc_type, name, email, province, municipality, password)
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
    if 'user_email' not in session:
        return None
    current_user = Users.query.filter_by(email=str(session.get('user_email', ""))).first()
    if not current_user:
        return None
    return current_user


if __name__ == "__main__":
    app.run(debug=True)