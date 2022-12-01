from datetime import datetime, timedelta

def date(date_time):
    date = (datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S') + timedelta(hours=3)).date()
    return date
