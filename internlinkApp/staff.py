from loginapp import app
from loginapp import db
from flask import redirect, render_template, session, url_for

@app.route('/staff/home')
def staff_home():
     """Staff Homepage endpoint.

     Methods:
     - get: Renders the homepage for the current staff user, or an "Access
          Denied" 403: Forbidden page if the current user has a different role.

     If the user is not logged in, requests will redirect to the login page.
     """
     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['role']!='staff':
          return render_template('access_denied.html'), 403

     return render_template('staff_home.html')