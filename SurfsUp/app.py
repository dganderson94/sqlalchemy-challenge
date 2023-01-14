from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import datetime as dt
from dateutil.relativedelta import relativedelta
from statistics import mean


def most_recent_date(session):
    return session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]

def one_year_back(session):
    # Starting from the most recent data point in the database. 
    most_recent_dt = dt.datetime.strptime(most_recent_date(session),'%Y-%m-%d')
    # Calculate the date one year from the last date in data set.
    return most_recent_dt - relativedelta(years = 1)

def tobs_range(session, start, end):
    # Query all tobs in date range
    query = session.query(Measurement.tobs)\
        .filter(Measurement.date >= start)\
        .filter(Measurement.date <= end)
    # Convert query results into list
    query_list = [row[0] for row in query]
    # Summarize as a dictionary
    data_dict = {
        'TMIN' : min(query_list),
        'TAVG' : mean(query_list),
        'TMAX' : max(query_list)
    }
    return data_dict


##################
# Database Setup #
##################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Station = Base.classes.station
Measurement = Base.classes.measurement

###############
# Flask Setup #
###############
app = Flask(__name__)


################
# Flask Routes #
################

@app.route("/")
def welcome():
    """List all available routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/(yyyy-mm-dd)<br/>"
        f"/api/v1.0/(yyyy-mm-dd)/(yyyy-mm-dd)"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Retrieve the last 12 months of precipitation data"""
    one_year_back_dt = one_year_back(session)

    # Perform a query to retrieve the data and precipitation scores
    precip_data = session.query(Measurement.date,Measurement.prcp)\
        .filter(Measurement.date > one_year_back_dt).all()

    session.close()

    # Convert query results into dictionary
    query_dict = {row[0] : row[1] for row in precip_data}

    return jsonify(query_dict)


@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Retrieve a list of stations"""
    # Perform a query to retrieve names of stations
    stations = session.query(Station.name).all()

    session.close()

    # Convert query results into list
    query_list = [row[0] for row in stations]

    return jsonify(query_list)


@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Retrieve the dates and temperature observations of the most-active station for the previous year of data"""
    # Get one year back from the most recent observation
    one_year_back_dt = one_year_back(session)

    # Get the most active station id
    most_active = session.query(Station.station)\
    .filter(Station.station == Measurement.station)\
    .group_by(Measurement.station)\
    .order_by(func.count(Measurement.id).desc()).first()[0]

    observations = session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.station == most_active)\
        .filter(Measurement.date > one_year_back_dt)

    session.close()

    # Convert query results into list
    query_list = [{row[0] : row[1]} for row in observations]

    return jsonify(query_list)


@app.route("/api/v1.0/<start>")
def start(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Retrieve temperature data after the given date"""
    # Pass everything into tobs_range, using the most recent date in the absence of a given end date
    data_dict = tobs_range(session, start, most_recent_date(session))

    session.close()

    return jsonify(data_dict)


@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Retrieve temperature data after the given date"""
    # Pass everything into tobs_range
    data_dict = tobs_range(session, start, end)

    session.close()

    return jsonify(data_dict)


if __name__ == "__main__":
    app.run(debug=True)