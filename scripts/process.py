# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 21:10:59 2016

@author: anna
"""

import datetime
import grass.script as gscript
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point


dim = {10823: '640x480',
       10838: '800x600',
       1217: '640x480',
       1239: '480x360',
       1290: '640x480',
       1323: '640x480',
       14252: '320x240',
       14330: '768x576',
       1637: '480x360',
       17603: '800x450',
       18921: '640x480',
       23528: '640x480',
       23965: '640x480',
       23966: '640x480',
       23970: '640x480',
       3548: '704x576',
       3760: '600x456',
       4663: '640x480',
       4731: '640x480',
       5363: '640x480',
       5751: '1024x768',
       9706: '800x600',
       9955: '640x480'}

timeoffset = \
      {10823: (2, 0),
       10838: (2, 0),
       1217: (2, 0),
       1239:  (2, 0),
       1290: (2, 0),
       1323: (3, 0),
       14252: (2, 0),
       14330: (2, 0),
       1637: (2, 0),
       17603: (-6, 0),
       18921: (3, 0),
       23528: (2, 0),
       23965: (2, 0),
       23966: (2, 0),
       23970: (-5, 0),
       3548: (3, 0),
       3760: (9, 30),
       4663: (2, 0),
       4731: (2, 0),
       5363: (2, 0),
       5751: (2, 0),
       9706: (1, 0),  # germany, probably incorrect
       9955: (2, 0)}


def main(filename, out):
    lines = []
    data = {}
    with open(filename, 'r') as f:
        lines = f.readlines()
    urls = []
    for line in lines[1:]:
        url, x, y, w, h = line.strip().split(',')
        camera = url.split('/')[4]
        date, time = url.split('/')[5].strip('.jpg').split('_')
        year, month, day = int(date[:4]), int(date[4:6]), int(date[6:])
        hour, minut, sec = int(time[:2]), int(time[2:4]), int(time[4:])
        offset = timeoffset[int(camera)]
        minut += offset[1]
        if minut > 60:
            minut -= 60
            hour += 1
        hour += offset[0]
        if hour < 0:
            hour += + 24
        if hour > 24:
            hour -= 24

        if camera not in data:
            data[camera] = []
            urls.append((url, camera))
        # middle point
        #data[camera].append(((year, month, day, hour, minut, sec), (float(x) + float(w) / 2., float(y) - float(h) / 2.)))
        # bottom point
        data[camera].append(((year, month, day, hour, minut, sec), (float(x) + float(w) / 2., float(y))))

    cols = [(u'cat', 'INTEGER PRIMARY KEY'),
            (u'date', 'TEXT'),
            (u'time', 'TEXT'),
            ('hour', 'INTEGER'),
            ('minutes', 'INTEGER')]

    for each in data.keys():
        # middle point
        name = out + '_' + each
        # bottom point
        name = out + '_bottom_' + each
        with VectorTopo(name, mode='w', tab_cols=cols[:], with_z=True) as points:
            for time, coor in data[each]:
                pw, ph = dim[int(each)].split('x')
                t = datetime.datetime(*time)
                z = t.hour * 60 + t.minute + t.second/60.
                p = Point(coor[0] / 2., int(ph) - coor[1] / 2., z)
                p2 = Point(coor[0] / 2., int(ph) - coor[1] / 2., z)
                dt = datetime.datetime(*time)
                points.write(p, (dt.strftime("%x"), dt.strftime("%X"), t.hour, t.minute))
                # save the changes to the database
            points.table.conn.commit()

#    for url, cam in urls:
#        print 'wget -O camera_' + cam + '.jpg ' + url 


if __name__ == '__main__':
    f = '/home/anna/Documents/Projects/Hipp_STC/Plaza.csv'
    out = 'people'
    main(f, out)

