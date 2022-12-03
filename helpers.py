from datetime import datetime, timedelta
import os

ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}


def date(date_time):
    date = (datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)).date()
    return date

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
