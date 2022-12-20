from datetime import datetime, timedelta
import os

ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}

# Format date and time (3 hours added for local time in Turkiye)
def date(date_time):
    date = (datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)).date()
    return date

def time_filter(date_time):
    time = (datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)).time()
    return time


# Cheks file format for profile pictures to be uploaded
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
