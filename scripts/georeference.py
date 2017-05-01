# -*- coding: utf-8 -*-
"""
Created on Sun May 22 19:16:57 2016

@author: anna
"""
import os
# import copy
import numpy as np
from numpy.linalg import inv

from skimage import transform as tf
from skimage import io

import grass.script as gscript
from grass.script import array as garray


def getEnvironment(gisdbase, location, mapset):
    """Creates environment to be passed in run_command for example.
    Returns tuple with temporary file path and the environment. The user
    of this function is responsile for deleting the file."""
    tmp_gisrc_file = gscript.tempfile()
    with open(tmp_gisrc_file, 'w') as f:
        f.write('MAPSET: {mapset}\n'.format(mapset=mapset))
        f.write('GISDBASE: {g}\n'.format(g=gisdbase))
        f.write('LOCATION_NAME: {l}\n'.format(l=location))
        f.write('GUI: text\n')
    env = os.environ.copy()
    env['GISRC'] = tmp_gisrc_file
    return tmp_gisrc_file, env


def indicatrix(raster, size):
    env = os.environ.copy()
    env['GRASS_OVERWRITE'] = '1'
    env['GRASS_VERBOSE'] = '0'
    env['GRASS_REGION'] = gscript.region_env(raster=raster)
    info = gscript.raster_info(raster)
    number = [3, 5]
    ew = info['east'] - info['west']
    ns = info['north'] - info['south']
    ew_step = ew / float(number[0] + 1)
    ns_step = ns / float(number[1] + 1)
    name = raster + '_indicatrix'
    circle_tmp = 'tmp_circle'
    circle_tmp2 = 'tmp_circle2'
    gscript.mapcalc('{} = null()'.format(circle_tmp2), overwrite=True)
    for i in range(number[0]):
        for j in range(number[1] - 1):
            gscript.run_command('r.circle', output=circle_tmp, min=size, max=size + 1, flags='b',
                                coordinates=[info['west'] + (i + 1) * ew_step, info['south'] + (j + 1) * ns_step],
                                env=env)
            gscript.run_command('r.patch', input=[circle_tmp, circle_tmp2], output=name, env=env)
            gscript.run_command('g.copy', raster=[name, circle_tmp2], env=env)

    gscript.run_command('r.to.vect', input=name, output=name, type='line', flags='vt', env=env)
    gscript.run_command('g.remove', type='raster', flags='f', name=[circle_tmp, circle_tmp2], env=env)
    return name


def main(image, gisenv, gisrc):
    os.environ['GISRC'] = gisrc
    path = os.path.join(gisenv['GISDBASE'], gisenv['LOCATION_NAME'], gisenv['MAPSET'], 'group', image)
    path_to_points = os.path.join(path, 'POINTS')

    # setup target environment and switch to it
    path_to_TARGET = os.path.join(path, 'TARGET')
    with open(path_to_TARGET, 'r') as f:
        target = f.readlines()
        target_location = target[0]
        target_mapset = target[1]
    target_gisrc, tenv = getEnvironment(gisenv['GISDBASE'], target_location, target_mapset)

    im = io.imread('{}.jpg'.format(image))
    dst = []
    src = []
    with open(path_to_points) as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            dstx, dsty, srcx, srcy, ok = line.split()
            if int(ok):
                dst.append((float(dstx), float(dsty)))
                src.append((float(srcx), float(srcy)))
    dst = np.array(dst)
    src = np.array(src)
    # src2 = copy.copy(src)
    dst[:, 1] = im.shape[0] - dst[:, 1]

    centerx, centery = np.min(src[:, 0]), np.min(src[:, 1])
    src[:, 0] -= centerx
    src[:, 1] -= centery
    revers = 400
    src[:, 1] = revers - src[:, 1]

    tform3 = tf.ProjectiveTransform()
    tform3.estimate(src, dst)
    warped = tf.warp(im, tform3)

    os.environ['GISRC'] = target_gisrc
    gscript.run_command('g.region', w=centerx, e=centerx + im.shape[1],
                        n=centery + revers, s=centery - im.shape[0] + revers, res=1)

    name = 'rectified_{}'.format(image)
    for num, color in zip([0, 1, 2], 'rgb'):
        rectified = garray.array()
        for y in range(rectified.shape[0]):
            for x in range(rectified.shape[1]):
                rectified[y, x] = round(255 * warped[y, x, num])
        rectified.write(mapname=name + '_' + color, overwrite=True)
    gscript.run_command('r.colors', map=[name + '_r', name + '_g', name + '_b'], color='grey')
    gscript.run_command('r.composite', red=name + '_r', green=name + '_g', blue=name + '_b',
                        output=name, overwrite=True)
    gscript.run_command('g.remove', type='raster', pattern=name + "_*", flags='f')

    os.environ['GISRC'] = gisrc
    # indicatrix
    print indicatrix(raster=image, size=5)

    # rectify points
    H = inv(tform3.params)
    name = image.strip('camera_')
    os.environ['GISRC'] = gisrc
    vectors = gscript.read_command('g.list', type='vector', pattern="*{}*".format(name),
                                   exclude='*indicatrix').strip().splitlines()
    for vector in vectors:
        os.environ['GISRC'] = gisrc
        points = gscript.read_command('v.out.ascii', input=vector, columns='*').strip()
        new = []
        for record in points.splitlines():
            point = record.split('|')
            xx, yy = float(point[0]), float(point[1])
            yy = im.shape[0] - yy
            Z = xx * H[2, 0] + yy * H[2, 1] + H[2, 2]
            X = (xx * H[0, 0] + yy * H[0, 1] + H[0, 2]) / Z
            Y = (xx * H[1, 0] + yy * H[1, 1] + H[1, 2]) / Z
            X += centerx
            Y = revers - Y + centery
            # Y =  -Y + centery
            new.append([point[3], X, Y, point[2]])
            new[-1].extend(point[4:])
            new[-1] = '|'.join([str(each) for each in new[-1]])
        os.environ['GISRC'] = target_gisrc

        gscript.write_command('v.in.ascii', input='-', flags='z',
                              output='points_{}'.format(vector), overwrite=True, stdin='\n'.join(new),
                              columns="cat integer,x double precision,y double precision,height double precision,"
                                      "date varchar(50),time varchar(50),hour integer,"
                                      "minutes integer,url varchar(500),url2 varchar(500)",
                              x=2, y=3, z=4, cat=1)

    os.environ['GISRC'] = gisrc
    vectors = gscript.read_command('g.list', type='vector', pattern="*{}*indicatrix".format(name)).strip().splitlines()

    for vector in vectors:
        os.environ['GISRC'] = gisrc
        lines = gscript.read_command('v.out.ascii', input=vector, format='standard').strip()
        new = []
        for record in lines.splitlines():
            first = record.strip().split()[0].strip()
            try:
                float(first)
            except ValueError:
                new.append(record)
                continue
            if first == '1':
                new.append(record)
                continue
            xx, yy = record.strip().split()
            xx, yy = float(xx), float(yy)
            yy = im.shape[0] - yy
            Z = xx * H[2, 0] + yy * H[2, 1] + H[2, 2]
            X = (xx * H[0, 0] + yy * H[0, 1] + H[0, 2]) / Z
            Y = (xx * H[1, 0] + yy * H[1, 1] + H[1, 2]) / Z
            X += centerx
            Y = revers - Y + centery
            # Y =  -Y + centery
            new.append('{} {}'.format(X, Y))
        os.environ['GISRC'] = target_gisrc
        gscript.write_command('v.in.ascii', input='-', output=vector, format='standard', overwrite=True,
                              stdin='\n'.join(new))
        gscript.run_command('v.generalize', overwrite=True, input=vector, type='line',
                            output=vector + 'tmp', method='snakes', threshold=10)
        gscript.run_command('g.rename', vector=[vector + 'tmp', vector], overwrite=True)

    gscript.try_remove(target_gisrc)
    return


if __name__ == '__main__':
    # this should be run from XY location
    # finds all imagery groups with georeferensing info and transforms the points
    # and creates indicatrix
    groups = gscript.read_command('g.list', type='group').strip().splitlines()
    gisenv = gscript.gisenv()
    gisrc = os.environ['GISRC']
    for group in groups:
        files = os.listdir(os.path.join(gisenv['GISDBASE'], gisenv['LOCATION_NAME'], gisenv['MAPSET'], 'group', group))
        # if '8794' not in group:
        #     continue
        if 'POINTS' in files:
            main(group, gisenv, gisrc)
