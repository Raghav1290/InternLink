import os
from flask import redirect, render_template, session, url_for, request, flash
from datetime import datetime
from werkzeug.utils import secure_filename

from internlinkApp import app, db
from internlinkApp.user import ALLOWED_RESUME_EXTENSIONS, allowed_file

# Student Home Route
@app.route('/student/home')
def student_home():

     # If User is not logged in then It will be redirected to login
     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['role']!='student':
          return render_template('access_denied.html'), 403

     return render_template('student_home.html')

#Internship Route
@app.route('/internships', methods=['GET'])
def browse_internships():

     # If User is not logged in then It will be redirected to login
     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['role'] != 'student':
          return render_template('access_denied.html'), 403

     internships = [] #Intialized empty list of internships
     category_filter = request.args.get('category')
     location_filter = request.args.get('location')
     duration_filter = request.args.get('duration')
     stipend_filter = request.args.get('stipend')

     try:
          with db.get_cursor() as cursor:
               # Querryinng the internships based on filters and deadlines
               query = """
                    SELECT i.internship_id, i.title, i.description, i.location, i.duration,
                         i.skills_required, i.deadline, i.stipend, i.number_of_opening,
                         e.company_name, e.logo_path
                    FROM internship i
                    JOIN employer e ON i.company_id = e.emp_id
                    WHERE i.deadline >= CURRENT_DATE()
               """
               params = []

               if category_filter:
                    # Searching within skills_required, title or description for the category
                    query += " AND (i.title LIKE %s OR i.skills_required LIKE %s OR i.description LIKE %s)"
                    params.extend([f"%{category_filter}%", f"%{category_filter}%", f"%{category_filter}%"])
               if location_filter:
                    query += " AND i.location LIKE %s"
                    params.append(f"%{location_filter}%")
               if duration_filter:
                    query += " AND i.duration LIKE %s"
                    params.append(f"%{duration_filter}%")
               if stipend_filter:
                    query += " AND i.stipend LIKE %s"
                    params.append(f"%{stipend_filter}%")

               # Ordering it in Ascending order as per the deadlines     
               query += " ORDER BY i.deadline ASC;" 
               cursor.execute(query, tuple(params))
               internships = cursor.fetchall()

     except Exception as e:
          print(f"Error fetching internships: {e}")
          return render_template('error.html', error_message="Could not load internships."), 500


     return render_template('browse_internships.html',
                              internships=internships,
                              selected_category=category_filter,
                              selected_location=location_filter,
                              selected_duration=duration_filter,
                              selected_stipend=stipend_filter)

# Fetching Internship Route
@app.route('/internship/<int:internship_id>')
def view_internship_details(internship_id):
    """View details of a specific internship.
    Fetches all details including associated company information.
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
            # Fetching student_id from user_id in session
            cursor.execute("SELECT student_id FROM student WHERE user_id = %s;", (user_id,))
            student_data = cursor.fetchone()
            if not student_data:
                flash("Your student profile is incomplete. Please update your profile before applying for internships.", "warning")
                return redirect(url_for('profile')) # Redirecting to profile page if profile of student is not found

            student_id = student_data['student_id']

            # Checking if the internship is already applied by the student
            cursor.execute("SELECT * FROM application WHERE student_id = %s AND internship_id = %s;",
                           (student_id, internship_id))
            if cursor.fetchone():
                application_exists = True
                flash("You have already applied for this internship.", "info") 

            # Fetching internship details so that form could be pre-fill
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

     # If internship is not already applied by the student
    if request.method == 'POST' and not application_exists:
        cover_letter = request.form.get('cover_letter')
        resume_file = request.files.get('resume') 

        # If the student wants to replace existing resume
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

                # Deleting previous resume or if the student is replacing resume
                if current_resume_path and os.path.exists(os.path.join(app.root_path, 'static', current_resume_path)):
                    os.remove(os.path.join(app.root_path, 'static', current_resume_path))

                # Saving new resume uploaded by the student
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

                    # Inserting new application of student internship in the application table
                    cursor.execute('''
                        INSERT INTO application (student_id, internship_id, status, feedback)
                        VALUES (%s, %s, %s, %s);
                    ''', (student_id, internship_id, 'Pending', cover_letter)) 

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