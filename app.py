from collections import defaultdict
import os

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from models import Aphorism, User, VefxistyaosaniLine, db

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'litera-dev-secret-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vepkhvi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'error'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')


@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')


@app.route('/contact')
def contact():
    """Render the contact page."""
    return render_template('contact.html')


@app.route('/cheracteranalysis')
def cheracteranalysis():
    """Render the character analysis page."""
    return render_template('cheracteranalysis.html')


@app.route('/examprep')
def examprep():
    """Render the exam preparation page."""
    return render_template('examprep.html')


@app.route('/moderntraslations')
def moderntraslations():
    """Render the modern translations page."""
    return render_template('moderntraslations.html')


@app.route('/practicetests')
def practicetests():
    """Render the practice tests page."""
    return render_template('practicetests.html')


@app.route('/privacypolicy')
def privacypolicy():
    """Render the privacy policy page."""
    return render_template('privacypolicy.html')


@app.route('/studyguide')
def studyguide():
    """Render the study guide page."""
    return render_template('studyguide.html')


@app.route('/syllabus')
def syllabus():
    """Render the syllabus page."""
    return render_template('syllabus.html')


@app.route('/tos')
def tos():
    """Render the terms of service / terms page."""
    return render_template('tos.html')


@app.route('/aphorisms')
def aphorisms():
    """Display all aphorisms."""
    all_aphorisms = Aphorism.query.all()
    return render_template('aphorisms.html', aphorisms=all_aphorisms)


@app.route('/vefxistyaosani')
def vefxistyaosani():
    rows = VefxistyaosaniLine.query.order_by(
        VefxistyaosaniLine.chapter_id,
        VefxistyaosaniLine.strophe_id,
        VefxistyaosaniLine.line_id,
    ).all()

    stanzas = defaultdict(list)
    for row in rows:
        stanzas[(row.chapter_id, row.strophe_id)].append(row)

    return render_template('vefxistyaosani.html', stanzas=stanzas)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Create a new scholar account."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        grade = (request.form.get('grade') or '').strip() or None
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email is required.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if email and User.query.filter_by(email=email).first():
            errors.append('An account with that email already exists.')

        if errors:
            for message in errors:
                flash(message, 'error')
            return render_template(
                'register.html',
                full_name=full_name,
                email=email,
                grade=grade or '',
            )

        user = User(full_name=full_name, email=email, grade=grade)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Welcome to Litera. Your scholar account is ready.', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Sign in an existing scholar."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash('Invalid email or password.', 'error')
            return render_template('login.html', email=email)

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.full_name}.', 'success')
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Sign out the current scholar."""
    logout_user()
    flash('You have been signed out.', 'success')
    return redirect(url_for('index'))


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
