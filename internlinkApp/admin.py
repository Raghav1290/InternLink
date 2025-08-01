from internlinkApp import app, db
from flask import redirect, render_template, session, url_for, request, flash

# Admin Home ROute
@app.route('/admin/home')
def admin_home():
     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['role']!='admin':
          return render_template('access_denied.html'), 403

     return render_template('admin_home.html')

# Admin User Management Route
@app.route('/admin/users', methods=['GET'])
def admin_user_management():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'admin':
        return render_template('access_denied.html'), 403

    users_data = []
    error_message = None

    search_name = request.args.get('name') 
    filter_role = request.args.get('role')
    filter_status = request.args.get('status')

    try:
        with db.get_cursor() as cursor:
            # Fetching all users from database
            query = "SELECT user_id, username, full_name, email, role, status FROM users WHERE 1=1"
            params = []

            # Applying filters
            if search_name:
                query += " AND full_name LIKE %s"
                params.append(f"%{search_name}%")
            if filter_role and filter_role != 'all':
                query += " AND role = %s"
                params.append(filter_role)
            if filter_status and filter_status != 'all':
                query += " AND status = %s"
                params.append(filter_status)

            query += " ORDER BY role ASC, full_name ASC;"
            cursor.execute(query, tuple(params))
            users_data = cursor.fetchall()

    except Exception as e:
        print(f"Error fetching users for admin: {e}")
        error_message = "Could not load user data."

    return render_template('admin_user_management.html',
                           users=users_data,
                           search_name=search_name,
                           filter_role=filter_role,
                           filter_status=filter_status,
                           error_message=error_message)

# Route for Admin User Management
@app.route('/admin/users/<int:user_id>/change_status', methods=['POST'])
def admin_change_user_status(user_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'admin':
        return render_template('access_denied.html'), 403

    new_status = request.form.get('status')

    # Preventing the admin no to deactivate their own user account
    if user_id == session['user_id'] and new_status == 'inactive':
        flash("You cannot deactivate your own admin account.", 'danger')
        return redirect(url_for('admin_user_management'))

    try:
        with db.get_cursor() as cursor:
            cursor.execute("UPDATE users SET status = %s WHERE user_id = %s;",
                           (new_status, user_id))
            flash(f"User ID {user_id} status updated to '{new_status}' successfully!", 'success')
    except Exception as e:
        print(f"Error changing user status: {e}")
        flash("An error occurred while updating user status. Please try again.", 'danger')

    return redirect(url_for('admin_user_management'))