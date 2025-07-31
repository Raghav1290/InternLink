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