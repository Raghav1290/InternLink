from internlinkApp import app, db
from flask import redirect, render_template, session, url_for, request, flash

# Employer Home Route
@app.route('/employer/home')
def employer_home():
     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['role']!='employer':
          return render_template('access_denied.html'), 403

     return render_template('employer_home.html')

# Employer Interships Route
@app.route('/employer/internships', methods=['GET'])
def employer_posted_internships():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'employer':
        return render_template('access_denied.html'), 403

    user_id = session['user_id']
    posted_internships = []
    error_message = None

    try:
        with db.get_cursor() as cursor:
            # Here we are fetching the emp_id for the employer who is logged in
            cursor.execute("SELECT emp_id, company_name FROM employer WHERE user_id = %s;", (user_id,))
            employer_data = cursor.fetchone()
            if not employer_data:
                # Flashing warning message if the profile is incomplete
                flash("Your employer profile is incomplete. Please update your profile before viewing posted internships.", "warning")
                return redirect(url_for('profile'))

            emp_id = employer_data['emp_id']
            company_name = employer_data['company_name']

            # Fetching the internships published by the employer
            query = """
                SELECT internship_id, title, location, duration, deadline, stipend, number_of_opening
                FROM internship
                WHERE company_id = %s
                ORDER BY deadline DESC;
            """
            cursor.execute(query, (emp_id,))
            posted_internships = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching employer's internships: {e}")
        error_message = "Could not load posted internships."

    return render_template('employer_posted_internships.html',
                           internships=posted_internships,
                           company_name=company_name,
                           error_message=error_message)

# Employer Application Management Route
@app.route('/employer/applications', methods=['GET'])
def employer_manage_applications():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'employer':
        return render_template('access_denied.html'), 403

    user_id = session['user_id']
    applications = []
    error_message = None

    # Here we are fetching filter parameters from the URL string query
    search_applicant = request.args.get('applicant_name')
    search_internship_title = request.args.get('internship_title')
    filter_status = request.args.get('status')

    try:
        with db.get_cursor() as cursor:
            # Fetching emp_id for the employer who is logged in 
            cursor.execute("SELECT emp_id FROM employer WHERE user_id = %s;", (user_id,))
            employer_data = cursor.fetchone()
            if not employer_data:
                flash("Your employer profile is incomplete. Please update your profile before managing applications.", "warning")
                return redirect(url_for('profile'))

            emp_id = employer_data['emp_id']

            # Default query to get applications for the internships posted by employer
            query = """
                SELECT a.student_id, a.internship_id, a.status, a.feedback,
                       u.full_name AS student_full_name, u.email AS student_email,
                       s.university, s.course, s.resume_path,
                       i.title AS internship_title, i.location AS internship_location
                FROM application a
                JOIN student s ON a.student_id = s.student_id
                JOIN users u ON s.user_id = u.user_id
                JOIN internship i ON a.internship_id = i.internship_id
                WHERE i.company_id = %s
            """
            params = [emp_id]

            if search_applicant:
                query += " AND u.full_name LIKE %s"
                params.append(f"%{search_applicant}%")
            if search_internship_title:
                query += " AND i.title LIKE %s"
                params.append(f"%{search_internship_title}%")
            if filter_status and filter_status != 'all':
                query += " AND a.status = %s"
                params.append(filter_status)

            query += " ORDER BY a.status ASC, u.full_name ASC;"
            cursor.execute(query, tuple(params))
            applications = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching applications for employer: {e}")
        error_message = "Could not load applications."

    return render_template('employer_manage_applications.html',
                           applications=applications,
                           search_applicant=search_applicant,
                           search_internship_title=search_internship_title,
                           filter_status=filter_status,
                           error_message=error_message)
