web: gunicorn autovise.wsgi:application --log-file -
release: python manage.py migrate && python manage.py collectstatic --noinput
