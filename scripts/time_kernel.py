# -*- coding: utf-8 -*-
"""
Created on Mon May 16 13:34:17 2016

@author: anna
"""

import grass.script as gscript


def time_kernel(points):
    name = points
    if '@' in points:
        name, mapset = points.split('@')

    info = gscript.parse_command('v.univar', flags='g', map=points, column='hour')
    minim, maxim = int(info['min']), int(info['max'])
    i = minim
    size = 3
    print minim, maxim
    while i + size <= maxim:
        gscript.run_command('v.extract', input=points, where="hour >= {} and hour <= {}".format(i, i + size - 1),
                            output=name + "_tmp", overwrite=True, quiet=True)
        gscript.run_command('v.kernel', input=name + "_tmp", output=name + '_kernel_' + str(i),
                            radius=70, overwrite=True, quiet=True)
        i += 1



if __name__ == '__main__':
    gscript.use_temp_region()
    vectors = gscript.list_grouped(type='vector', pattern="people_*")['PERMANENT']
    for each in vectors:
        gscript.run_command('g.region', raster='camera_' + each.split('_')[-1], zoom='camera_' + each.split('_')[-1])
        time_kernel(each)
    maps = gscript.list_grouped(type='raster', pattern="*kernel*")['kernel']
    gscript.write_command('r.colors', map=maps, rules='-', stdin='0% white\n20% yellow\n50% red\n100% magenta')
