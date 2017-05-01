# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 21:10:59 2016

@author: anna
"""
import os
import sys
import glob
import datetime
import grass.script as gscript
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point

CSV_PATH = '/home/anna/Documents/Projects/Hipp_STC/filtering/'


cols = [(u'cat', 'INTEGER PRIMARY KEY'),
        (u'date', 'TEXT'),
        (u'time', 'TEXT'),
        ('hour', 'INTEGER'),
        ('minutes', 'INTEGER'),
        ('url', 'VARCHAR(500)'),
        ('url2', 'VARCHAR(500)')]


def import_points(camera, output):
    data = []
    years = set()
    types = set()
    with open(os.path.join(CSV_PATH, 'camera_{}_points.csv'.format(camera))) as f:
        lines = f.readlines()
    for line in lines[1:]:
        year, month, day, hour, minute, type, count, x, y, url, url2, yr, m, d, h, mi, camw,	camh = line.strip().split(',')
        data.append(((int(year), int(month), int(day), int(hour), int(minute)), type, count, url, url2, (float(x), float(y))))
        years.add(int(year))
        types.add(type)

    for year in years:
        for typ in types:
            cat = 0
            name = '{}_{}_{}_{}'.format(output, camera, year, typ)
            with VectorTopo(name, mode='w', tab_cols=cols[:], with_z=True, overwrite=True) as points:
                for time, type, count, url, url2, coor in data:
                    if time[0] != year or type != typ:
                        continue
                    cat += 1
                    z = time[3] + time[4] / 60.
                    p = Point(coor[0], int(camh) - coor[1], z)
                    dt = datetime.datetime(*time)
                    points.write(p, cat=cat, attrs=(dt.strftime("%x"), dt.strftime("%X"), dt.hour, dt.minute, url, url2))
                points.table.conn.commit()


def import_camera(camera, output):
    single = os.path.join(CSV_PATH, 'camera_{}.jpg'.format(camera))
    multiple = glob.glob(os.path.join(CSV_PATH, 'camera_{}_*.jpg'.format(camera)))
    if not multiple:
        gscript.run_command('r.in.gdal', input=single, output='camera_{}'.format(camera), overwrite=True)
        gscript.run_command('g.region', raster='camera_{}.red'.format(camera))
        gscript.run_command('r.composite', red='camera_{}.red'.format(camera),
                            green='camera_{}.green'.format(camera), blue='camera_{}.blue'.format(camera),
                            output='camera_{}'.format(camera), overwrite=True)
        gscript.run_command('i.group', group='camera_{}'.format(camera), input='camera_{}'.format(camera))
    else:
        for each in multiple:
            year = os.path.basename(each).split('.')[0].split('_')[-1]
            gscript.run_command('r.in.gdal', input=each, output='camera_{}_{}'.format(camera, year), overwrite=True)
            gscript.run_command('g.region', raster='camera_{}_{}.red'.format(camera, year))
            gscript.run_command('r.composite', red='camera_{}_{}.red'.format(camera, year),
                                green='camera_{}_{}.green'.format(camera, year), blue='camera_{}_{}.blue'.format(camera, year),
                                output='camera_{}_{}'.format(camera, year), overwrite=True)
            gscript.run_command('i.group', group='camera_{}_{}'.format(camera, year), input='camera_{}_{}'.format(camera, year))


if __name__ == '__main__':
    for each_camera in sys.argv[1:]:
        import_points(each_camera, 'points')
        import_camera(each_camera, 'camera')
