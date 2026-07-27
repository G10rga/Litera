from flask import Flask, render_template, request
from models import db, Aphorism, VefxistyaosaniLine
import pandas as pd

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vepkhvi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)


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
    """Display all Vefxistyaosani lines."""
    page = request.args.get('page', 1, type=int)
    per_page = 50

    paginated_lines = VefxistyaosaniLine.query.paginate(page=page, per_page=per_page)
    return render_template('vefxistyaosani.html', pagination=paginated_lines)


# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
