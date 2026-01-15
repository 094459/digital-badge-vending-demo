from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import os

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for admin access"""
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin')
        
        if password == admin_password:
            session['authenticated'] = True
            next_page = request.args.get('next', '/')
            return redirect(next_page)
        else:
            flash('Invalid password', 'error')
    
    return render_template('login.html')


@bp.route('/logout')
def logout():
    """Logout"""
    session.pop('authenticated', None)
    return redirect(url_for('public.index'))
