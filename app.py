#!/usr/bin/env python3
import os
import json
import pyotp
import pyqrcode
from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
)

# Load users DB
with open("users.json") as user_db:
    users_dict = json.load(user_db)

# Init Flask app
app = Flask(__name__)
app.secret_key = 'somesecretkeythatonlyishouldknow'


@app.before_request
def before_request():
    g.user = None
    g.email = None
    g.otp = None

    if 'user_id' in session:
        if session['user_id'] in users_dict:
            username = session['user_id']
            g.user = username
            g.email = users_dict[username]['email']

            otp_code = users_dict[username]['otp_code']
            g.otp = pyotp.totp.TOTP(otp_code).now()


# Routes
@app.route('/', methods=['GET', 'POST'])
def root():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)

        username = request.form['username']
        password = request.form['password']

        # Check if username&password matches
        if username in users_dict and users_dict[username]['password'] == password:
            session['user_id'] = username
            session.pop('login_message', None)

            # If QR file not yet existing create it
            qr_file_name = f'static/qrcode-{username}.png'
            otp_code = users_dict[username]['otp_code']
            email = users_dict[username]['email']
            if not os.path.isfile(qr_file_name):
                # Create string for Google Authenticator or Authy
                # example: otpauth://totp/Test%20App:dani%40ricardo.ch?secret=XXXXXXXXYYYYYYHH&issuer=Test%20App
                otpauth = pyotp.totp.TOTP(otp_code).provisioning_uri(name=email, issuer_name='Test App')

                # Generate QR Code from otpauth string and put it in a png file
                qrcode = pyqrcode.create(otpauth)
                qrcode.png(qr_file_name, scale=6)

            return redirect(url_for('profile'))

        session['login_message'] = 'Login failed, retry'
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/profile')
def profile():
    if not g.user:
        return redirect(url_for('login'))

    return render_template('profile.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


# Initialize main app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)
