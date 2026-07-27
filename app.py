from flask import Flask, render_template

app = Flask(__name__)


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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

