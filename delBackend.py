import logging
import mysql.connector 
import sys
import os
from flask import Flask, send_from_directory, Response, render_template, jsonify, request
from datetime import timedelta, date


logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/myLog.log')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_app():
    # Minimal Flask app that serves delHTML.html and delCSS.css from the project root.
    app = Flask(__name__, static_folder=BASE_DIR, template_folder=BASE_DIR)
    app.jinja_env.add_extension('jinja2.ext.do')
    return app

app = create_app()

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
@app.route('/datePage')
def date_page():
    yearCalendar = []

    for month in range(1, 11):
        # adjust month to start from August
        adjusted_month = (month + 6) % 12 + 1

        yearCalendar.append(get_month_days(2025, adjusted_month))


    return render_template('datePage.html', yearCalendar=yearCalendar)

   
    # calendar = get_year_calendar()
    # return render_template('datePage.html', calendar=calendar)

    # today = date.today()
    # year, month = today.year, today.month

    # first_of_month = date(today.year, today.month, 1)
    # last_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1) if today.month < 12 else date(today.year + 1, 1, 1) - timedelta(days=1)
    # date_range = [first_of_month + timedelta(days=i) for i in range((last_of_month - first_of_month).days + 1)]
    # return render_template('datePage.html', today=today, date_range=date_range)
    #return send_from_directory(BASE_DIR, 'datePage.html')

@app.route('/delCSS.css')
def css():
    css_path = os.path.join(BASE_DIR, 'delCSS.css')
    if os.path.exists(css_path):
        return send_from_directory(BASE_DIR, 'delCSS.css', mimetype='text/css')
    return Response('', status=204)

@app.route('/get_date')
def get_date():
    current_date = date.now().strftime("%Y-%m-%d")
    return jsonify({"current_date": current_date})

def db_connect():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            passwd="Guitarist0810$",
            db="dellvallecalendar")
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

get_month_days(2025, 11)
    
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

    return jsonify(result=row[0].strftime("%Y-%m-%d") if row else "No result found")

# Query to fetch the 45th available day after the provided date
# db_cursor.execute("WITH NumberedSubset AS (SELECT date, ROW_NUMBER() OVER (ORDER BY date ASC) AS RowNum FROM calendar WHERE date > '2025-10-12' AND bool_day = 1) SELECT date FROM NumberedSubset WHERE RowNum = 45;")

if __name__ == "__main__":
    app.run(debug=True)
