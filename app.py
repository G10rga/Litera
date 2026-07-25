from flask import Flask, render_template
app = Flask(__name__, static_folder='static', static_url_path='')


@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/work.html')
def work():
    return render_template('work.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)