from django.shortcuts import render
import datetime as dt
import logging
from timetable.models import Train, Route, Stop

# Create your views here.

def handle(msg, xml):

    stops_remaining = len(xml['uR']['TS'][0]['ns5:Location'])

    print(stops_remaining)
    print(msg)
    return

    arrival = xml['uR']['TS'][0]['ns5:Location'][count]

    if 'ns5:arr' in arrival:
        if arrival['ns5:arr']['@delayed'] == True:

            if '@et' in arrival['ns5:arr']:
                actual = dt.datetime.strptime(arrival['ns5:arr']['@et'], '%H:%M')
            else:
                actual = None

            if '@pta' in arrival:
                sched = dt.datetime.strptime(arrival['@pta'], '%H:%M')
            else:
                sched = None

            if sched is not None and actual is not None:
                
                rid = xml['uR']['TS'][0]['@rid']
                uid = xml['uR']['TS'][0]['@uid']
                delayed = actual - sched
                
                delayed_secs = int(delayed.total_seconds())

                print(msg)

                # sql = f'UPDATE timetable_journey SET "arrivalTime" = \'{actual.strftime("%H:%M:%S")}\', "delayedTime" = \'{delayed_secs}\' WHERE ("rid" = \'{rid}\') AND ("uid" = \'{uid}\')'
                # print(sql)
                # cursor.execute(sql)
                # connection.commit()

                logging.info('Delayed, scheduled: %s, actual %s. Service delayed by %s', sched.time(), actual.time(), (actual-sched))
