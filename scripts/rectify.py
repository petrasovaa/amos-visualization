# -*- coding: utf-8 -*-
"""
Created on Sun May 22 19:16:57 2016

@author: anna
"""
import os
import copy
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


def main(camera):
    im = io.imread('pictures/camera_{}.jpg'.format(camera))
    # read POINTS file
    path_to_points = '/home/anna/grassdata/Hipp_STC/PERMANENT/group/camera_{}_/POINTS'.format(camera)
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
    src2 = copy.copy(src)
    dst[:, 1] = im.shape[0] - dst[:, 1]

    centerx, centery = np.min(src[:, 0]), np.min(src[:, 1])
    src[:, 0] -= centerx
    src[:, 1] -= centery
    revers = 200
    src[:, 1] = revers - src[:, 1]

    tform3 = tf.ProjectiveTransform()
    tform3.estimate(src, dst)
    warped = tf.warp(im, tform3)

    gscript.run_command('g.region', w=centerx, e=centerx + im.shape[1],
                        n=centery + revers, s=centery - im.shape[0] + revers, res=1)

    name = 'rectified_{}'.format(camera)
    for num, color in zip([0, 1, 2], 'rgb'):
        rectified = garray.array()
        for y in range(rectified.shape[0]):
            for x in range(rectified.shape[1]):
                rectified[y, x] = round(255 * warped[y, x, num])
        rectified.write(mapname=name + '_' + color, overwrite=True)
    gscript.run_command('r.colors', map=[name + '_r', name + '_g', name + '_b'], color='grey')
    gscript.run_command('r.composite', red=name + '_r', green=name + '_g', blue=name + '_b',
                        output=name, overwrite=True)
    gscript.run_command('g.remove', type='raster', pattern=name + "_", flags='f')
    # rectify points
    tmp_gisrc_file, env = getEnvironment(gisdbase=gscript.gisenv()['GISDBASE'], location='Hipp_STC', mapset='PERMANENT')
    H = inv(tform3.params)
    new = []
    points = gscript.read_command('v.out.ascii', input='people_bottom_{}'.format(camera),
                                  env=env, columns='*').strip()
    gscript.try_remove(tmp_gisrc_file)
    for record in points.splitlines():
        point = record.split('|')
        print point
        xx, yy = float(point[0]), float(point[1])
        yy = im.shape[0] - yy
        Z = xx * H[2, 0] + yy * H[2, 1] + H[2, 2]
        X = (xx * H[0, 0] + yy * H[0, 1] + H[0, 2]) / Z
        Y = (xx * H[1, 0] + yy * H[1, 1] + H[1, 2]) / Z
        X += centerx
        Y = revers - Y + centery
        #Y =  -Y + centery
        new.append([X, Y])
        new[-1].extend(point[2:])
        new[-1] = '|'.join([str(each) for each in new[-1]])
    gscript.write_command('v.in.ascii', input='-', flags='z',
                          output='rectified_points_{}'.format(camera), overwrite=True,
                          stdin='\n'.join(new),
                          columns="x double precision,y double precision,height double precision,cat integer,date varchar(50),time varchar(50),hour integer,minutes integer" ,
                          x=1, y=2, z=3, cat=4)


if __name__ == '__main__':
    camera = 1217
    main(camera)
