# -*- coding: utf-8 -*-
"""
This script downloads data from online database, filters outlines to remove duplicates,
and outputs data into CSV.

@author: anna
"""

import os
import sys
import requests
import json
from collections import namedtuple
import urllib
import datetime
import collections
try:
    from pytz import timezone, utc
    from timezonefinder import TimezoneFinder
except ImportError:
    print 'Missing timezonefinder or pytz packages'
import socket
socket.setdefaulttimeout(10)


Bbox = namedtuple("Bbox", "x y w h worker")
Camera = namedtuple("Camera", "id w h lat lon")


missing_latlon = {8794: (47.177930, 8.516177),
                  5599: (-45.873625, 170.503706),
                  14519: (59.3328, 18.0645),
                  9266: (50.55, 9.667)}


def get_cameras(hitId):
    def get_cameras_(cameras, url):
        key, num = url.split('&')[-1].split('=')
        fname = 'hitId_{}_page_{}.json'.format(hitId, num)
        if not os.path.isfile(fname):
            resp = requests.get(url=url)
            data = resp.json()
            with open(fname, 'w') as f:
                json.dump(data, f)
        else:
            with open(fname, 'r') as f:
                data = json.load(f)
        for each in data['results']:
            cameras.append(each['submission']['image']['webcam'].strip('/').split('/')[-1])

        if data['next']:
            get_cameras_(cameras, data['next'])

    cameras = []
    url = 'http://amosweb.cse.wustl.edu/REST/outlines/?submission__hitId={}&page=1'.format(hitId)
    get_cameras_(cameras, url)
    counter = collections.Counter(cameras)
    return counter


def process_camera(camera):
    fname = 'camera_params_{}.json'.format(camera)
    if not os.path.isfile(fname):
        url = 'http://amosweb.cse.wustl.edu/REST/webcams/{}'.format(camera)
        resp = requests.get(url=url)
        data = resp.json()
        with open(fname, 'w') as f:
            json.dump(data, f)
    else:
        with open(fname, 'r') as f:
            data = json.load(f)
    # add latlon if theyare not defined and we no them by manula search
    lat, lon = 50, 0  # default
    if not data['latitude']:
        if data['id'] in missing_latlon.keys():
            lat = missing_latlon[data['id']][0]
            lon = missing_latlon[data['id']][1]
    else:
        lat = data['latitude']
        lon = data['longitude']
    c = Camera(data['id'], data['last_width'], data['last_height'], lat, lon)

    # download image
    cam_image = 'camera_{}.jpg'.format(camera)
    if not os.path.isfile(cam_image):
        try:
            urllib.urlretrieve(data['url'], cam_image)
        except IOError:
            print data['url'] + " doesn't work"
    return c


def download_json(camera):
    fname = 'camera_{}.json'.format(camera.id)
    if not os.path.isfile(fname):
        url = 'http://amosweb.cse.wustl.edu/REST/outlines'
        page = 1
        resp = requests.get(url=url, params={'submission__image__webcam': camera.id, 'page': page})
        with open(fname, 'w') as f:
            f.write('[')
            while True:
                data = resp.json()
                counts = len(data['results'])
                i = 0
                for each in data['results']:
                    f.write(json.dumps(each))
                    if i < counts - 1:
                        f.write(',\n')
                    i += 1
                page += 1
                if resp.json()['next']:
                    resp = requests.get(url=url, params={'submission__image__webcam': camera.id, 'page': page})
                    f.write(',\n')
                else:
                    break
            f.write(']')

    with open(fname, 'r') as f:
        data = json.load(f)
    return data


def overlap(bboxA, bboxB):
    si = max(0, min(bboxA.x + bboxA.w, bboxB.x + bboxB.w) - max(bboxA.x, bboxB.x)) * \
        max(0, min(bboxA.y + bboxA.h, bboxB.y + bboxB.h) - max(bboxA.y, bboxB.y))
    sA = bboxA.w * bboxA.h
    sB = bboxB.w * bboxB.h
    return float(si) / min(sA, sB)


def get_bbox_point(bbox):
    # middle of x, bottom of bbox for georeferencing
    return (bbox.x + bbox.w / 2, bbox.y + bbox.h)


def get_bboxes_point(bbox_list):
    x = 0
    y = 0
    for bbox in bbox_list:
        xb, yb = get_bbox_point(bbox)
        x += xb
        y += yb
    x /= len(bbox_list)
    y /= len(bbox_list)
    return (x, y)


def resolve_duplicates(duplicates):
    threshold = 0.25
    records = []
    removed = []
    for a, outlineA in enumerate(duplicates):
        if outlineA in removed:
            continue
        overlapping = [outlineA, ]
        for outlineB in duplicates[a + 1:]:
            if outlineB in removed:
                continue
            # gather duplicates by overap and workers
            if overlap(outlineA, outlineB) >= threshold and outlineA.worker != outlineB.worker:
                overlapping.append(outlineB)
        if len(overlapping) > 1:
            x, y = get_bboxes_point(overlapping)
            records.append((x, y))
            removed.extend(overlapping)
        else:
            records.append(get_bbox_point(outlineA))

    return records


def local_time(dt, zone):
    return dt.astimezone(timezone(zone))


def filterhits(camera, data):
    # timezones
    tf = TimezoneFinder()
    zone = tf.timezone_at(lng=camera.lon, lat=camera.lat)

    timestamps = []
    for record in data:
        timestamps.append(record['submission']['image']['timestamp'])

    instance = {}
    for timestamp in set(timestamps):
        instance[timestamp] = {'vehicles': set(), 'bikes': set(), 'people': set()}
        for record in data:
            if record['submission']['image']['timestamp'] == timestamp:
                worker = record['submission']['workerId']
                bbox = Bbox(record['x1'], record['y1'], record['x2'], record['y2'], worker)
                # some have w = 0 or h = 0
                if bbox.w * bbox.h > 0:
                    instance[timestamp][record['type']].add(bbox)

    with open('camera_{}_points.csv'.format(camera.id), 'w') as f:
        f.write('year,month,day,hour,minute,type,count,x,y,url,url2,y,m,d,h,mi,camw,camh\n')
        for timestamp in sorted(instance.keys()):
            date, time = timestamp.split('T')
            y, m, d = date.split('-')
            h, mi, s = time.split(':')
            ts = timestamp.replace(':', '').replace('T', '_').replace('-', '')
            dt = datetime.datetime(year=int(y), month=int(m), day=int(d), hour=int(h), minute=int(mi), second=int(s), tzinfo=utc)
            lt = local_time(dt, zone)
            url = 'http://amos.cse.wustl.edu/mturk/reviewOutlines/{}/{}'.format(camera.id, ts)
            url2 = 'http://amos.cse.wustl.edu/image/{}/{}.jpg'.format(camera.id, ts)
            for htype in instance[timestamp].keys():
                records = resolve_duplicates(list(instance[timestamp][htype]))
                for xx, yy in records:
                    f.write('{yl},{ml},{dl},{hl},{mil},{tp},{cnt},{xx},{yy},{url},{url2},{y},{m},{d},{h},{mi},{camw},{camh}\n'
                            .format(yl=lt.year, ml=lt.month, dl=lt.day, hl=lt.hour, mil=lt.minute, y=y, m=m,
                                    d=d, h=h, mi=mi, tp=htype, cnt=len(records), xx=xx, yy=yy, url=url, url2=url2,
                                    camw=camera.w, camh=camera.h))


if __name__ == '__main__':
    for each in ('stableBEOutlines', 'stableBEchangeValidation', 'sfmRectangles', 'plazas'):
        cam = get_cameras(each)
        print each
        for camid in cam.keys():
            print "{}: {}".format(camid, cam[camid] )

#    print all_cams
    
    for each_camera in sys.argv[1:]:
        print each_camera
        camera_id = each_camera
        camera = process_camera(camera_id)
        data = download_json(camera)
        filterhits(camera, data)

