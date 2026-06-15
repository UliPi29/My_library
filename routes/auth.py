from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import User
from extensions import login_manager

bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(login=login).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            nxt = request.args.get('next')
            if nxt and nxt.startswith('/'):
                return redirect(nxt)
            return redirect(url_for('main.index'))
        else:
            flash(
                'Невозможно аутентифицироваться с указанными логином и паролем',
                'danger'
            )

    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('main.index'))