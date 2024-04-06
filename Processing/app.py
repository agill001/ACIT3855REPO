import connexion
from connexion import NoContent
import yaml
import logging.config
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from stats import Base, SportGramStats
import datetime
import requests
import os
from flask_cors import CORS

# before lab 10
# Load configurations
# with open('app_conf.yml', 'r') as f:
#     app_config = yaml.safe_load(f.read())

# with open('log_conf.yml', 'r') as f:
#     log_config = yaml.safe_load(f.read())

# logging.config.dictConfig(log_config)
# logger = logging.getLogger('basicLogger')

# Lab10 Part 1: Determine the environment and set configuration file paths
if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

# Load configurations from determined paths
with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')
logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)


# Database setup
DB_ENGINE = create_engine(f"sqlite:///{app_config['datastore']['filename']}")
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def get_stats():
    # starting requests for stats n log info
    logger.info("Request for SportGram statistics has started")

    session = DB_SESSION()

    try:
        # query db for recent stats entry
        stats = session.query(SportGramStats).order_by(
            SportGramStats.id.desc()).first()

# if stats exist put em in dictionary
        if stats:
            stats_dict = {
                "num_create_posts": stats.num_create_posts,
                "num_follow_events": stats.num_follow_events,
                "total_likes": stats.total_likes,
                "total_follow_count": stats.total_follow_count,
                "last_updated": stats.last_updated.strftime("%Y-%m-%d %H:%M:%S")
            }

            logger.debug(f"Current statistics: {stats_dict}")
            session.close()
            return stats_dict, 200
        else:
            logger.error("Statistics do not exist")
            session.close()
            return "Statistics do not exist", 404
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        session.close()
        return {"message": "An error occurred while processing your request.", "details": str(e)}, 500


def populate_sportgram_stats():
    # start of it with log message
    logger.info("Periodic processing of SportGram statistics has started")

    session = DB_SESSION()

    try:
        # reading stats from database
        stats = session.query(SportGramStats).order_by(
            SportGramStats.id.desc()).first()
        # if stats dont exist use default values
        last_updated = stats.last_updated if stats else datetime.datetime.min

        # get datetime
        current_datetime = datetime.datetime.now()

        # query 2 end points from data store service
        createPost_response = requests.get(
            f"{app_config['eventstore']['url']}/createPost-events",
            params={'start_timestamp': last_updated.strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_timestamp': current_datetime.strftime('%Y-%m-%dT%H:%M:%S')})
        followEvent_response = requests.get(
            f"{app_config['eventstore']['url']}/followEvent-events",
            params={'start_timestamp': last_updated.strftime('%Y-%m-%dT%H:%M:%S'),
                    'end_timestamp': current_datetime.strftime('%Y-%m-%dT%H:%M:%S')})

        # checking if they are successful
        if createPost_response.status_code == 200 and followEvent_response.status_code == 200:

            createPost_data = createPost_response.json()
            followEvent_data = followEvent_response.json()

            # Logging each createPost event processed
            for event in createPost_data:
                logger.debug(
                    f"Processing createPost event with trace_id: {event.get('trace_id')}")

            # Logging each followEvent processed
            for event in followEvent_data:
                logger.debug(
                    f"Processing followEvent with trace_id: {event.get('trace_id')}")

            # Process events and update statistics
            total_likes = sum(event['likesCount'] for event in createPost_data)
            total_follow_count = sum(event['followCount']
                                     for event in followEvent_data)

            # Log for each type of event
            logger.info(
                f"Processing {len(createPost_data)} createPost events from {last_updated} to {current_datetime}")
            logger.info(
                f"Processing {len(followEvent_data)} followEvent events from {last_updated} to {current_datetime}")

# update or make new stats in the databse
            if stats:
                stats.num_create_posts += len(createPost_data)
                stats.num_follow_events += len(followEvent_data)
                stats.total_likes += total_likes
                stats.total_follow_count += total_follow_count
                stats.last_updated = current_datetime
            else:
                new_stats = SportGramStats(
                    num_create_posts=len(createPost_data),
                    num_follow_events=len(followEvent_data),
                    total_likes=total_likes,
                    total_follow_count=total_follow_count,
                    last_updated=current_datetime
                )
                session.add(new_stats)

            session.commit()
            logger.info("SportGram statistics updated successfully.")
        else:
            logger.error(
                f"Failed to fetch new events. CreatePost status: {createPost_response.status_code}, FollowEvent status: {followEvent_response.status_code}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        session.close()
        logger.info("Periodic processing of SportGram statistics has ended")


# lab8
# Setup connexion with CORS
app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("openapi.yml",
            strict_validation=True,
            validate_responses=True)


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_sportgram_stats, 'interval',
                  seconds=app_config['scheduler']['period_sec'])
    sched.start()


# # before lab8
# app = connexion.FlaskApp(__name__, specification_dir='./')
# app.add_api('openapi.yml', strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100)
