import logging
import mysql.connector 
import sys
import os
from flask import Flask, redirect, send_from_directory, Response, render_template, jsonify, request, flash, session, url_for
from functools import wraps
from datetime import timedelta, date
from werkzeug.security import check_password_hash 
from config import Config


logger = logging.getLogger(__name__)
logging.basicConfig(filename='Del-Valle-Calendar-Tool\logs\myLog.log')

def generete_secret_key():
    return os.urandom(24).hex()

def create_app():
    # Minimal Flask app that serves delHTML.html and delCSS.css from the project root.
    #app = Flask(__name__, static_folder=BASE_DIR, template_folder=BASE_DIR)
    app = Flask(__name__)
    app.config.from_object(Config)
    app.jinja_env.add_extension('jinja2.ext.do')
    app.secret_key = generete_secret_key()
    return app

app = create_app()

# test config load
try:
    db_host = app.config['DB_HOST']
    db_user = app.config['DB_USER']
    db_password = app.config['DB_PASSWORD']
    db_name = app.config['DB_NAME']
    app_password = app.config['APP_PASSWORD_HASH']

    if None in [db_host, db_user, db_password, db_name, app_password]:
        raise ValueError("One or more database configuration values are missing")
    logger.info("Database configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load database configuration: {e}")
    logger.debug("Current app.config contents:")
    for key in app.config:
        logger.debug(f"{key}: {app.config[key]}")
    sys.exit(1)


CALENDAR = '1'
SCHOOL_DAYS = '2'


@app.route('/')
def home():
    return render_template('delHTML.html')
    #return send_from_directory(BASE_DIR, 'delHTML.html')


# Get month days from DB, return as list of dicts
def get_month_days(year, month):
    """Return a list of days in month with their bool_day status from the database."""
    db = db_connect()
    db_cursor = create_cursor(db)

    # WHERE school_year = %s AND MONTH(school_date) = %s BETWEEN YEAR(MIN(school_date)) 
    try:
        db_cursor.execute("SELECT school_date, bool_day From calendar WHERE school_year = %s AND MONTH(school_date) = %s ORDER BY school_date;", (year, month))
        rows = db_cursor.fetchall()
        month_data = [{"school_date": row[0], "bool_day": row[1]} for row in rows]
        # clean_month = arrange_month_into_weeks(month_data)
    except Exception as e:
        logger.error(f"Database query error: {e}")
    else:
        return month_data
        
# Authenticate login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/get_month/<int:year>/<int:month>')
def get_month(year, month):
    calendar = get_month_days(year, month)
    # Return data as JSON
    data = [[d.strftime('%Y-%m-%d') for d in week] for week in calendar]
    return jsonify({"calendar": data})


# DATE PAGE ROUTE OLD/TESTING AJAX FUNCTIONALITY
# ----------------------------------------------------------------------------------
@app.route('/datePageOld.html')
def date_page_old():
    yearCalendar = []

    for month in range(1, 11):
        # adjust month to start from August
        adjusted_month = (month + 6) % 12 + 1

        yearCalendar.append(get_month_days(2025, adjusted_month))

    return render_template('datePageOld.html', yearCalendar=yearCalendar)

# DATE PAGE ROUTE
# ----------------------------------------------------------------------------------
@app.route('/datePage', methods=['POST'])
def date_page():
    yearCalendar = []

    for month in range(1, 11):
        # adjust month to start from August
        adjusted_month = (month + 6) % 12 + 1

        yearCalendar.append(get_month_days(2025, adjusted_month))


    return render_template('datePage.html', yearCalendar=yearCalendar, mode='view')

@app.route('/datePage/edit', methods=['GET', 'POST'])
@login_required
def edit_date_page():
    
    
    yearCalendar = []

    for month in range(1, 11):
        # adjust month to start from August
        adjusted_month = (month + 6) % 12 + 1

        yearCalendar.append(get_month_days(2025, adjusted_month))
    
    return render_template('datePage.html', yearCalendar=yearCalendar, mode='edit')
    
@app.route('/datePage/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        app.logger.info('User attempting to log in')
        password = request.form.get('password')
        if not password.isalnum():
            error = 'non-alphanumeric entry'
            flash('password must be alphanumeric')
        elif check_password_hash(app_password, password):
            session['logged_in'] = True
            app.logger.info('User logged in successfully')
            return redirect('/datePage/edit')
    else:
        return render_template('login.html', error=error)

@app.route('/delCSS.css')
def css():

    if os.path.exists('static/css/delCSS.css'):
        return send_from_directory('/static/css', 'delCSS.css', mimetype='text/css')
    return Response('', status=204)

@app.route('/get_date')
def get_date():
    current_date = date.now().strftime("%Y-%m-%d")
    return jsonify({"current_date": current_date})

def db_connect():
    try:
        
        conn = mysql.connector.connect(
            host=db_host, 
            user=db_user,
            passwd=db_password,
            db=db_name)
    except mysql.connector.Error as err:
        print(f"Failed to connect to database: {err}")
        logger.error(f"Database connection error: {err}")
        sys.exit(1)
    return conn


def create_cursor(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("USE `dellvallecalendar`")
    except mysql.connector.Error as err:
        print(f"Failed to create cursor: {err}")
        logger.error(f"Cursor creation error: {err}")
        conn.close()
        sys.exit(1)
    return cursor

    
@app.route('/on_submit', methods=['POST'])
def on_submit():
#    data = request.form.get('picked_date')
    pickedDate = request.form.get('userDate')
    userDays = request.form.get('userDays')
    calendarOrSchoolDays = request.form.get('calendarOrSchoolDays')

    if pickedDate is None or userDays is None or calendarOrSchoolDays is None:
        logger.error("Missing form data")
        return jsonify({"error": "Missing form data"}), 400
    
    logger.info(f"Received date from form: {pickedDate}, userDays: {userDays}, calendarOrSchoolDays: {calendarOrSchoolDays}")
    
    print(f"data from form: {pickedDate}, userDays: {userDays}, calendarOrSchoolDays: {calendarOrSchoolDays}")
    # Run the DB query to compute the result (45th available day after provided date)
    db = db_connect()
    db_cursor = create_cursor(db)
    sql_str = ""
    if calendarOrSchoolDays == CALENDAR:
        sql_str = "WITH NumberedSubset AS (SELECT school_date, ROW_NUMBER() OVER (ORDER BY school_date ASC) AS RowNum FROM calendar WHERE school_date > %s ) SELECT school_date FROM NumberedSubset WHERE RowNum = %s;"
    else:
        sql_str = "WITH NumberedSubset AS (SELECT school_date, ROW_NUMBER() OVER (ORDER BY school_date ASC) AS RowNum FROM calendar WHERE school_date > %s AND bool_day = 1) SELECT school_date FROM NumberedSubset WHERE RowNum = %s;"
    try:
        db_cursor.execute(sql_str, (pickedDate, userDays,)
        )
        print("DB query executed, fetching result...")
        row = db_cursor.fetchone()
    
    except Exception as e:
        # Ensure DB resources are closed on error
        db_cursor.close()
        db.close()
        logger.error(f"Database query error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        # normal close
        try:
            db_cursor.close()
        except Exception:
            logger.error("Error closing cursor")
        try:
            db.close()
        except Exception:
            logger.error("Error closing database connection")

    app.logger.info("")
    return jsonify(result=row[0].strftime("%m/%d/%Y") if row else "No result found")

# Query to fetch the 45th available day after the provided date
# db_cursor.execute("WITH NumberedSubset AS (SELECT date, ROW_NUMBER() OVER (ORDER BY date ASC) AS RowNum FROM calendar WHERE date > '2025-10-12' AND bool_day = 1) SELECT date FROM NumberedSubset WHERE RowNum = 45;")

if __name__ == "__main__":
    app.run(debug=True)
