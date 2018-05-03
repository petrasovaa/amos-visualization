# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 21:10:59 2016

@author: Anna Petrasova
"""
import os
import sys
import copy
import numpy as np
from datetime import datetime
import grass.script as gscript
from grass.exceptions import CalledModuleError
from collections import defaultdict
from PIL import Image


def is_weekday(dt):
    return dt.isoweekday() in (1, 2, 3, 4, 5)

def is_sunday(dt):
    return dt.isoweekday() == 7

def is_saturday(dt):
    return dt.isoweekday() == 6


def get_categories(vector):
    hist = gscript.read_command('v.category', input=vector, layer=2, option='print').strip().splitlines()             
    hist = [int(each) for each in hist]
    cats, counts = np.unique(hist, return_counts=True)
    res = dict(zip(cats, counts))
    reversed_dict = defaultdict(list)
    for key, value in res.iteritems():
        reversed_dict[value].append(key)
    return dict(reversed_dict)


def extract_clusters(vectors, cluster, time_condition, output):
    gscript.run_command('v.edit', flags='b', overwrite=True, map=output, tool='create')
    tmp_vec = 'tmp_vec'
    for vector in vectors:
#        cluster_points_points_9106_2015_people__05_09_15__16_13_00
        name, date, time = vector.split('__')
        m, d, y = date.split('_')
        h, mi, s = time.split('_')
        dt = datetime(int(y), int(m), int(d), int(h), int(mi))
        if time_condition(dt):
            cat_dict = get_categories(vector)
            cats = []
            # individuals have cat 0, need to treat them separately
            if cluster[0] == 1:
                cats = [0]
            else:
                for i in cluster:
                    if i in cat_dict:
                        cats += cat_dict[i]
                if 0 in cats:
                    cats.remove(0)
            gscript.run_command('v.extract', input=vector, layer='2', cats=','.join([str(i) for i in cats]), flags='t',
                                output=tmp_vec, overwrite=True, quiet=True)
            gscript.run_command('v.patch', flags='nab', input=tmp_vec, output=output, overwrite=True, quiet=True)

    gscript.run_command('v.category', input=output, layer='2,1', option='chlayer', output=tmp_vec, overwrite=True, quiet=True)
    gscript.run_command('v.build', map=tmp_vec, quiet=True)
    gscript.run_command('g.rename', vector=[tmp_vec, output], overwrite=True, quiet=True)


def create_heatmaps(vectors, background_ortho, radius, width, height):
    os.environ['GRASS_FONT'] = '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'
    names = []
    for vector in vectors:
        gscript.run_command('v.kernel', input=vector, output=vector + '_kernel', radius=radius, overwrite=True, quiet=True)
        names.append(vector + '_kernel')
    gscript.write_command('r.colors', map=names, rules='-', stdin='0% white\n10% yellow\n40% red\n100% magenta')
    maxdens = float(gscript.parse_command('r.univar', map=names, flags='g')['max'])
    for vector in vectors:
        gscript.run_command('d.mon', start='cairo', output='foreground_' + vector + '_kernel' + '.png',
                            width=width, height=height, overwrite=True)
        gscript.run_command('d.rast', map=vector + '_kernel')
        gscript.run_command('d.mon', stop='cairo')
        # background
        gscript.run_command('d.mon', start='cairo', output='background_' + vector + '_kernel' + '.png',
                            width=width, height=height, overwrite=True)
        gscript.run_command('d.rast', map=background_ortho)
        gscript.run_command('d.legend', flags='t', raster=vector + '_kernel', label_step=0.5, digits=1, range=[0, maxdens], at=[3,40,3,6], color='white')
        gscript.run_command('d.mon', stop='cairo')

        # put together with transparency
        foreground = Image.open('foreground_' + vector + '_kernel' + '.png')
        background = Image.open('background_' + vector + '_kernel' + '.png')
        foreground = foreground.convert("RGBA")
        datas = foreground.getdata()
        newData = []
        for item in datas:
            intens = item[0] + item[1] + item[2]
            newData.append((item[0], item[1], item[2], min(765-intens, 200)))
        foreground.putdata(newData)
        background.paste(foreground, (0, 0), foreground)
        background.save('heatmap_{v}.png'.format(v=vector), "PNG")
        gscript.try_remove('foreground_' + vector + '_kernel' + '.png')
        gscript.try_remove('background_' + vector + '_kernel' + '.png')


if __name__ == '__main__':
    for vector in sys.argv[1:]:
        vectors = gscript.list_grouped(type='vector', pattern="cluster_{}*".format(vector))[gscript.gisenv()['MAPSET']]
        #### don't use cluster 1  (individuals) with couples, ...

        extract_clusters(vectors, [1], is_weekday, 'cluster_individuals_weekday')
        extract_clusters(vectors, [2], is_weekday, 'cluster_couples_weekday')
        extract_clusters(vectors, [3,4,5], is_weekday, 'cluster_smallgroups_weekday')
        extract_clusters(vectors, range(6,20), is_weekday, 'cluster_biggroups_weekday')
        
        extract_clusters(vectors, [1], is_sunday, 'cluster_individuals_sunday')
        extract_clusters(vectors, [2], is_sunday, 'cluster_couples_sunday')
        extract_clusters(vectors, [3,4,5], is_sunday, 'cluster_smallgroups_sunday')
        extract_clusters(vectors, range(6,20), is_sunday, 'cluster_biggroups_sunday')

        vectors = gscript.list_grouped(type='vector', pattern="cluster_*_weekday".format(vector))[gscript.gisenv()['MAPSET']]
        vectors += gscript.list_grouped(type='vector', pattern="cluster_*_sunday".format(vector))[gscript.gisenv()['MAPSET']]
        create_heatmaps(vectors, 'ortho_9106', 5, 660, 670)

