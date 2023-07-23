from flask import Flask, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import pickle
import bcrypt

app = Flask(__name__)
app.app_context().push()

import pymysql

pymysql.install_as_MySQLdb()

## open and load the pickle file provided in read mode.
model = pickle.load(open('model.pkl', 'rb'))

app.config['DEBUG'] = True
app.config['ENV'] = 'development'
app.config['FLASK_ENV'] = 'development'
app.config['SECRET_KEY'] = 'ItShouldBeAlongStringOfRandomCharacters'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost:3306/home_loan'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class users(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    user_name = db.Column (db.String(255))
    password = db.Column(db.String(255))
    def __init__(self,user_name,password):
        self.user_name = user_name
        self.password = password

db.create_all()


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Perform necessary operations to store the user data in the database
        data = users(username,hashed_password)
        db.session.add(data)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("here")
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']

        # Perform necessary operations to verify the user credentials
        user = db.session.query(users).filter(users.user_name == username).first()
        #user_list = users.query.filter_by(user_name == username).all()
        if user is not None:
            stored_password = user.password  # Assuming the hashed password is stored in the third column of the user table

            # Compare the hashed password with the provided password
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                # Password matches, user authenticated
                session['loggedin'] = True
                session['id'] = user.id
                session['username'] = user.user_name
                return redirect(url_for('predict'))  # Redirect to the predict page
            else:
                return render_template('login.html', msg="The username and password dont match, please re-enter the details." )
        else :
            return redirect(url_for('register'))
    return render_template('login.html')


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        float_features = [float(x) for x in request.form.values()]
        final_features = [np.array(float_features)]
        prediction = model.predict(final_features)

        output = round(prediction[0], 2)

        if prediction == 1:
            output = "Congrats!! You are eligible for the loan."
        else:
            output = "Sorry, You are not eligible for the loan."

            # Render the template with the prediction result and form data
        return render_template('predict.html', prediction_text=output)
    return render_template('predict.html')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
