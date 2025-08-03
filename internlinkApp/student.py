"""
This module manages all InternLink features exclusive to students.

It specifies how to view the student's dashboard or homepage.
Examining and sorting through open internships.
Examining the comprehensive details for a particular internship.
Filling up internship applications.
Monitoring the progress of applications that have been filed. 
"""

import os
from flask import redirect, render_template, session, url_for, request, flash
from datetime import datetime
from werkzeug.utils import secure_filename

from internlinkApp import app, db
from internlinkApp.user import ALLOWED_RESUME_EXTENSIONS, allowed_file

# Student Home Route
@app.route('/student/home')
def student_home():
    
    """
    The student homepage's endpoint.

    takes people who aren't logged in to the login page.
    prevents individuals who are not students from accessing the site.

    Returns: str: A redirect or the rendered student home page.
    """

    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role']!='student':
        return render_template('access_denied.html'), 403

    return render_template('student_home.html')

#Internship Route
@app.route('/internships', methods=['GET'])
def browse_internships():
    """
     Endpoint for searching and sorting internships.

    enables students to browse and filter a list of available internships based on a number of parameters, including category, location, duration, and pay
    """
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'student':
        return render_template('access_denied.html'), 403

    internships = []
    category_filter = request.args.get('category')
    location_filter = request.args.get('location')
    duration_filter = request.args.get('duration')
    stipend_filter = request.args.get('stipend')

    categories = ["Software", "Marketing", "Research", "Design", "Data", "Engineering", "Other"]

    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT DISTINCT location FROM internship ORDER BY location;")
            locations = [loc['location'] for loc in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT duration FROM internship ORDER by duration;")
            durations = [dur['duration'] for dur in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT stipend FROM internship ORDER by stipend;")
            stipends = [stip['stipend'] for stip in cursor.fetchall()]

            query = """
                SELECT i.internship_id, i.title, i.description, i.location, i.duration,
                       i.skills_required, i.deadline, i.stipend, i.number_of_opening,
                       e.company_name, e.logo_path
                FROM internship i
                JOIN employer e ON i.company_id = e.emp_id
                WHERE i.deadline >= CURRENT_DATE()
            """
            params = []

            if category_filter and category_filter != 'all': 
                query += " AND (i.title LIKE %s OR i.skills_required LIKE %s OR i.description LIKE %s)"
                params.extend([f"%{category_filter}%", f"%{category_filter}%", f"%{category_filter}%"])
            if location_filter and location_filter != 'all':
                query += " AND i.location = %s"
                params.append(location_filter)
            if duration_filter and duration_filter != 'all':
                query += " AND i.duration = %s"
                params.append(duration_filter)
            if stipend_filter and stipend_filter != 'all':
                query += " AND i.stipend = %s"
                params.append(stipend_filter)

            query += " ORDER BY i.deadline ASC;"
            cursor.execute(query, tuple(params))
            internships = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching internships or filter options: {e}")
        flash("An error occurred while loading the internships. Please try again later.", "danger")
        return redirect(url_for('student_home'))


    return render_template('browse_internships.html',
                           internships=internships,
                           categories=categories,
                           locations=locations,
                           durations=durations,
                           stipends=stipends,
                           selected_category=category_filter,
                           selected_location=location_filter,
                           selected_duration=duration_filter,
                           selected_stipend=stipend_filter)

# Fetching Internship Route
@app.route('/internship/<int:internship_id>')
def view_internship_details(internship_id):
    """
    Endpoint to view the information of a certain internship.

    Arguments: internship_id (int): The internship's ID to be viewed.

    Returns: "" or a redirect to the rendered internship details page.
    """
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'student': 
        return render_template('access_denied.html'), 403

    internship_details = None
    try:
        with db.get_cursor() as cursor:
            query = """
                SELECT i.*, e.company_name, e.company_description, e.website, e.logo_path
                FROM internship i
                JOIN employer e ON i.company_id = e.emp_id
                WHERE i.internship_id = %s;
            """
            cursor.execute(query, (internship_id,))
            internship_details = cursor.fetchone()

        if not internship_details:
            return render_template('error.html', error_message="Internship not found."), 404

    except Exception as e:
        print(f"Error fetching internship details: {e}")
        return render_template('error.html', error_message="Could not load internship details."), 500

    return render_template('internship_details.html', internship=internship_details)

#Applying Internship Route
@app.route('/internship/<int:internship_id>/apply', methods=['GET', 'POST'])
def apply_for_internship(internship_id):
    """
    endpoint where students can submit internship applications.
    
    manages the application form's display (GET) and submission processing (POST). It controls resume uploads and pre-fills data.

    Arguments: internship_id (int): The internship ID for which an application is being made.
    
    Returns: str: A redirect or the rendered application page.
    """
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'student':
        return render_template('access_denied.html'), 403

    user_id = session['user_id']
    internship_details = None
    student_profile = None
    application_exists = False
    form_errors = {}
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT student_id FROM student WHERE user_id = %s;", (user_id,))
            student_data = cursor.fetchone()
            if not student_data:
                flash("Your student profile is incomplete. Please update your profile before applying for internships.", "warning")
                return redirect(url_for('profile'))
            
            student_id = student_data['student_id']

            cursor.execute("SELECT * FROM application WHERE student_id = %s AND internship_id = %s;",
                           (student_id, internship_id))
            if cursor.fetchone():
                application_exists = True
                flash("You have already applied for this internship.", "info")

            cursor.execute("""
                SELECT i.internship_id, i.title, i.description, i.location, i.duration, i.deadline, i.stipend,
                       e.company_name
                FROM internship i
                JOIN employer e ON i.company_id = e.emp_id
                WHERE i.internship_id = %s;
            """, (internship_id,))
            internship_details = cursor.fetchone()

            if not internship_details:
                return render_template('error.html', error_message="Internship not found."), 404
            
            cursor.execute("""
                SELECT u.full_name, u.email, s.university, s.course, s.resume_path
                FROM users u
                LEFT JOIN student s ON u.user_id = s.user_id
                WHERE u.user_id = %s;
            """, (user_id,))
            student_profile = cursor.fetchone()
            if not student_profile:
                 flash("Your student profile details could not be loaded. Please ensure your profile is complete.", "warning")
                 return redirect(url_for('profile'))

    except Exception as e:
        print(f"Error loading application page: {e}")
        return render_template('error.html', error_message="Could not load application form."), 500

    if request.method == 'POST' and not application_exists:
        cover_letter = request.form.get('cover_letter')
        resume_file = request.files.get('resume')
        replace_resume = request.form.get('replace_resume') == 'true'

        current_resume_path = student_profile['resume_path']
        new_resume_path = current_resume_path

        if resume_file and resume_file.filename != '':
            if not allowed_file(resume_file.filename, ALLOWED_RESUME_EXTENSIONS):
                form_errors['resume'] = 'Resume must be a PDF file.'
            else:
                upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                if current_resume_path and os.path.exists(os.path.join(app.root_path, 'static', current_resume_path)):
                    os.remove(os.path.join(app.root_path, 'static', current_resume_path))

                filename = secure_filename(f"resume_{user_id}_{internship_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
                resume_file.save(os.path.join(upload_folder, filename))
                new_resume_path = 'uploads/' + filename
        elif replace_resume and not resume_file:
             new_resume_path = None
             if current_resume_path and os.path.exists(os.path.join(app.root_path, 'static', current_resume_path)):
                 os.remove(os.path.join(app.root_path, 'static', current_resume_path))
        elif not current_resume_path and not resume_file:
            form_errors['resume'] = 'A resume is required to apply for an internship.'


        if form_errors:
            flash("Please correct the errors in your application form.", 'danger')
            return render_template('apply_internship.html',
                                internship=internship_details,
                                student_profile=student_profile,
                                application_exists=application_exists,
                                form_errors=form_errors)
        else:
            try:
                with db.get_cursor() as cursor:
                    if new_resume_path != current_resume_path:
                        cursor.execute("UPDATE student SET resume_path = %s WHERE user_id = %s;",
                                    (new_resume_path, user_id))

                    cursor.execute('''
                        INSERT INTO application (student_id, internship_id, status, cover_letter, feedback)
                        VALUES (%s, %s, %s, %s, %s);
                    ''', (student_id, internship_id, 'Pending', cover_letter, None))
                
                flash("Application submitted successfully! You can track its status in 'My Applications'.", 'success')
                return redirect(url_for('my_applications'))
            except Exception as e:
                print(f"Error submitting application: {e}")
                flash("An error occurred while submitting your application. Please try again.", 'danger')
                return render_template('apply_internship.html',
                                    internship=internship_details,
                                    student_profile=student_profile,
                                    application_exists=application_exists,
                                    form_errors=form_errors)

    return render_template('apply_internship.html',
                        internship=internship_details,
                        student_profile=student_profile,
                        application_exists=application_exists,
                        form_errors=form_errors)

# My application route
@app.route('/my_applications', methods=['GET'])
def my_applications():
    """
    endpoint where students can monitor the applications they have submitted.

    searches the database for every application linked to the student who is currently logged in, including information from the employer and internship tables.

    Returns: str: The page that was displayed and showed the apps list. 
    """
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'student':
        return render_template('access_denied.html'), 403

    user_id = session['user_id']
    applications = []

    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT student_id FROM student WHERE user_id = %s;",
                        (user_id,))
            student_data = cursor.fetchone()
            if not student_data:
                flash("Student profile not found. Please ensure your student details are complete.", "warning")
                return redirect(url_for('profile'))

            student_id = student_data['student_id']

            query = """
                SELECT a.status, a.feedback,
                       i.title AS internship_title, i.location AS internship_location,
                       e.company_name AS company_name,
                       i.internship_id
                FROM application a
                JOIN internship i ON a.internship_id = i.internship_id
                JOIN student s ON a.student_id = s.student_id
                JOIN employer e ON i.company_id = e.emp_id
                WHERE s.student_id = %s
                ORDER BY i.deadline DESC;
            """
            cursor.execute(query, (student_id,))
            applications = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching applications: {e}")
        flash("Could not load your applications. Please try again.", "danger")
        applications = []

    return render_template('my_applications.html', applications=applications)