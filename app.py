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


@app.route('/vefxistyaosani/upload', methods=['GET', 'POST'])
def upload_vefxistyaosani():
    """Upload Vefxistyaosani CSV file to database."""
    if request.method == 'POST':
        try:
            # Read CSV file from vefxistyaosani.csv
            csv_path = 'vefxistyaosani.csv'
            df = pd.read_csv(csv_path)

            # Expected columns
            expected_columns = {'id', 'line', 'chapter', 'chapter_id', 'strophe_id', 'line_id'}
            actual_columns = set(df.columns)

            if not expected_columns.issubset(actual_columns):
                return f'Error: CSV must contain columns: {", ".join(expected_columns)}', 400

            # Clear existing data if checkbox is checked
            if request.form.get('clear_existing'):
                VefxistyaosaniLine.query.delete()

            # Add rows to database
            count = 0
            for _, row in df.iterrows():
                line_obj = VefxistyaosaniLine(
                    line=str(row['line']) if pd.notna(row['line']) else '',
                    chapter=str(row['chapter']) if pd.notna(row['chapter']) else None,
                    chapter_id=int(row['chapter_id']) if pd.notna(row['chapter_id']) else None,
                    strophe_id=int(row['strophe_id']) if pd.notna(row['strophe_id']) else None,
                    line_id=int(row['line_id']) if pd.notna(row['line_id']) else None
                )
                db.session.add(line_obj)
                count += 1

                # Commit in batches to avoid memory issues
                if count % 1000 == 0:
                    db.session.commit()

            db.session.commit()
            total = VefxistyaosaniLine.query.count()
            return f'Successfully uploaded {count} lines! Total in database: {total}', 200

        except Exception as e:
            return f'Error processing file: {str(e)}', 400

    return render_template('upload_vefxistyaosani.html')


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
