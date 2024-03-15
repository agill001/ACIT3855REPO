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

# Load configuration files
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# URLs for the Storage service endpoints
create_post_url = app_config['eventstore1']['url']
follow_event_url = app_config['eventstore2']['url']

# Kafka Producer setup (lab6)
try:
    kafka_client = KafkaClient(
        hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    kafka_topic = kafka_client.topics[str.encode(
        app_config['events']['topic'])]
    kafka_producer = kafka_topic.get_sync_producer()
except Exception as e:
    print(f"Error connecting to Kafka: {e}")
    # Exit or handle the error appropriately


# Load logging configuration
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

# Create logger
logger = logging.getLogger('basicLogger')

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
