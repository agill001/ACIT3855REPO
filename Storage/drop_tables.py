# import mysql.connector

# db_conn = mysql.connector.connect(
#     host="localhost", user="agill", password="123#Password", database="lab4")
# db_cursor = db_conn.cursor()

# db_cursor.execute('''
# DROP TABLE IF EXISTS create_post_events, follow_events
# ''')

# db_conn.commit()
# db_conn.close()


import mysql.connector
import yaml

# Load configuration
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f)

# Database Configuration
# db_user = app_config['datastore']['user']
# db_password = app_config['datastore']['password']
# db_hostname = app_config['datastore']['hostname']
# db_port = app_config['datastore']['port']
# db_name = app_config['datastore']['db']

db_user = 'user'
db_password = 'Password'
db_hostname = 'acit3855lab6.eastus.cloudapp.azure.com'
db_port = '3306'
db_name = 'events'

# Establish Connection
db_conn = mysql.connector.connect(
    host=db_hostname, user=db_user, password=db_password, database=db_name)
db_cursor = db_conn.cursor()

# Drop Tables
db_cursor.execute('DROP TABLE IF EXISTS create_post_events')
db_cursor.execute('DROP TABLE IF EXISTS follow_events')

# Commit Changes and Close Connection
db_conn.commit()
db_conn.close()
