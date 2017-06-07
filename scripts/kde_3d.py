# -*- coding: utf-8 -*-
"""
Created on Thu May 19 18:10:43 2016

@author: anna
"""

import os
import numpy as np
from scipy import stats
import grass.script as gscript
from grass.script import array as garray
from statsmodels.nonparametric.kernel_density import KDEMultivariate


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


def kde(camera, points, gisrc, env):
    name = points
    if '@' in points:
        name, mapset = points.split('@')
    print name
    os.environ['GISRC'] = gisrc
    ascii = gscript.read_command('v.out.ascii', input=name, separator='|').strip()
    rescale_z = 1.0
    points = []
    for line in ascii.splitlines():
        x, y, z, c = line.split('|')
        points.append((float(x), float(y), float(z) * rescale_z))
    values = np.array(points).T
    # https://jakevdp.github.io/blog/2013/12/01/kernel-density-estimation/
    kde = stats.gaussian_kde(values, bw_method='silverman')
    kde.set_bandwidth(bw_method='silverman')

    kde2 = KDEMultivariate(values,
                           bw='cv_ml',
                           var_type='ccc')
    bw = kde2.bw
    bw_new = [(bw[0] + bw[1]) / 2., (bw[0] + bw[1]) / 2., bw[2]]
    kde2 = KDEMultivariate(values, bw=bw_new, var_type='ccc')

    ortho = gscript.read_command('g.list', type='raster', pattern='ortho_{}*'.format(camera.split('_')[-1])).strip().split('\n')[0]
    gscript.run_command('g.region', raster=ortho, zoom=ortho)
    res = 10
    res2 = res/2
    tbres = 0.5
    t, b = 22, 5
    gscript.run_command('g.region', flags='a', t=t * rescale_z, b=b * rescale_z,
                        tbres=tbres * rescale_z, res3=res, res=1)
    region = gscript.region(region3d=True)
    xi, yi, zi = np.mgrid[region['w'] + res2:region['e']-res2:complex(0, region['cols3']),
                          region['n']-res2:region['s'] + res2:complex(0, region['rows3']),
                          region['b'] + 0.5 * tbres * rescale_z:region['t'] - 0.5 * tbres * rescale_z:complex(0, (region['t'] - region['b']) / (tbres * rescale_z))]
    # change back to unscaled region
    gscript.run_command('g.region', flags='a', t=t, b=b, tbres=tbres, res3=res, res=1)
    coords = np.vstack([item.ravel() for item in [xi, yi, zi]])
    density = kde(coords)
    density = kde2.pdf(coords)
    
    density = density.reshape(xi.shape)
    n_points = gscript.vector_info_topo(name)['points']
    # times number of points to scale normalized result from scipy
    # times voxel volume, sum(map) ==  npoints
    days = float(gscript.read_command('db.select', sql="select count(distinct date) from {v}".format(v=name), flags='c').strip())
    # this line would mean number of people per grid cell
    #multiplication = n_points * (region['ewres3'] * region['nsres3'] * region['tbres']) / days
    # multiply by n_points to convert from normalized to density per unit area (1m2 and 1 h)
    multiplication = n_points
    # if rescaled z, need to rescale the values back
    multiplication *= rescale_z
    multiplication /= days  # per 1 day
    # for 10x10m and 1 h
    multiplication *= 100

    map3d = garray.array3d()
    for z in range(map3d.shape[0]):
        for y in range(map3d.shape[1]):
            for x in range(map3d.shape[2]):
                map3d[z, y, x] = multiplication * density[x, y, z]
    map3d.write(mapname="map3d_{}".format(name), overwrite=True)
    # export to VTK
    export_VTK_color(name, ortho, t, b)


def export_VTK_color(name, ortho, top, bottom):
    # the .999 is necessary for correct color breaks rendering in GRASS and paraview
    rules = ['5 blue', '8.999 blue', '8.999 116:197:25', '10.999 116:197:25', '10.999 yellow', '12.999 yellow',
             '12.999 orange', '16.999 orange', '16.999 red', '22 red']
    gscript.run_command('r3.mapcalc', exp="time_{name} = float(depth() - 1) * 0.5 + {b}".format(name=name, b=bottom), overwrite=True, quiet=True)
    gscript.write_command('r3.colors', map='time_{name}'.format(name=name), rules='-', stdin='\n'.join(rules), quiet=True)
    for c in 'rgb':
        gscript.run_command('r3.mapcalc', exp="time_{c}_{name} = {c}#time_{name}".format(c=c, name=name), overwrite=True, quiet=True)
    gscript.run_command('r3.out.vtk', input="map3d_{}".format(name), rgbmaps=['time_{c}_{name}'.format(c=c, name=name) for c in 'rgb'],
                        output='map3d_{}.vtk'.format(name), quiet=True, overwrite=True)

    # plane with ortho
    gscript.run_command('g.region', raster=ortho, zoom=ortho)
    gscript.mapcalc("map_{name} = {b}".format(name=name, b=bottom), quiet=True, overwrite=True)
    gscript.run_command('r.out.vtk', elevation="map_{}".format(name), rgbmaps=[ortho + '.' + c for c in ('red', 'green', 'blue')],
                        output='map_{}.vtk'.format(name), quiet=True, overwrite=True)
    # cleanup
    gscript.run_command('g.remove', type='raster_3d', flags='fe', pattern="time_[rgb]_*")


if __name__ == '__main__':
    # this should be run from XY location
    # finds all imagery groups with georeferencing info and transforms the points
    # and creates indicatrix
    groups = gscript.read_command('g.list', type='group').strip().splitlines()
    gisenv = gscript.gisenv()
    gisrc = os.environ['GISRC']
    for group in groups:
        path = os.path.join(gisenv['GISDBASE'], gisenv['LOCATION_NAME'], gisenv['MAPSET'], 'group', group)
        files = os.listdir(path)
        # if '8794' not in group:
        #     continue
        if 'TARGET' in files and 'POINTS' in files:
            # setup target environment and switch to it
            path_to_TARGET = os.path.join(path, 'TARGET')
            with open(path_to_TARGET, 'r') as f:
                target = f.readlines()
                target_location = target[0]
                target_mapset = target[1]
            target_gisrc, tenv = getEnvironment(gisenv['GISDBASE'], target_location, target_mapset)
            camera = group.strip('camera_').split('_')[0]
            people_maps = gscript.read_command('g.list', type='vector', pattern="*{group}*_people".format(group=group.strip('camera_')),
                                               mapset='.', env=tenv).strip().split('\n')
            for each in people_maps:
                kde(camera=camera, points=each, gisrc=target_gisrc, env=tenv)
            os.environ['GISRC'] = gisrc
            gscript.try_remove(target_gisrc)

    
