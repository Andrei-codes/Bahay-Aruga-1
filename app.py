from flask import Flask, render_template, session, request
from model import db, Users

app = Flask(__name__)
app.secret_key = "kagaguhan"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///sqlite.db"
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register-user', methods=['POST', 'GET'])
def register_user():
    name, email, province, municipality, password, password2 = request.form['name'], request.form['email'], request.form['province'], request.form['municipality'], request.form['password'], request.form['password_2']
    if not (name and email and password and password2):
        return "fill out all fields", 400
    if password != password2:
        return "password not matched", 400
    user_entry = Users(
        name=name,
        email=email,
        province=province,
        municipality=municipality,
        password=password
    )
    db.session.add(user_entry)
    db.session.commit()
    return "true", 200

@app.route('/auth-user', methods=['POST', 'GET'])
def auth_user():
    email, password = request.form['email'], request.form['password']
    if not (email and password):
        return "fill out all fields", 400
    if not Users.auth_user(email, password):
        return "false", 400
    return "true", 200

if __name__ == "__main__":
    app.run(debug=True)