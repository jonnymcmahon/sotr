from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import boto3
import datetime
import gzip
import os
import xml.etree.ElementTree as ET
import json
from .models import Station, Journey

# Create your views here.

def download_file(request):

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

        print(journey[0].attrib['tpl'], journey[num_stops].attrib['tpl'], journey.attrib['toc'])

        #check if station exists in stations table TODO: find updated list of TIPLOCs for stations table (current is from 2016)
        orig = Station.objects.filter(tiploc = journey[0].attrib['tpl'])
        dest = Station.objects.filter(tiploc = journey[num_stops].attrib['tpl'])

        if not orig or not dest: continue
        else:
            orig = Station.objects.filter(tiploc = journey[0].attrib['tpl']).get()
            dest = Station.objects.filter(tiploc = journey[num_stops].attrib['tpl']).get()

        #unsure if bug in data? sometimes journey has no ptd / pta, so use wta / wtd instead
        depart = journey[0].attrib['ptd'] if ('ptd' in journey.attrib) else journey[0].attrib['wtd']
        arrive = journey[num_stops].attrib['pta'] if ('pta' in journey.attrib) else journey[num_stops].attrib['wta']

        obj, created = Journey.objects.update_or_create(
            date = journey.attrib['ssd'],
            origin_id = orig.id,
            destination_id = dest.id,
            departureTime = depart,
            arrivalTime = arrive,
            uid = journey.attrib['uid']
            )   

    return render(request, 'hello2.html')



def read_stations_list(request):

    with open('/django/timetable/storage/stations.json', 'r') as f:
        stations = json.load(f)

    for station in stations:
        obj, created = Station.objects.update_or_create(
            name = station['name'],
            crs = station['crs'],
            tiploc = station['tiploc']
        )

    return render(request, 'hello2.html')