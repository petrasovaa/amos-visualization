# -*- coding: utf-8 -*-
"""
Created on Mon May 16 13:34:17 2016

@author: anna
"""
from PIL import Image
from subprocess import call
import grass.script as gscript


def time_kernel(points):
    name = points
    if '@' in points:
        name, mapset = points.split('@')

    info = gscript.parse_command('v.univar', flags='g', map=points, column='hour')
    minim, maxim = int(info['min']), int(info['max'])
    i = minim
    size = 1
    while i + size <= maxim:
        gscript.run_command('v.extract', input=points, where="hour >= {} and hour <= {}".format(i, i + size - 1),
                            output=name + "_tmp", overwrite=True, quiet=True)
        gscript.run_command('v.kernel', input=name + "_tmp", output=name + '_kernel_' + str(i),
                            radius=70, overwrite=True, quiet=True)
        gscript.run_command('r.timestamp', map=name + '_kernel_' + str(i), date='01 jan 2000 {}:00:00'.format(i + int(size / 2)))
        i += 1


def render_juxtaposed(camera):
    reg = gscript.region()
    maps = gscript.natural_sort(gscript.list_grouped(type='raster', pattern="people_{}_kernel_*".format(camera))['kernel'])
    width = len(maps) * reg['cols']
    height = 1 * reg['rows']
    step = 100. / len(maps)
    gscript.run_command('d.mon', start='cairo', output='foreground_{}.png'.format(camera),
                        width=width, height=height, overwrite=True)
    gscript.run_command('d.frame', flags='e')
    i = 0
    for map in maps:
        gscript.run_command('d.frame', flags='c', frame='frame_{}'.format(i),
                            at='{},{},{},{}'.format(0, 100, i * step, (i + 1) * step,
                                                    ))
        gscript.run_command('d.rast', map=map)
        i += 1
    gscript.run_command('d.mon', stop='cairo')
    # background
    gscript.run_command('d.mon', start='cairo', output='background_{}.png'.format(camera),
                        width=width, height=height, overwrite=True)
    gscript.run_command('d.frame', flags='e')
    i = 0
    for map in maps:
        gscript.run_command('d.frame', flags='c', frame='frame_{}'.format(i),
                            at='{},{},{},{}'.format(0, 100, i * step, (i + 1) * step,
                                                    ))
        gscript.run_command('d.rast', map='camera_{}'.format(camera))
        h, minut, sec = gscript.read_command('r.timestamp', map=map).split()[-1].split(':')
        gscript.run_command('d.text', align='lc', linespacing=1.5, text="{}:00".format(h), size=5, bgcolor='white', at='50,0.7')
        i += 1
    gscript.run_command('d.mon', stop='cairo')

    # put together with transparency
    foreground = Image.open('foreground_{}.png'.format(camera))
    background = Image.open('background_{}.png'.format(camera))
    foreground = foreground.convert("RGBA")
    datas = foreground.getdata()
    newData = []
    for item in datas:
        intens = item[0] + item[1] + item[2]
        newData.append((item[0], item[1], item[2], min(765-intens, 200)))
    foreground.putdata(newData)

    background.paste(foreground, (0, 0), foreground)
    background.save('series_{}.png'.format(camera), "PNG")

    gscript.try_remove('foreground_{}.png'.format(camera))
    gscript.try_remove('background_{}.png'.format(camera))


def render_animation(camera):
    reg = gscript.region()
    maps = gscript.natural_sort(gscript.list_grouped(type='raster', pattern="people_{}_kernel_*".format(camera))['kernel'])
    width = reg['cols']
    height = reg['rows']
    i = 0
    files = []
    remove = []
    for map in maps:
        gscript.run_command('d.mon', start='cairo', output='foreground_' + map + '.png',
                            width=width, height=height, overwrite=True)
        gscript.run_command('d.rast', map=map)
        gscript.run_command('d.mon', stop='cairo')
        # background
        gscript.run_command('d.mon', start='cairo', output='background_' + map + '.png',
                            width=width, height=height, overwrite=True)
        gscript.run_command('d.rast', map='camera_{}'.format(camera))
        h, minut, sec = gscript.read_command('r.timestamp', map=map).split()[-1].split(':')
        gscript.run_command('d.text', align='lc', linespacing=1.5, text="{}:00".format(h), size=5, bgcolor='white', at='50,0.7')
        gscript.run_command('d.mon', stop='cairo')

        # put together with transparency
        foreground = Image.open('foreground_' + map + '.png')
        background = Image.open('background_' + map + '.png')
        remove.append('foreground_' + map + '.png')
        remove.append('background_' + map + '.png')
        foreground = foreground.convert("RGBA")
        datas = foreground.getdata()
        newData = []
        for item in datas:
            intens = item[0] + item[1] + item[2]
            newData.append((item[0], item[1], item[2], min(765-intens, 200)))
        foreground.putdata(newData)
        background.paste(foreground, (0, 0), foreground)
        background.save('anim_{}_{}.png'.format(camera, i), "PNG")
        files.append('anim_{}_{}.png'.format(camera, i))
        i += 1

    # animation
    params = ["convert", '-delay', '1x2']
    params.extend(files)
    params.extend(['series_{}_tmp.gif'.format(camera)])
    call(params)
    call(['convert', 'series_{}_tmp.gif'.format(camera), '(', '+clone', '-set', 'delay', '500',
          ')', '+swap', '+delete', 'series_{}.gif'.format(camera)])

    # cleanup
    gscript.try_remove('series_{}_tmp.gif'.format(camera))
    for each in files:
        gscript.try_remove(each)
    for each in remove:
        gscript.try_remove(each)


if __name__ == '__main__':
    import os
    os.environ['GRASS_FONT'] = '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'
    gscript.use_temp_region()
    gscript.run_command('g.remove', type='raster', pattern="people_*_kernel_*", flags='f')
    vectors = gscript.list_grouped(type='vector', pattern="people_*")['PERMANENT']
    for each in vectors:
        gscript.run_command('g.region', raster='camera_' + each.split('_')[-1], zoom='camera_' + each.split('_')[-1])
        time_kernel(each)

    maps = gscript.list_grouped(type='raster', pattern="*kernel*")['kernel']
    gscript.write_command('r.colors', map=maps, rules='-', stdin='0% white\n10% yellow\n40% red\n100% magenta')
    for each in vectors:
        gscript.run_command('g.region', raster='camera_' + each.split('_')[-1], zoom='camera_' + each.split('_')[-1])
        render_juxtaposed(each.split('_')[-1])
        render_animation(each.split('_')[-1])
