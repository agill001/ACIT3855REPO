import connexion
import yaml
import logging.config
import json
from pykafka import KafkaClient

from flask_cors import CORS

# Load configurations
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


# Function to retrieve a specific 'createPost' event by index


def get_create_post_event(index):
    # Set up Kafka client connection
    hostname = "%s:%d" % (
        app_config["events"]["hostname"], app_config["events"]["port"])
    # Connects to Kafka using the hostname and port from config
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode("events")]  # Specifies the Kafka topic

    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True, consumer_timeout_ms=1000)
    logger.info("Retrieving createPost event at index %d" % index)

# Initialize a counter to track message index
    count = 0
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)

            if msg['type'] == 'createPost':
                if count == index:
                    return msg['payload'], 200
                count += 1

    except:
        logger.error("No more messages found")

    logger.error("Could not find createPost event at index %d" % index)
    return {"message": "Not Found"}, 404


def get_follow_event(index):
    hostname = "%s:%d" % (
        app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode("events")]

    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True, consumer_timeout_ms=1000)
    logger.info("Retrieving followEvent at index %d" % index)

    count = 0
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)

            if msg['type'] == 'followEvent':
                if count == index:
                    return msg['payload'], 200
                count += 1

    except:
        logger.error("No more messages found")

    logger.error("Could not find followEvent at index %d" % index)
    return {"message": "Not Found"}, 404


app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("openapi.yml",
            strict_validation=True,
            validate_responses=True)

if __name__ == "__main__":

    app.run(port=8110)
