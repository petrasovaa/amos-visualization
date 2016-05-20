# -*- coding: utf-8 -*-
"""
Created on Thu May 19 18:10:43 2016

@author: anna
"""

import numpy as np
from scipy import stats
import grass.script as gscript
from grass.script import array as garray


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


def kde(points):
    name = points
    if '@' in points:
        name, mapset = points.split('@')
    ascii = gscript.read_command('v.out.ascii', input=each, separator='|').strip()
    points = []
    for line in ascii.splitlines():
        x, y, z, c = line.split('|')
        points.append((float(x), float(y), float(z)))
    values = np.array(points).T
    kde = stats.gaussian_kde(values)
    gscript.run_command('g.region',  raster='camera_{}'.format(name.split('_')[-1]),
                        zoom='camera_{}'.format(name.split('_')[-1]))
    res = 10
    res2 = res/2
    gscript.run_command('g.region', flags='a', t=1260, b=330, tbres=30, res3=res, res=1)
    region = gscript.region(region3d=True)
    xi, yi, zi = np.mgrid[region['w'] + res2:region['e']-res2:complex(0, region['cols3']),
                          region['n']-res2:region['s'] + res2:complex(0, region['rows3']),
                          345:1245:31j]

    coords = np.vstack([item.ravel() for item in [xi, yi, zi]])
    density = kde(coords)
    density = density.reshape(xi.shape)
    map3d = garray.array3d()
    for z in range(map3d.shape[0]):
        for y in range(map3d.shape[1]):
            for x in range(map3d.shape[2]):
                map3d[z, y, x] = 1e6 * density[x, y, z]
    map3d.write(mapname="map3d_{}".format(name.split('_')[-1]), overwrite=True)


if __name__ == '__main__':
    gscript.use_temp_region()
    vectors = gscript.list_grouped(type='vector', pattern="people_*")['PERMANENT']
    for each in vectors:
        print each
        kde(each)
        
