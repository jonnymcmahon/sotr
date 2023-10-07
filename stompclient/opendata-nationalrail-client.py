#
# National Rail Open Data client demonstrator
# Copyright (C)2019-2022 OpenTrainTimes Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import stomp
import zlib
import io
import time
import socket
import logging
import xmlschema
import os
from dotenv import load_dotenv
import sys
import django

sys.path.append('/django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sotr.settings')
django.setup()

import views

dotenv_path = os.path.join('/django/sotr/.env')

load_dotenv(dotenv_path)

logging.basicConfig(format='%(asctime)s %(levelname)s\t%(message)s', level=logging.INFO)

USERNAME = os.getenv('STOMP_USERNAME')
PASSWORD = os.getenv('STOMP_PASSWORD')
HOSTNAME = os.getenv('STOMP_HOSTNAME')
HOSTPORT = 61613
# Always prefixed by /topic/ (it's not a queue, it's a topic)
TOPIC = '/topic/darwin.pushport-v16'

CLIENT_ID = socket.getfqdn()
HEARTBEAT_INTERVAL_MS = 15000
RECONNECT_DELAY_SECS = 15

if USERNAME == '':
    logging.error("Username not set - please configure your username and password in opendata-nationalrail-client.py!")

schema = xmlschema.XMLSchema('stompclient/ppv16/rttiPPTSchema_v16.xsd')

def connect_and_subscribe(connection):
    if stomp.__version__[0] < 5:
        connection.start()

    connect_header = {'client-id': USERNAME + '-' + CLIENT_ID}
    subscribe_header = {'activemq.subscriptionName': CLIENT_ID}

    connection.connect(username=USERNAME,
                       passcode=PASSWORD,
                       wait=True,
                       headers=connect_header)

    connection.subscribe(destination=TOPIC,
                         id='1',
                         ack='auto',
                         headers=subscribe_header)


class StompClient(stomp.ConnectionListener):

    def on_heartbeat(self):
        logging.info('Received a heartbeat')

    def on_heartbeat_timeout(self):
        logging.error('Heartbeat timeout')

    def on_error(self, headers, message):
        logging.error(message)

    def on_disconnected(self):
        logging.warning('Disconnected - waiting %s seconds before exiting' % RECONNECT_DELAY_SECS)
        time.sleep(RECONNECT_DELAY_SECS)
        exit(-1)

    def on_connecting(self, host_and_port):
        logging.info('Connecting to ' + host_and_port[0])

    def on_message(self, frame):
        try:
            logging.info('Message sequence=%s, type=%s received', frame.headers['SequenceNumber'],
                            frame.headers['MessageType'])

            if frame.headers['MessageType'] == 'TS':
                bio = io.BytesIO()
                bio.write(str.encode('utf-16'))
                bio.seek(0)
                msg = zlib.decompress(frame.body, zlib.MAX_WBITS | 32)
                xml = schema.to_dict(msg)
                
                views.handle(xml)

        except Exception as e:
            views.handle_error(msg, e)


conn = stomp.Connection12([(HOSTNAME, HOSTPORT)],
                          auto_decode=False,
                          heartbeats=(HEARTBEAT_INTERVAL_MS, HEARTBEAT_INTERVAL_MS))

conn.set_listener('', StompClient())
connect_and_subscribe(conn)

while True:
    time.sleep(1)

cursor.close()
conn.disconnect()