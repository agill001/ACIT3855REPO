import logging.config
import connexion
from connexion import NoContent
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
import yaml
import json
from datetime import datetime
from dateutil import parser
from create_tables import CreatePostEvent, FollowEvent
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread

# Load configurations
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

DATABASE_URI = f"mysql+pymysql://{app_config['datastore']['user']}:{app_config['datastore']['password']}@{app_config['datastore']['hostname']}:{app_config['datastore']['port']}/{app_config['datastore']['db']}"
engine = create_engine(DATABASE_URI)
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


# def get_createPost_events(start_timestamp, end_timestamp):
#     session = Session()
#     try:
#         start = datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S")
#         end = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S")

#         logger.info(
#             f"Fetching createPost events from {start_timestamp} to {end_timestamp}")
#         results = session.query(CreatePostEvent).filter(
#             and_(CreatePostEvent.date_created >= start,
#                  CreatePostEvent.date_created < end)
#         ).all()
#         logger.info(f"Successfully fetched {len(results)} createPost events")
#         return [result.to_dict() for result in results], 200
#     except Exception as e:
#         logger.error(f"Error fetching createPost events: {e}")
#         return NoContent, 500
#     finally:
#         session.close()


# def get_followEvent_events(start_timestamp, end_timestamp):
#     session = Session()
#     try:
#         start = datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S")
#         end = datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S")

#         logger.info(
#             f"Fetching followEvent events from {start_timestamp} to {end_timestamp}")
#         results = session.query(FollowEvent).filter(
#             and_(FollowEvent.date_created >= start,
#                  FollowEvent.date_created < end)
#         ).all()
#         logger.info(f"Successfully fetched {len(results)} followEvent events")
#         return [result.to_dict() for result in results], 200
#     except Exception as e:
#         logger.error(f"Error fetching followEvent events: {e}")
#         return NoContent, 500
#     finally:
#         session.close()


# Function to process Kafka messages
def process_messages():
    try:
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

            logger.debug(f"Stored event request successfully.")

    except Exception as e:
        print(f"error: {e}")


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api('openapi.yml', strict_validation=True, validate_responses=True)

if __name__ == '__main__':
    t1 = Thread(target=process_messages)
    t1.daemon = True
    t1.start()
    app.run(port=8090)
