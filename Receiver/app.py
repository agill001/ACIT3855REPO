import connexion
from connexion import NoContent
import yaml
import logging
import logging.config
import uuid
import requests
import datetime
import json
from pykafka import KafkaClient
import time
import os

# bef lab 10
# Load configuration files
# with open('app_conf.yml', 'r') as f:
#     app_config = yaml.safe_load(f.read())

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


# URLs for the Storage service endpoints
create_post_url = app_config['eventstore1']['url']
follow_event_url = app_config['eventstore2']['url']


# before lab9
# Kafka Producer setup (lab6)
# try:
#     kafka_client = KafkaClient(
#         hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
#     kafka_topic = kafka_client.topics[str.encode(
#         app_config['events']['topic'])]
#     kafka_producer = kafka_topic.get_sync_producer()
# except Exception as e:
#     print(f"Error connecting to Kafka: {e}")
#     # Exit or handle the error appropriately


# bef lab 10
# # Load logging configuration
# with open('log_conf.yml', 'r') as f:
#     log_config = yaml.safe_load(f.read())
#     logging.config.dictConfig(log_config)

# # Create logger
# logger = logging.getLogger('basicLogger')

""" before lab6 code  """
# def create_post(body):
#     """
#     Handle createPost event
#     """
#     trace_id = str(uuid.uuid4())  # Generate a unique trace_id
#     logger.info(
#         f"Received event createPost request with a trace id of {trace_id}")
#     body['trace_id'] = trace_id

#     response = requests.post(create_post_url, json=body, headers={
#                              'Content-Type': 'application/json'})
#     logger.info(
#         f"Returned event createPost response (Id: {trace_id}) with status {response.status_code}")
#     return NoContent, response.status_code


# def follow_event(body):
#     """
#     Handle followEvent event
#     """
#     trace_id = str(uuid.uuid4())  # Generate a unique trace_id
#     logger.info(
#         f"Received event followEvent request with a trace id of {trace_id}")
#     body['trace_id'] = trace_id

#     response = requests.post(follow_event_url, json=body, headers={
#                              'Content-Type': 'application/json'})
#     logger.info(
#         f"Returned event followEvent response (Id: {trace_id}) with status {response.status_code}")
#     return NoContent, response.status_code


""" after lab6 code  """


# Lab 9 Part 5: Establish Kafka connection when service starts
def get_kafka_producer():
    max_retries = app_config['kafka']['max_retries']
    retry_sleep_time = app_config['kafka']['retry_sleep_time']
    retry_count = 0

    while retry_count < max_retries:
        try:
            kafka_client = KafkaClient(
                hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
            kafka_topic = kafka_client.topics[str.encode(
                app_config['events']['topic'])]
            producer = kafka_topic.get_sync_producer()
            logger.info(f"Connected to Kafka on attempt {retry_count + 1}")
            return producer

        except Exception as e:
            logger.error(f"Error connecting to Kafka: {e}")
            retry_count += 1
            time.sleep(retry_sleep_time)

    logger.error("Failed to connect to Kafka after maximum retries")
    return None


kafka_producer = get_kafka_producer()


def create_post(body):
    """
    Handle createPost event
    """
    trace_id = str(uuid.uuid4())  # Generate a unique trace_id
    logger.info(
        f"Received event createPost request with a trace id of {trace_id}")
    body['trace_id'] = trace_id

    # Kafka message
    msg = {
        "type": "createPost",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    kafka_producer.produce(msg_str.encode('utf-8'))

    logger.info(f"Published createPost event (Id: {trace_id}) to Kafka")
    return NoContent, 201  # Hardcoded status code


def follow_event(body):
    """
    Handle followEvent event
    """
    trace_id = str(uuid.uuid4())  # Generate a unique trace_id
    logger.info(
        f"Received event followEvent request with a trace id of {trace_id}")
    body['trace_id'] = trace_id

    # Kafka message
    msg = {
        "type": "followEvent",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    kafka_producer.produce(msg_str.encode('utf-8'))

    logger.info(f"Published followEvent (Id: {trace_id}) to Kafka")
    return NoContent, 201  # Hardcoded status code


# Set up Connexion application
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080)
