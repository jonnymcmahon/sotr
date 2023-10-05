from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q, Case, When
import boto3
import datetime
import gzip
import os
import xml.etree.ElementTree as ET
import json
from .models import Station, Journey, TOC, Route, Stop, Train
import time
import hashlib
import sys
import base64

# Create your views here.

def parse_schedule(request):

    output_filepath = download_file()
    
    xml_unzipped = gzip.open(output_filepath, 'r')

    tree = ET.parse(xml_unzipped)
    root = tree.getroot()

    today = datetime.date.today()

    for journey in root:
        
        #check if journey or association
        if 'Association' in journey.tag: continue

        #check if train is for today's timetable
        if not journey.attrib['ssd'] == today.strftime('%Y-%m-%d'): continue

        #check if passenger service
        if 'isPassengerSvc' in journey.attrib:
            if journey.attrib['isPassengerSvc'] == "false": continue

        num_stops = len(journey)-1

        route_info = find_route(journey)
        route_id = route_info[0]
        toc_id = route_info[1]
        
        #TODO: understand cancelled services
        if 'cancelReason' in journey[num_stops].tag: train_cancelled = True
        else: train_cancelled = False

        #unsure if bug in data? sometimes journey has no ptd / pta, so use wta / wtd instead
        depart = journey[0].attrib['ptd'] if ('ptd' in journey.attrib) else journey[0].attrib['wtd']

        #if time has no seconds, add 00
        if len(depart) < 6:
            depart += ':00'

        depart = datetime.datetime.strptime(depart, "%H:%M:%S").time()

        train_timestamp = datetime.datetime.combine(today, depart)

        obj = Train.objects.update_or_create(
            timestamp = train_timestamp,
            rid = journey.attrib['rid'],
            cancelled = train_cancelled,
            route_id = route_id,
            toc_id = toc_id
        )

    return render(request, 'hello2.html')

def download_file():

    s3 = boto3.client(
    's3',
    region_name= os.getenv('AWS_S3_REGION_NAME'),
    aws_access_key_id= os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key= os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    date = datetime.date.today()
    prefix_key = f'PPTimetable/{date.year}{date.month:02d}{date.day:02d}'

    timetables = s3.list_objects_v2(
        Bucket = 'darwin.xmltimetable',
        Prefix = prefix_key
    )

    length = len(timetables['Contents'])

    latest_timetable_key = timetables['Contents'][(length-1)]['Key']

    output_filename = latest_timetable_key[12:]
    output_filepath = f'/django/timetable/storage/{output_filename}'

    if not(os.path.isfile(output_filename)):
        zipped_timetable = s3.download_file(
            Bucket= os.getenv('AWS_STORAGE_BUCKET_NAME'),
            Key= latest_timetable_key,
            Filename = output_filepath
        )
    
    return(output_filepath)

def read_stations_list(request):

    with open('/django/timetable/storage/stations.json', 'r') as f:
        stations = json.load(f)

    for station in stations:

        if(len(station['tiploc']) > 1):

            if not Station.objects.filter(tiploc= station['tiploc'][0]) | Station.objects.filter(tiploc=station['tiploc'][1]):

                obj, created = Station.objects.update_or_create(
                    name = station['location'],
                    tiploc = station['tiploc'][0],
                    alternative_tiploc = station['tiploc'][1]
                )
                
                if created == False:
                    print(obj)

        else:

            if not Station.objects.filter(tiploc= station['tiploc'][0]):

                obj, created = Station.objects.update_or_create(
                    name = station['location'],
                    tiploc = station['tiploc'][0],
                )

                if created == False:
                    print(obj)

    return render(request, 'hello2.html')

def read_tocs(request):

    with open('/django/timetable/storage/toc.json', 'r') as f:
        tocs = json.load(f)

    for toc in tocs:
        obj, created = TOC.objects.update_or_create(
            name = toc['name'],
            toc = toc['toc'],
            passengerSvc = toc['passengerSvc']
        )

    return render(request, 'hello2.html')






def find_route(journey):

    #new variable station_stops as journey includes tiplocs that arent stations (junctions etc)
    station_stops = 2
    for stop in journey:
        if 'IP' in stop.tag:
            station_stops += 1

    length = len(journey)-1
    
    #if train cancelled, change lookup for final stop TODO: understand cancelled services
    if 'cancelReason' in journey[length].tag:
        length -= 1

    toc_id = TOC.objects.filter(toc = journey.attrib['toc'])[0].id

    orig_tiploc = journey[0].attrib['tpl']
    dest_tiploc = journey[length].attrib['tpl']

    route_id = None
    
    #if matches another route do a check to see if they are the same
    if Route.objects.filter(orig = orig_tiploc, dest = dest_tiploc, toc_id = toc_id, num_stops = station_stops):
        
        #get new checksum
        new_route_checksum = generate_route_checksum(journey, orig_tiploc, dest_tiploc)

        #try to find checksum in db
        if not Route.objects.filter(orig = orig_tiploc, dest = dest_tiploc, toc_id = toc_id, num_stops = station_stops, checksum = new_route_checksum):
            
            route_id = save_new_route(journey, orig_tiploc, dest_tiploc, toc_id, new_route_checksum)

    else:
        #get new route checksum
        new_route_checksum = generate_route_checksum(journey, orig_tiploc, dest_tiploc)

        #new route, add route and stops to db
        route_id = save_new_route(journey, orig_tiploc, dest_tiploc, toc_id, new_route_checksum)

    if route_id is None:
        route_id = Route.objects.filter(orig = orig_tiploc, dest = dest_tiploc, toc_id = toc_id, num_stops = station_stops, checksum = new_route_checksum).get().id

    return route_id, toc_id





def save_new_route(journey, orig_tiploc, dest_tiploc, toc_id, route_checksum):

    date = datetime.datetime.strptime(journey.attrib['ssd'], '%Y-%m-%d')
    
    route = Route(orig = orig_tiploc, dest = dest_tiploc, toc_id = toc_id, checksum = route_checksum)
    route.save()

    orig_record = Station.objects.filter(Q(tiploc = orig_tiploc)| Q(alternative_tiploc = orig_tiploc)).get()
    dest_record = Station.objects.filter(Q(tiploc = dest_tiploc)| Q(alternative_tiploc = dest_tiploc)).get()

    orig = Stop(stop_number = 1, route_id = route.id, station_id = orig_record.id)
    orig.save()

    duration_checksum = 0

    stop_no = 2

    previous_stop_time = journey[0].attrib['ptd'] if ('ptd' in journey.attrib) else journey[0].attrib['wtd']

    previous_stop_time = str_to_time(previous_stop_time)

    previous_stop_time = datetime.datetime.combine(date, previous_stop_time)

    for stop in journey:

        if 'IP' in stop.tag or 'DT' in stop.tag:
            #grab stop tiploc, time
            stop_tiploc = stop.attrib['tpl']

            #parse time to datetime obj
            stop_time = stop.attrib['pta'] if ('pta' in stop.attrib) else stop.attrib['wta']

            stop_time = str_to_time(stop_time)

            stop_time = datetime.datetime.combine(date, stop_time)

            #check if train time has passed midnight (if diff in hour > 5hrs)
            if abs(stop_time.hour - previous_stop_time.hour) > 5:
                stop_time += datetime.timedelta(days=1)
                date += datetime.timedleta(days=1)

                print(stop_time, previous_stop_time, 'NEXT DAY!!!')
            
            #find time since last stop
            next_stop_time = stop_time - previous_stop_time
            
            #move previous_stop_time one stop along
            previous_stop_time = stop_time

            stop_tiploc = check_alternative_tiplocs(stop_tiploc)

            station_record = Station.objects.filter(tiploc = stop_tiploc).get()

            #create db record
            Stop.objects.create(stop_number = stop_no, route_id = route.id, station_id = station_record.id, time_from_last = next_stop_time)

            duration_checksum += ((next_stop_time.total_seconds()/60) * stop_no)

            stop_no += 1

    route.num_stops = stop_no 
    route.duration_checksum = duration_checksum
    route.save()

    return route.id



def str_to_time(stop_time):

    #handles cases where seconds field is optional
    if len(stop_time) < 6:
        stop_time = datetime.datetime.strptime(stop_time, '%H:%M').time()
    else:
        stop_time = datetime.datetime.strptime(stop_time, '%H:%M:%S').time()

    return stop_time


def check_alternative_tiplocs(alt_tiploc):

    if alt := Station.objects.filter(alternative_tiploc = alt_tiploc).values('tiploc'):

        alt = alt.get()
        tiploc = alt['tiploc']

        return tiploc

    else:
        return alt_tiploc





def generate_route_checksum(journey, orig_tiploc, dest_tiploc):

    #check if both origin and destination tiplocs have alternatives
    orig_tiploc = check_alternative_tiplocs(orig_tiploc)

    dest_tiploc = check_alternative_tiplocs(dest_tiploc)    

    route = [orig_tiploc]

    for stop in journey:
        if 'IP' in stop.tag:
            tiploc = stop.attrib['tpl']

            tiploc = check_alternative_tiplocs(tiploc)

            route.append(tiploc)

    route.append(dest_tiploc)

    route_string = '|'.join(route)
    route_checksum = hashlib.md5(route_string.encode('utf-8')).digest()

    return route_checksum