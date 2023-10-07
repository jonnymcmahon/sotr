from django.shortcuts import render
import datetime as dt
import logging
from timetable.models import Train, Route, Stop, Station, Delay
from timetable.views import str_to_time, check_alternative_tiplocs
from stompclient.models import Error

# Create your views here.

def handle(xml):

    if 'ns5:Location' in xml['uR']['TS'][0]:
        journey = xml['uR']['TS'][0]['ns5:Location']
    else:
        return #TODO understand LateReason blocks

    if 'ns5:arr' in journey[0]:
        if journey[0]['ns5:arr']['@delayed'] == True:

            print('Delay!')

            rid = xml['uR']['TS'][0]['@rid']

            #check if train exists
            if Train.objects.filter(rid = rid):

                train = Train.objects.filter(rid = rid).get()

                #individual dates / previous for scheduled vs expected to account for cross-midnight changes
                sched_date = exp_date = dt.datetime.strptime(xml['uR']['TS'][0]['@ssd'], '%Y-%m-%d')

                previous_sched_arrival = previous_exp_arrival = None

                for stop in journey:

                    #check if arr block as schedule includes passing tiplocs
                    if 'ns5:arr' in stop:

                        stop_tiploc = stop['@tpl']
                        stop_tiploc = check_alternative_tiplocs(stop_tiploc)

                        sched_time = stop['@pta'] if '@pta' in stop else stop['@wta']

                        sched_arrival = dt.datetime.combine(sched_date, str_to_time(sched_time))
                        exp_arrival = dt.datetime.combine(exp_date, str_to_time(stop['ns5:arr']['@et']))

                        #check if either scheduled or expected has crossed midnight
                        if previous_sched_arrival is not None:
                            if abs(sched_arrival.hour - previous_sched_arrival.hour) > 5:
                                sched_arrival += dt.timedelta(days=1)
                                sched_date += dt.timedelta(days=1)

                        if previous_exp_arrival is not None:
                            if abs(exp_arrival.hour - previous_exp_arrival.hour) > 5:
                                exp_arrival += dt.timedelta(days=1)
                                exp_date += dt.timedelta(days=1)                
                        
                        previous_sched_arrival = sched_arrival
                        previous_exp_arrival = exp_arrival

                        delay = exp_arrival - sched_arrival
                    
                        train_id = train.id
                        route_id = train.route_id
                        toc_id = train.toc_id

                        station_id = Station.objects.filter(tiploc = stop_tiploc).get().id

                        stop_id = Stop.objects.filter(route_id = route_id, station_id = station_id).get().id

                        obj, created = Delay.objects.update_or_create(
                            delay = delay,
                            route_id = route_id,
                            stop_id = stop_id,
                            toc_id = toc_id,
                            train_id = train_id
                        )

def handle_error(msg, e):

    Error.objects.create(timestamp = dt.datetime.now(), error_msg = e, stomp_msg = msg)