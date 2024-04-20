./wait_for_db.sh
poetry run gunicorn gips.wsgi -w 4 -b 0.0.0.0:8000 --timeout 0
