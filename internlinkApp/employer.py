""" This module manages InternLink's employer-specific features.

It specifies features for: - Accessing the homepage of the employer.
- Looking at a list of internships that their company has posted.
- Filtering and updating the status of their internship applications. 
"""

from internlinkApp import app, db
from flask import redirect, render_template, session, url_for, request, flash

# Employer Home Route
@app.route('/employer/home')
def employer_home():
     """
    The employer homepage's endpoint.

    takes people who aren't logged in to the login page.
    prevents individuals who are not employers from accessing the site.
    """

     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['role']!='employer':
          return render_template('access_denied.html'), 403

     return render_template('employer_home.html')

@app.route('/employer/internships', methods=['GET'])
def employer_posted_internships():
    """ endpoint where employers may see the internships they have posted.

    obtains from the database a list of internships connected to the employer's organization that the user is currently logged into.

    Returns: str: The page that is displayed and shows the list of internships that have been posted.
    """
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'employer':
        return render_template('access_denied.html'), 403

    user_id = session['user_id']
    posted_internships = []
    error_message = None

    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT emp_id, company_name FROM employer WHERE user_id = %s;", (user_id,))
            employer_data = cursor.fetchone()
            if not employer_data:
                flash("Your employer profile is incomplete. Please update your profile before viewing posted internships.", "warning")
                return redirect(url_for('profile'))
            
            emp_id = employer_data['emp_id']
            company_name = employer_data['company_name']

            query = """
                SELECT i.internship_id, i.title, i.location, i.duration, i.deadline, i.stipend, i.number_of_opening,
                       COUNT(a.internship_id) AS application_count
                FROM internship i
                LEFT JOIN application a ON i.internship_id = a.internship_id
                WHERE i.company_id = %s
                GROUP BY i.internship_id
                ORDER BY i.deadline DESC;
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


@app.route('/employer/applications', methods=['GET'])
def employer_manage_applications():
    """ 
    endpoint for managing applications for employers.

    gives employers the ability to see, sort, and search applications submitted for internships at their organization.

    Returns: str: A list of programs displayed on the produced page.
    """

    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'employer':
        return render_template('access_denied.html'), 403

    user_id = session['user_id']
    applications = []
    error_message = None

    search_applicant = request.args.get('applicant_name')
    search_internship_title = request.args.get('internship_title')
    filter_status = request.args.get('status')

    applicants = []
    internship_titles = []

    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT emp_id FROM employer WHERE user_id = %s;", (user_id,))
            employer_data = cursor.fetchone()
            if not employer_data:
                flash("Your employer profile is incomplete. Please update your profile before managing applications.", "warning")
                return redirect(url_for('profile'))
            
            emp_id = employer_data['emp_id']

            cursor.execute("""
                SELECT DISTINCT u.full_name AS applicant
                FROM application a
                JOIN student s ON a.student_id = s.student_id
                JOIN users u ON s.user_id = u.user_id
                JOIN internship i ON a.internship_id = i.internship_id
                WHERE i.company_id = %s
                ORDER BY applicant;
            """, (emp_id,))
            applicants = [app['applicant'] for app in cursor.fetchall()]

            cursor.execute("""
                SELECT DISTINCT i.title
                FROM internship i
                WHERE i.company_id = %s
                ORDER BY i.title;
            """, (emp_id,))
            internship_titles = [title['title'] for title in cursor.fetchall()]

            query = """
                SELECT a.student_id, a.internship_id, a.status, a.feedback, a.cover_letter,
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

            if search_applicant and search_applicant != 'all':
                query += " AND u.full_name = %s"
                params.append(search_applicant)
            if search_internship_title and search_internship_title != 'all':
                query += " AND i.title = %s"
                params.append(search_internship_title)
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
                           applicants=applicants,
                           internship_titles=internship_titles,
                           search_applicant=search_applicant,
                           search_internship_title=search_internship_title,
                           filter_status=filter_status,
                           error_message=error_message)


@app.route('/employer/application/<int:student_id>/<int:internship_id>/update_status', methods=['POST'])
def employer_update_application_status(student_id, internship_id):

    """ 
    Endpoint allowing employers to update the feedback and status of an application.

    Args: student_id (int): The applicant's ID as a student.
        internship_id (int): The internship's identification number.

    Redirects: str: The application management page is accessed.
    """

    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'employer':
        return render_template('access_denied.html'), 403

    new_status = request.form.get('status')
    feedback = request.form.get('feedback')

    user_id = session['user_id']
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT emp_id FROM employer WHERE user_id = %s;", (user_id,))
            employer_data = cursor.fetchone()
            if not employer_data:
                flash("Employer profile not found.", 'danger')
                return redirect(url_for('employer_manage_applications'))
            emp_id = employer_data['emp_id']

            cursor.execute("""
                SELECT i.company_id FROM application a
                JOIN internship i ON a.internship_id = i.internship_id
                WHERE a.student_id = %s AND a.internship_id = %s;
            """, (student_id, internship_id))
            application_info = cursor.fetchone()

            if not application_info or application_info['company_id'] != emp_id:
                flash("You are not authorized to manage this application.", 'danger')
                return redirect(url_for('employer_manage_applications'))

            cursor.execute("""
                UPDATE application
                SET status = %s, feedback = %s
                WHERE student_id = %s AND internship_id = %s;
            """, (new_status, feedback, student_id, internship_id))
            flash("Application status updated successfully!", 'success')

    except Exception as e:
        print(f"Error updating application status: {e}")
        flash("An error occurred while updating application status. Please try again.", 'danger')

    return redirect(url_for('employer_manage_applications'))