import logging.config
import connexion
from connexion import NoContent
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
import yaml
import json
import time
from datetime import datetime
from dateutil import parser
from create_tables import CreatePostEvent, FollowEvent
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import os


# before lab10
# Load configurations
# with open('app_conf.yml', 'r') as f:
#     app_config = yaml.safe_load(f.read())

# with open('log_conf.yml', 'r') as f:
#     log_config = yaml.safe_load(f.read())
#     logging.config.dictConfig(log_config)

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


DATABASE_URI = f"mysql+pymysql://{app_config['datastore']['user']}:{app_config['datastore']['password']}@{app_config['datastore']['hostname']}:{app_config['datastore']['port']}/{app_config['datastore']['db']}"
# engine = create_engine(DATABASE_URI)
# Lab 9 Part 6: Modify the create_engine call to manage connection pool
engine = create_engine(DATABASE_URI, pool_size=10,
                       pool_recycle=3600, pool_pre_ping=True)
Session = sessionmaker(bind=engine)


# Define event handling functions


def create_post(body):
    """
    Store a new createPost event in the database.
    """
    session = Session()
    new_event = CreatePostEvent(
        postId=body['postId'],
        content=body['content'],
        eventDetails=json.dumps(body['eventDetails']),
        userTags=json.dumps(body['userTags']),
        timestamp=body['timestamp'],
        likesCount=body['likesCount'],
        trace_id=body['trace_id']
    )
    session.add(new_event)
    session.commit()
    session.close()
    logger.info(f"Stored createPost event with trace ID {body['trace_id']}")
    return NoContent, 201


def follow_event(body):
    """
    Store a new followEvent event in the database.
    """
    session = Session()
    new_event = FollowEvent(
        eventId=body['eventId'],
        eventName=body['eventName'],
        followedBy=body['followedBy'],
        followCount=body['followCount'],
        trace_id=body['trace_id']
    )
    session.add(new_event)
    session.commit()
    session.close()
    logger.info(f"Stored followEvent with trace ID {body['trace_id']}")
    return NoContent, 201

# # Functions to retrieve events


def get_createPost_events(start_timestamp, end_timestamp):
    session = Session()
    try:
        start = datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S")

        logger.info(
            f"Fetching createPost events from {start_timestamp} to {end_timestamp}")
        results = session.query(CreatePostEvent).filter(
            and_(CreatePostEvent.date_created >= start,
                 CreatePostEvent.date_created < end)
        ).all()
        logger.info(f"Successfully fetched {len(results)} createPost events")
        return [result.to_dict() for result in results], 200
    except Exception as e:
        logger.error(f"Error fetching createPost events: {e}")
        return NoContent, 500
    finally:
        session.close()


def get_followEvent_events(start_timestamp, end_timestamp):
    session = Session()
    try:
        start = datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S")
        end = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S")

        logger.info(
            f"Fetching followEvent events from {start_timestamp} to {end_timestamp}")
        results = session.query(FollowEvent).filter(
            and_(FollowEvent.date_created >= start,
                 FollowEvent.date_created < end)
        ).all()
        logger.info(f"Successfully fetched {len(results)} followEvent events")
        return [result.to_dict() for result in results], 200
    except Exception as e:
        logger.error(f"Error fetching followEvent events: {e}")
        return NoContent, 500
    finally:
        session.close()

# before lab9
# Function to process Kafka messages
# def process_messages():
#     try:
#         hostname = "%s:%d" % (
#             app_config["events"]["hostname"], app_config["events"]["port"])
#         client = KafkaClient(hosts=hostname)
#         topic = client.topics[str.encode(app_config["events"]["topic"])]
#         consumer = topic.get_simple_consumer(consumer_group=b'event_group',
#                                              reset_offset_on_start=False,
#                                              auto_offset_reset=OffsetType.LATEST)

#         for msg in consumer:
#             msg_str = msg.value.decode('utf-8')
#             msg = json.loads(msg_str)
#             logger.info("Message: %s" % msg)

# # Process different types of messages
#             if msg["type"] == "createPost":
#                 payload = msg["payload"]
#                 create_post(payload)
#                 logger.info("create post added")

#             elif msg["type"] == "followEvent":
#                 payload = msg["payload"]
#                 follow_event(payload)
#                 logger.info("follow event added")

#             consumer.commit_offsets()

#             logger.debug(f"Stored event request successfully.")

#     except Exception as e:
#         print(f"error: {e}")


# lab9
def process_messages():
    # Lab 9 Part 4: Define a maximum number of retries and retry sleep time
    max_retries = app_config['kafka']['max_retries']
    retry_sleep_time = app_config['kafka']['retry_sleep_time']
    retry_count = 0

    # Lab 9 Part 4: Retry logic for Kafka connection
    while retry_count < max_retries:
        try:
            logger.info(
                f"Trying to connect to Kafka, attempt {retry_count + 1}")
            hostname = "%s:%d" % (
                app_config["events"]["hostname"], app_config["events"]["port"])
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config["events"]["topic"])]
            consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                                 reset_offset_on_start=False,
                                                 auto_offset_reset=OffsetType.LATEST)

            for msg in consumer:
                msg_str = msg.value.decode('utf-8')
                msg = json.loads(msg_str)
                logger.info("Message: %s" % msg)

                # Process different types of messages
                if msg["type"] == "createPost":
                    payload = msg["payload"]
                    create_post(payload)
                    logger.info("create post added")

                elif msg["type"] == "followEvent":
                    payload = msg["payload"]
                    follow_event(payload)
                    logger.info("follow event added")

                consumer.commit_offsets()

                logger.debug("Stored event request successfully.")

            break  # Successful connection, break out of the loop

        except Exception as e:
            logger.error(f"Error connecting to Kafka: {e}")
            time.sleep(retry_sleep_time)
            retry_count += 1

    if retry_count == max_retries:
        logger.error("Failed to connect to Kafka after maximum retries")


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", base_path="/storage",
            strict_validation=True, validate_responses=True)

if __name__ == '__main__':
    t1 = Thread(target=process_messages)
    t1.daemon = True
    t1.start()
    app.run(port=8090)
