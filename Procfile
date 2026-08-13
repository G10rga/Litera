web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60
release: flask --app wsgi:application db upgrade
