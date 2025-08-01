import os
import re
from datetime import datetime

from flask import redirect, render_template, request, session, url_for, flash # Adding flash for displaying error and success messages
from flask_bcrypt import Bcrypt
from markupsafe import Markup

from internlinkApp import app, db

flask_bcrypt = Bcrypt(app)

DEFAULT_USER_ROLE = 'student'

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_RESUME_EXTENSIONS = {'pdf'}

def allowed_file(filename, allowed_extensions):
    # his is a function which will help to check if the filename has an allowed file extension.
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def user_home_url():
    #It will help in generating a URL to the homepage for the users who are currently logged in.
    if 'loggedin' in session:
        role = session.get('role', None)
        # Checking the user role type and redirecting them to their specific role end points
        if role=='student': home_endpoint='student_home'
        elif role=='employer': home_endpoint='employer_home'
        elif role=='admin': home_endpoint='admin_home'
        else: home_endpoint = 'logout'
    else:
        home_endpoint = 'login'
    return url_for(home_endpoint)

# User Homepage Route
@app.route('/')
def root():
    return redirect(user_home_url())

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
         return redirect(user_home_url())

    username_invalid = False
    password_invalid = False
    account_inactive = False
    error_message = None 

    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            error_message="username and password are missing."
            return render_template('login.html', username=username, error_message=error_message)

        with db.get_cursor() as cursor:
            cursor.execute('''
                       SELECT user_id, username, password_hash, role, status
                       FROM users
                       WHERE username = %s;
                       ''', (username,))
            account = cursor.fetchone()

            if account is not None:
                # Here we're checking if the user account is inactive
                if account['status'] == 'inactive':
                    account_inactive = True
                    return render_template('login.html', username=username, account_inactive=account_inactive)

                password_hash = account['password_hash']

                if flask_bcrypt.check_password_hash(password_hash, password):
                    session['loggedin'] = True
                    session['user_id'] = account['user_id']
                    session['username'] = account['username']
                    session['role'] = account['role']
                    return redirect(user_home_url())
                else:
                    password_invalid = True
                    return render_template('login.html', username=username, password_invalid=password_invalid)
            else:
                username_invalid = True
                return render_template('login.html', username=username, username_invalid=username_invalid)

    return render_template('login.html') # If the request is GET then render login template

# SignUp Route
@app.route('/signup', methods=['GET','POST'])
def signup():

    if 'loggedin' in session:
         return redirect(user_home_url())

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # fields for other students 
    full_name = request.form.get('full_name')
    university = request.form.get('university')
    course = request.form.get('course')
    resume_file = request.files.get('resume')

    username_error = None
    email_error = None
    password_error = None
    confirm_password_error = None 
    signup_successful = False
    error_message = None

    if request.method == 'POST':
        with db.get_cursor() as cursor:
            cursor.execute('SELECT user_id FROM users WHERE username = %s;', (username,))
            account_already_exists = cursor.fetchone() is not None

        # Validation for username
        if not username: username_error = 'Username is required.'
        elif account_already_exists: username_error = 'An account already exists with this username.'
        elif len(username) < 3: username_error = 'Your username must be at least 3 characters long.'
        elif len(username) > 50: username_error = 'Your username cannot exceed 50 characters.'
        elif not re.match(r'^[A-Za-z0-9]+$', username):
            username_error = 'Your username can only contain letters and numbers.'            

        # Validation for email 
        if not email: email_error = 'Email address is required.'
        elif len(email) > 100: email_error = 'Your email address cannot exceed 100 characters.'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            email_error = 'Invalid email address.'

        # Validation for password
        if not password: password_error = 'Password is required.'
        elif len(password) < 8: password_error = 'Password must be at least 8 characters long.'
        elif not re.search(r'[A-Z]', password):
            password_error = 'Password must contain at least one uppercase letter.'
        elif not re.search(r'[a-z]', password):
            password_error = 'Password must contain at least one lowercase letter.'
        elif not re.search(r'[0-9]', password):
            password_error = 'Password must contain at least one digit.'
        elif not re.search(r'[^A-Za-z0-9]', password):
            password_error = 'Password must contain at least one special character.'

        # # Validation for confirm password
        if password != confirm_password:
            confirm_password_error = 'Passwords do not match.'

        if (username_error or email_error or password_error or confirm_password_error):
            return render_template('signup.html',
                                   username=username,
                                   email=email,
                                   password=password,
                                   confirm_password=confirm_password,
                                   username_error=username_error,
                                   email_error=email_error,
                                   password_error=password_error,
                                   confirm_password_error=confirm_password_error) 
        else:
            password_hash = flask_bcrypt.generate_password_hash(password)

            try:
                with db.get_cursor() as cursor:
                    cursor.execute('''
                                INSERT INTO users (username, password_hash, email, role, status)
                                VALUES (%s, %s, %s, %s, %s);
                                ''',
                                (username, password_hash, email, DEFAULT_USER_ROLE, 'active'))
                signup_successful = True
                flash_message_html = f"You have successfully signed up! Please "
                flash("You are successfully registered. Please Login...", 'success') 
                return render_template('signup.html', signup_successful=signup_successful)
            except Exception as e:
                print(f"Error during signup: {e}")
                error_message = "An error occurred during registration. Please try again."
                return render_template('signup.html', username=username, email=email, error_message=error_message)

    return render_template('signup.html') 

# Profile Route
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'loggedin' not in session:
         return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']
    profile_data = {}
    form_errors = {}

    def get_user_profile(user_id, role):
        with db.get_cursor() as cursor:
            if role == 'student':
                cursor.execute('''
                                SELECT u.username, u.email, u.full_name, u.profile_image, u.role, u.status,
                                       s.university, s.course, s.resume_path
                                FROM users u
                                LEFT JOIN student s ON u.user_id = s.user_id
                                WHERE u.user_id = %s;
                                ''', (user_id,))
            elif role == 'employer':
                cursor.execute('''
                                SELECT u.username, u.email, u.full_name, u.profile_image, u.role, u.status,
                                       e.company_name, e.company_description, e.website, e.logo_path
                                FROM users u
                                LEFT JOIN employer e ON u.user_id = e.user_id
                                WHERE u.user_id = %s;
                                ''', (user_id,))
            elif role == 'admin':
                cursor.execute('SELECT username, email, full_name, profile_image, role, status FROM users WHERE user_id = %s;',
                               (user_id,))
            return cursor.fetchone()

    if request.method == 'POST':
        # Fetching data from form submission
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        university = request.form.get('university')
        course = request.form.get('course')
        company_name = request.form.get('company_name')
        company_description = request.form.get('company_description')
        website = request.form.get('website')

        profile_image_file = request.files.get('profile_image')
        remove_profile_image = request.form.get('remove_profile_image') == 'true'
        resume_file = request.files.get('resume')
        remove_resume = request.form.get('remove_resume') == 'true'
        logo_file = request.files.get('logo')
        remove_logo = request.form.get('remove_logo') == 'true'

        current_profile_data = get_user_profile(user_id, role)
        current_profile_image = current_profile_data['profile_image'] if current_profile_data and 'profile_image' in current_profile_data else None
        current_resume_path = current_profile_data['resume_path'] if current_profile_data and 'resume_path' in current_profile_data else None
        current_logo_path = current_profile_data['logo_path'] if current_profile_data and 'logo_path' in current_profile_data else None

        if not full_name: form_errors['full_name'] = "Full name is required."
        elif len(full_name) > 100: form_errors['full_name'] = "Full name cannot exceed 100 characters."

        if role == 'admin':
            if not email: form_errors['email'] = "Email is required for Admin profile."
            elif len(email) > 100: form_errors['email'] = "Email address cannot exceed 100 characters."
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email): form_errors['email'] = "Invalid email address."

        elif role == 'student':
            if not university: form_errors['university'] = "University is required for Student profile."
            elif len(university) > 100: form_errors['university'] = "University cannot exceed 100 characters."
            if not course: form_errors['course'] = "Course is required for Student profile."
            elif len(course) > 100: form_errors['course'] = "Course cannot exceed 100 characters."
            if resume_file and resume_file.filename != '' and not allowed_file(resume_file.filename, ALLOWED_RESUME_EXTENSIONS):
                form_errors['resume'] = "Resume must be a PDF file."

        elif role == 'employer':
            if not company_name: form_errors['company_name'] = "Company name is required for Employer profile."
            elif len(company_name) > 100: form_errors['company_name'] = "Company name cannot exceed 100 characters."
            if website and not re.match(r'https?://(?:[-\w.]|(?:%[\da-fA-Z]{2}))+', website): form_errors['website'] = "Please enter a valid company website URL."
            if logo_file and logo_file.filename != '' and not allowed_file(logo_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                form_errors['logo'] = "Company logo must be an image file (PNG, JPG, JPEG, GIF)."

        if profile_image_file and profile_image_file.filename != '' and not allowed_file(profile_image_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            form_errors['profile_image'] = "Profile image must be an image file (PNG, JPG, JPEG, GIF)."

        if form_errors:
            flash("Please correct the errors in the form.", 'danger')
            profile_data = {**current_profile_data, **request.form.to_dict()}
            return render_template('profile.html', profile=profile_data, form_errors=form_errors)

        try:
            with db.get_cursor() as cursor:
                update_user_sql = "UPDATE users SET full_name = %s"
                user_params = [full_name]

                if role == 'admin':
                    update_user_sql += ", email = %s"
                    user_params.append(email)

                if remove_profile_image:
                    update_user_sql += ", profile_image = NULL"
                    if current_profile_image:
                        os.remove(os.path.join(app.root_path, 'static', current_profile_image))
                elif profile_image_file and profile_image_file.filename != '':
                    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                    if not os.path.exists(upload_folder): os.makedirs(upload_folder)
                    if current_profile_image:
                        os.remove(os.path.join(app.root_path, 'static', current_profile_image))

                    filename = secure_filename(f"profile_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{os.path.splitext(profile_image_file.filename)[1]}")
                    profile_image_file.save(os.path.join(upload_folder, filename))
                    update_user_sql += ", profile_image = %s"
                    user_params.append('uploads/' + filename)

                update_user_sql += " WHERE user_id = %s;"
                user_params.append(user_id)
                cursor.execute(update_user_sql, tuple(user_params))

                if role == 'student':
                    if remove_resume:
                        resume_path_to_db = None
                        if current_resume_path:
                            os.remove(os.path.join(app.root_path, 'static', current_resume_path))
                    elif resume_file and resume_file.filename != '':
                        upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                        if not os.path.exists(upload_folder): os.makedirs(upload_folder)
                        if current_resume_path:
                            os.remove(os.path.join(app.root_path, 'static', current_resume_path))

                        filename = secure_filename(f"resume_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
                        resume_file.save(os.path.join(upload_folder, filename))
                        resume_path_to_db = 'uploads/' + filename
                    else:
                        resume_path_to_db = current_resume_path


                    cursor.execute("UPDATE student SET university = %s, course = %s, resume_path = %s WHERE user_id = %s;",
                                   (university, course, resume_path_to_db, user_id))

                elif role == 'employer':
                    if remove_logo:
                        logo_path_to_db = None
                        if current_logo_path:
                            os.remove(os.path.join(app.root_path, 'static', current_logo_path))
                    elif logo_file and logo_file.filename != '':
                        upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                        if not os.path.exists(upload_folder): os.makedirs(upload_folder)
                        if current_logo_path:
                            os.remove(os.path.join(app.root_path, 'static', current_logo_path))

                        filename = secure_filename(f"logo_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{os.path.splitext(logo_file.filename)[1]}")
                        logo_file.save(os.path.join(upload_folder, filename))
                        logo_path_to_db = 'uploads/' + filename
                    else:
                        logo_path_to_db = current_logo_path

                    cursor.execute("UPDATE employer SET company_name = %s, company_description = %s, website = %s, logo_path = %s WHERE user_id = %s;",
                                   (company_name, company_description, website, logo_path_to_db, user_id))

            flash("Profile updated successfully!", 'success')
            return redirect(url_for('profile'))

        except Exception as e:
            print(f"Error updating profile: {e}")
            flash("An unexpected error occurred while updating your profile. Please try again.", 'danger')
            return redirect(url_for('profile'))

    profile_data = get_user_profile(user_id, role)
    return render_template('profile.html', profile=profile_data, form_errors=form_errors)


# Change Password Route
@app.route('/change_password', methods=['GET'])
def change_password():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    return render_template('change_password.html')

# Log out Route
@app.route('/logout')
def logout():

    session.pop('loggedin', None)
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash("You have been logged out.", 'info') # Flashing message for user logging out
    return redirect(url_for('login'))