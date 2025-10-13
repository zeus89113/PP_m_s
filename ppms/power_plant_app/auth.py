from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User
from functools import wraps


bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = User.query.get(user_id) if user_id else None


@bp.app_context_processor
def inject_user():
    return {
        'current_user': g.user,
        'is_authenticated': g.user is not None
    }


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login', next=request.path))
        return view_func(**kwargs)
    return wrapped_view


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(**kwargs):
            if g.user is None:
                return redirect(url_for('auth.login', next=request.path))
            if g.user.role not in roles and g.user.role != 'admin':
                flash('You do not have permission to access this resource.', 'error')
                return redirect(url_for('dashboard.nuclear_dashboard'))
            return view_func(**kwargs)
        return wrapped_view
    return decorator


@bp.route('/manage_users', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_users():
    if request.method == 'POST':
        # --- This is the complete logic from your original register function ---
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'operator').strip().lower()

        if not username or not password:
            flash('Username and password are required.', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
        elif role not in ['admin', 'operator', 'safety', 'environment']:
            flash('Invalid role selected.', 'error')
        else:
            user = User(
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
            )
            db.session.add(user)
            db.session.commit()
            flash(f'User "{username}" created successfully.', 'success')
            # Redirect back to the same page to show the new user in the list
            return redirect(url_for('auth.manage_users'))
        # --- End of copied logic ---
            
    # Fetch all existing users to display them on the page
    all_users = User.query.all()
    return render_template('manage_users.html', users=all_users)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        next_url = request.args.get('next') or url_for('dashboard.nuclear_dashboard')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session['user_id'] = user.id
            return redirect(next_url)
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


