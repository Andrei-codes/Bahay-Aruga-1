from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from model import db, Users, Patients, Reservation, Completed, Medicine, History
from flask_migrate import Migrate
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = "kagaguhan"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlite.db"
db.init_app(app)
migrate = Migrate(app, db)


@app.route("/")
def index():
    session.clear()
    return render_template("index.html")


@app.route("/login_page", methods=["GET"])
def login_page():
    session.clear()
    return render_template("login.html")


@app.route("/admin/api/get-patient/<int:id>", methods=["GET"])
def admin_api_get_schedule(id):
    session_user = get_session_user()
    if not session_user:
        return "Not logged in", 401
    target_patient = Patients.get_patient_by_id(id)
    if not target_patient:
        return jsonify({"message": "Patient not found"}), 404
    target_user = Users.get_user_by_id(target_patient.user_id)
    if not target_user:
        return jsonify({"message": "User not found"}), 404
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


@app.route("/admin/completed/delete/<int:id>", methods=["POST"])
def admin_completed_delete(id):
    target_completed = Completed.get_completed_by_id(id)
    if not target_completed:
        return "<script>alert('No completed reservations found');location.href='/admin/schedule'</script>"
    db.session.delete(target_completed)
    db.session.commit()
    return "<script>alert('Item deleted from completed records!');location.href='/admin/schedule'</script>"


@app.route("/admin/schedule/alter-status/", methods=["POST"])
def admin_schedule_alter_status():
    patient_id = request.form['patient_id']
    target_reservation = Reservation.get_reservation_by_patient_id(patient_id)
    if not target_reservation:
        return "<script>alert('No reservations found');location.href='/admin/schedule'</script>"
    
    if "promote" in request.form:
        if target_reservation.status == 2:
            return redirect(url_for('admin_schedule'))
        target_reservation.status += 1
        db.session.commit()
        return redirect(url_for('admin_schedule'))
    
    if "demote" in request.form:
        if target_reservation.status == 0:
            return redirect(url_for('admin_schedule'))
        target_reservation.status -= 1
        db.session.commit()
        return redirect(url_for('admin_schedule'))
    
    if "delete" in request.form:
        db.session.delete(target_reservation)
        db.session.commit()
        return redirect(url_for('admin_schedule'))
    
    if "complete" in request.form:
        target_patient = Patients.get_patient_by_id(patient_id)
        if not target_patient:
            return "<script>alert('Failed! Cannot find patient record');location.href='/admin/schedule'</script>"
        target_user = Users.get_user_by_id(target_patient.user_id)
        if not target_user:
            return "<script>alert('Failed! Cannot find user record');location.href='/admin/schedule'</script>"
        
        completed_insert = Completed.insert_completed(
            target_user.name,
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


@app.route("/admin/schedule/edit", methods=["POST", "GET"])
def admin_schedule_edit():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if not session_user.acc_type == 1:
        return redirect(url_for("patient_dashboard"))

    patient_id, reservation_date = (
        request.form["patient_id"],
        datetime.strptime(request.form["reservation_date"], "%Y-%m-%d").date(),
    )
    target_reservation = Reservation.get_reservation_by_patient_id(patient_id)
    if not target_reservation:
        return "none"
    target_reservation.reservation_date = reservation_date
    db.session.commit()
    return redirect(url_for("admin_schedule"))


@app.route("/admin/schedule/save", methods=["POST", "GET"])
def admin_schedule_save():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if not session_user.acc_type == 1:
        return redirect(url_for("patient_dashboard"))
    patient_id, reservation_date = (
        request.form["patient_id"],
        datetime.strptime(request.form["reservation_date"], "%Y-%m-%d").date(),
    )
    if not (patient_id or reservation_date):
        return "please fill up all the fields"
    reservation_insert = Reservation.insert_reservations(patient_id, reservation_date)
    if not reservation_insert:
        return "<script>alert('Failed! This account already have a reservation record');location.href='/admin/dashboard'</script>"
    return "<script>alert('Success! Schedule reservation has been saved');location.href='/admin/schedule'</script>"


@app.route("/admin/schedule")
def admin_schedule():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type == 0:
        return redirect(url_for("patient_dashboard"))
    all_patients = (
        db.session.query(Patients.id, Users.name)
        .join(Users, Patients.user_id == Users.id)
        .all()
    )
    available_patients = []
    for i, x in all_patients:
        reservation_obj = Reservation.get_reservation_by_patient_id(i)
        if not reservation_obj:
            available_patients.append((i, x))
    all_reservations = Reservation.fetch_reservations()
    all_completed = Completed.fetch_completed()
    return render_template(
        "admin/schedule.html",
        session_user=session_user,
        all_reservations=all_reservations,
        available_patients=available_patients,
        all_completed=all_completed,
    )


@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type == 0:
        return redirect(url_for("patient_dashboard"))
    return render_template("admin/dashboard.html")


@app.route('/update_stock', methods=['POST'])
def update_stock():
    updates = request.get_json()
    updated_meds = []  # List to track medicines with changes

    # Collect all updates
    for update in updates:
        medicine = Medicine.query.get(update['id'])
        if medicine:
            new_stock = update['stock']
            if medicine.stocks != new_stock:  # Check if stock has changed
                medicine.stocks = new_stock
                updated_meds.append({
                    'itemname': medicine.itemname,
                    'new_stock': new_stock
                })
                db.session.commit()  # Commit the update to the Medicine table

    # Add entries to History for medicines with stock changes
    if updated_meds:  # Proceed only if there are changes
        for med_info in updated_meds:
            history_entry = History(
                date=datetime.utcnow(),
                itemname=med_info['itemname'],
                stocks=med_info['new_stock']
            )
            db.session.add(history_entry)
        db.session.commit()  # Commit all history entries at once
    return jsonify({'status': 'success'})

@app.route("/admin/inventory", methods=["GET", "POST"])
def inventory():
    session_user = get_session_user()
    if not session_user:
        return "Not logged in"

    # Ensure only admin can access inventory (if applicable)
    if session_user.acc_type == 0:
        return redirect(url_for("patient_dashboard"))

    history_entries = History.query.order_by(History.date.desc()).all()  # Fetch history entries

    if request.method == "POST":
        # Handle stock updates
        data = request.json
        print('Received Data:', data)  # Debugging
        
        for item in data['stocks']:
            print('Updating:', item['itemname'], 'with stock:', item['stock'])
            success = Medicine.update_stock(item['itemname'], item['stock'])
            if not success:
                return jsonify({'status': 'error', 'message': f"Medicine {item['itemname']} not found"}), 404
        
        return jsonify({'status': 'success'})

    # If GET request, show inventory
    # Query all unique categories from Medicine table
    categories = set(medicine.category for medicine in Medicine.query.all())
    print(categories)
    
    # Query all rows from the Medicine table
    medicines = Medicine.query.all()
    print(medicines)

    # Create a list to store detailed medicine information
    medicine_data = []
    for medicine in medicines:
        medicine_info = {
            "id": medicine.id,
            "itemname": medicine.itemname,
            "category": medicine.category,
            "image_url": medicine.image_url,
            "stocks": medicine.stocks,
        }
        medicine_data.append(medicine_info)

    return render_template(
        "admin/inventory.html", medicines=medicine_data, categories=categories, history_entries=history_entries
    )
@app.route("/patient/dashboard", methods=["GET"])
def patient_dashboard():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type == 1:
        return redirect(url_for("admin_dashboard"))
    return render_template("patient/dashboard.html")


@app.route("/patient/schedule", methods=["GET"])
def patient_schedule():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type == 1:
        return redirect(url_for("admin_dashboard"))
    current_patient = Patients.get_patient_by_user_id(session_user.id)
    if not current_patient:
        return redirect(url_for("patient_reservation"))
    current_reservation = Reservation.get_reservation_by_patient_id(current_patient.id)
    return render_template(
        "patient/schedule.html",
        session_user=session_user,
        current_patient=current_patient,
        current_reservation=current_reservation,
    )


@app.route("/patient/reservation", methods=["GET"])
def patient_reservation():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type == 1:
        return redirect(url_for("admin_dashboard"))
    return render_template("patient/reservation.html", session_user=session_user)


@app.route("/patient/schedule/edit", methods=["POST", "GET"])
def patient_schedule_edit():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type == 1:
        return redirect(url_for("admin_dashboard"))

    target_patient = Patients.get_patient_by_user_id(session_user.id)
    target_user = Users.get_user_by_id(target_patient.user_id)
    target_reservation = Reservation.get_reservation_by_patient_id(target_patient.id)

    if not (target_patient or target_reservation or target_user):
        return redirect(url_for("patient_dashboard"))

    if "delete" in request.form:
        db.session.delete(target_patient)
        db.session.delete(target_reservation)
        db.session.commit()
        return redirect(url_for("patient_schedule"))
    if "submit" not in request.form:
        return redirect(url_for("patient_dashboard"))

    reservation_date = datetime.strptime(
        request.form["reservation_date"], "%Y-%m-%d"
    ).date()
    name = request.form["name"]
    age = request.form["age"]
    sex = request.form["sex"]
    type = request.form["type"]
    province = request.form["province"]
    municipality = request.form["municipality"]

    target_reservation.reservation_date = reservation_date
    target_user.name = name
    target_patient.age = age
    target_patient.sex = sex
    target_patient.cancer_type = type
    target_user.province = province
    target_user.municipality = municipality

    db.session.commit()
    return redirect(url_for("patient_schedule"))

wellness_plan_data = {}
@app.route("/patient/schedule/save", methods=["POST"])
def patient_schedule_save():
    session_user = get_session_user()
    if not session_user:
        return f"Not logged in"
    if session_user.acc_type == 1:
        return redirect(url_for("admin_dashboard"))
    target_patient = Patients.get_patient_by_user_id(session_user.id)
    if not target_patient:
        return redirect(url_for("patient_dashboard"))
    reservation_date = datetime.strptime(
        request.form["reservation_date"], "%Y-%m-%d"
    ).date()
    reservation_insert = Reservation.insert_reservations(
        target_patient.id, reservation_date
    )
    if not reservation_insert:
        return "<script>alert('Failed! Your account already have a reservation record');location.href='/patient/dashboard'</script>"
    return "<script>alert('Success! Schedule reservation has been sent to admin');location.href='/patient/dashboard'</script>"
wellness_plan_data = {}

@app.route('/patient/weeks', methods=["POST"])
def patient_weeks():
    age = request.form.get('age')
    gender = request.form.get('gender')
    diagnosis = request.form.get('diagnosis')

    # Update current wellness plan data
    wellness_plan_data['current'] = {'age': age, 'gender': gender, 'diagnosis': diagnosis}

    # Store data in session for use in other routes
    session['age'] = age
    session['gender'] = gender
    session['diagnosis'] = diagnosis

    return render_template('patient/patientweeks.html')

@app.route('/patient/completed', methods=["POST"])
def patient_completed():
    if request.method == 'POST':
        # Get the logged-in user
        session_user = get_session_user()  # Assuming you have a function to get the current user

        # Check if user is logged in
        if not session_user:
            return "Not logged in"

        # Retrieve form data
        comment_text = request.form.get('comment')
        exercise_checked = request.form.get('exercise_input', 'false')  # Default to 'false' if not provided
        medicine_checked = request.form.get('medicine_input', 'false')  # Default to 'false' if not provided
        
        # Find the patient by user ID
        target_patient = Patients.get_patient_by_user_id(session_user.id)

        if not target_patient:
            # Create new patient entry if not found
            Patients.create_or_update_health_status(session_user.id, exercise_checked, medicine_checked, comment_text)
        else:
            # Update existing patient's health status
            target_patient.update_health_status(exercise_checked, medicine_checked, comment_text)

        return render_template('patient/dashboard.html')
@app.route('/patient/plan')
def patient_plan():
    # Retrieve data from session
    age = session.get('age', 'N/A')
    gender = session.get('gender', 'N/A')
    diagnosis = session.get('diagnosis', 'N/A')
    day = request.args.get('day')

    return render_template('patient/plan.html', age=age, gender=gender, diagnosis=diagnosis, day=day)

@app.route("/patient/wellnessplan", methods=["GET", "POST"])
def patient_wellnessplan():
    session_user = get_session_user()

    # Check if user is logged in
    if not session_user:
        return "Not logged in"

    # Redirect admin users to admin dashboard
    if session_user.acc_type == 1:
         patients = Patients.query.all()
         return render_template('admin/plan.html', patients=patients)

    if request.method == "POST":
        try:
            reservation_date = datetime.strptime(
                request.form["reservation_date"], "%Y-%m-%d"
            ).date()
        except ValueError:
            return "Invalid date format"

        # Get the patient associated with the logged-in user
        target_patient = Patients.get_patient_by_user_id(session_user.id)

        # Redirect to patient dashboard if patient not found
        if not target_patient:
            return render_template('patient/wellnessplan.html', username=session_user.name)

        # Insert reservation into database
        reservation_insert = Reservation.insert_reservations(
            target_patient.id, reservation_date
        )

        # Handle reservation insertion result
        if not reservation_insert:
            return "<script>alert('Failed! Your account already has a reservation record');location.href='/patient/dashboard'</script>"

        return "<script>alert('Success! Schedule reservation has been sent to admin');location.href='/patient/dashboard'</script>"

    # For GET requests (initial page load)
    return render_template('patient/wellnessplan.html', username=session_user.name)


@app.route("/patient/save", methods=["POST"])
def patient_save():
    session_user = get_session_user()
    if not session_user:
        return "Not logged in"
    if session_user.acc_type == 1:
        return redirect(url_for("admin_dashboard"))

    # Check for required form fields
    required_fields = ["age", "sex", "type"]
    for field in required_fields:
        if field not in request.form or not request.form[field]:
            return f"Missing required field: {field}"

    age = request.form["age"]
    sex = request.form["sex"]
    type = request.form["type"]

    # Insert patient record
    patient_insert = Patients.insert_patient(session_user.id, age, sex, type)
    if not patient_insert:
        return redirect(url_for("patient_dashboard"))

    return redirect(url_for("patient_schedule"))


@app.route("/register-user", methods=["POST", "GET"])
def register_user():
    acc_type, name, email, province, municipality, password, password2 = (
        request.form["acc_type"],
        request.form["name"],
        request.form["email"],
        request.form["province"],
        request.form["municipality"],
        request.form["password"],
        request.form["password_2"],
    )
    if not (name and email and password and password2):
        return "fill out all fields", 400
    if password != password2:
        return "password not matched", 400
    if acc_type == "1":
        acc_type = True
    if acc_type == "0":
        acc_type = False
    user_insert = Users.insert_user(
        acc_type, name, email, province, municipality, password
    )
    if not user_insert:
        return redirect(url_for("index"))
    return redirect(url_for("login_page"))


@app.route("/auth-user", methods=["POST", "GET"])
def auth_user():
    email, password = request.form["email"], request.form["password"]
    current_user = Users.auth_user(email.strip(), password.strip())
    if not (email and password):
        return "fill out all fields", 400
    if not current_user:
        return "false", 400
    session["user_email"] = str(email)
    if not current_user.acc_type == 0:
        return redirect(url_for("patient_dashboard"))
    return redirect(url_for("admin_dashboard"))




def get_session_user():
    if "user_email" not in session:
        return None
    current_user = Users.query.filter_by(
        email=str(session.get("user_email", ""))
    ).first()
    if not current_user:
        return None
    return current_user


if __name__ == "__main__":
    app.run(debug=True)
