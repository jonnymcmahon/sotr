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
from .models import Station, Journey, TOC, Route, Stop
import time

# Create your views here.

def parse_schedule(request):

    output_filepath = download_file()
    
    xml_unzipped = gzip.open(output_filepath, 'r')

    tree = ET.parse(xml_unzipped)
    root = tree.getroot()

    for journey in root:
        
        #check if journey or association
        if 'Association' in journey.tag: continue

        #check if train is for today's timetable
        if not journey.attrib['ssd'] == datetime.date.today().strftime('%Y-%m-%d'): continue

        #check if passenger service
        if 'isPassengerSvc' in journey.attrib:
            if journey.attrib['isPassengerSvc'] == "false": continue

        num_stops = len(journey)-1
        
        #if train cancelled, change lookup for final stop TODO: understand cancelled services
        if 'cancelReason' in journey[num_stops].tag:
            num_stops -= 1

        # print(journey[0].attrib['tpl'], journey[num_stops].attrib['tpl'], journey.attrib['toc'])

        toc_record = TOC.objects.filter(toc = journey.attrib['toc'])[0]

        orig_tiploc = journey[0].attrib['tpl']
        dest_tiploc = journey[num_stops].attrib['tpl']

        orig = Station.objects.filter(Q(tiploc = orig_tiploc)| Q(alternative_tiploc = orig_tiploc)).get()
        dest = Station.objects.filter(Q(tiploc = dest_tiploc)| Q(alternative_tiploc = dest_tiploc)).get()

        #unsure if bug in data? sometimes journey has no ptd / pta, so use wta / wtd instead
        depart = journey[0].attrib['ptd'] if ('ptd' in journey.attrib) else journey[0].attrib['wtd']
        arrive = journey[num_stops].attrib['pta'] if ('pta' in journey.attrib) else journey[num_stops].attrib['wta']

        obj, created = Journey.objects.update_or_create(
            date = journey.attrib['ssd'],
            origin_id = orig.id,
            destination_id = dest.id,
            departureTime = depart,
            arrivalTime = arrive,
            uid = journey.attrib['uid'],
            rid = journey.attrib['rid'],
            toc_id = toc_record.id
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
    prefix_key = f'PPTimetable/{date.year}{date.month:02d}{date.day}'

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

def find_routes(request):
    # output_filepath = download_file()
    output_filepath = '/django/timetable/storage/20230925020504_v8.xml.gz'

    xml_unzipped = gzip.open(output_filepath, 'r')

    tree = ET.parse(xml_unzipped)
    root = tree.getroot()

    for journey in root:
        
        #check if journey or association
        if 'Association' in journey.tag: continue
        
        #check if passenger service
        if 'isPassengerSvc' in journey.attrib:
            if journey.attrib['isPassengerSvc'] == "false": continue

        #check if train is for today's timetable
        # if not journey.attrib['ssd'] == datetime.date.today().strftime('%Y-%m-%d'): continue
        if not journey.attrib['ssd'] == '2023-09-25': continue
        #new variable station_stops as journey includes tiplocs that arent stations (junctions etc)
        station_stops = 2

        for stop in journey:
            if 'IP' in stop.tag:
                station_stops += 1

        length = len(journey)-1
        
        #if train cancelled, change lookup for final stop TODO: understand cancelled services
        if 'cancelReason' in journey[length].tag:
            length -= 1

        toc_record = TOC.objects.filter(toc = journey.attrib['toc'])[0]

        orig_tiploc = journey[0].attrib['tpl']
        dest_tiploc = journey[length].attrib['tpl']
        
        #if matches another route do a check to see if they are the same
        if Route.objects.filter(orig = orig_tiploc, dest = dest_tiploc, toc_id = toc_record.id, num_stops = station_stops):

            route_match = False

            routes = Route.objects.filter(orig = orig_tiploc, dest = dest_tiploc, toc_id = toc_record.id, num_stops = station_stops)


            #TODO: origin / destination filtering for alternative tiplocs
            new_route = [orig_tiploc]

            for stop in journey:
                if 'IP' in stop.tag:
                    tiploc = stop.attrib['tpl']

                    if alt := Station.objects.filter(alternative_tiploc = tiploc).values('tiploc'):
                        alt = alt.get()

                        tiploc = alt['tiploc']

                    new_route.append(tiploc)

            new_route.append(dest_tiploc)
            #TODO maybe figure out a checksum system to make this quicker?
            for route in routes:

                stop_ids = Stop.objects.filter(route_id = route.id).values_list('station_id', flat=True)

                check_route = {}

                check_route[0] = []
                check_route[1] = []

                for stop_id in stop_ids:
                    station = Station.objects.filter(id = stop_id).values('tiploc', 'alternative_tiploc').get()

                    #if a station has multiple tiplocs (eg Wimbledon) then create multiple checksums to check against
                    #there is an edge case here if a route has multiple stops with an alternative tiploc
                    #however I haven't seen it occur in any routes yet
                    # if station['alternative_tiploc'] is not None:
                    #     print(new_route)
                    #     check_route[1] = check_route
                    #     check_route[1].append(station['alternative_tiploc'])

                    check_route[0].append(station['tiploc'])

                new_route_combined = '|'.join(new_route)
                check_route_1_combined = '|'.join(check_route[0])
                # if check_route[1] is not None:
                #     check_route_2_combined = '|'.join(check_route[1])

                if new_route_combined == check_route_1_combined:
                    route_match = True
                    break

            if route_match == False:
                print('Routes differ!')

                save_new_route(journey, orig_tiploc, dest_tiploc, toc_record)

        else:
            #new route, add route and stops to db
            save_new_route(journey, orig_tiploc, dest_tiploc, toc_record)

    return render(request, 'hello2.html')

def save_new_route(journey, orig_tiploc, dest_tiploc, toc_record):
    
            route = Route(orig = orig_tiploc, dest = dest_tiploc, toc_id = toc_record.id)
            route.save()

            orig_record = Station.objects.filter(Q(tiploc = orig_tiploc)| Q(alternative_tiploc = orig_tiploc)).get()
            dest_record = Station.objects.filter(Q(tiploc = dest_tiploc)| Q(alternative_tiploc = dest_tiploc)).get()

            orig = Stop(stop_number = 1, route_id = route.id, station_id = orig_record.id)
            orig.save()

            stop_no = 2

            for stop in journey:
                # print(stop.attrib)
                if 'IP' in stop.tag:
                    stop_tiploc = stop.attrib['tpl']

                    stop_record = Station.objects.filter(Q(tiploc = stop_tiploc)| Q(alternative_tiploc = stop_tiploc)).get()

                    Stop.objects.create(stop_number = stop_no, route_id = route.id, station_id = stop_record.id)

                    stop_no += 1

            dest = Stop(stop_number = stop_no, route_id = route.id, station_id = dest_record.id)
            dest.save()

            route.num_stops = stop_no
            route.save()