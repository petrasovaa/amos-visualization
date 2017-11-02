# -*- coding: utf-8 -*-
"""
@author: Anna Petrasova
"""

import os
import sys
import glob


# we don't count class ML and Geo together, only one of them
# because they mark the same person
classes_for_counting = ('both', 'Geo')


def get_point_from_bbox(x1, y1, x2, y2):
    """Extracts point from bbox, in this case the bottom middle point (people's feet)"""
    x = (x1 + x2) / 2.
    y = y2
    return x, y


def parse_name(name):
    """Get date and time based on file name"""
    # uses this convention: 2017-08-10-19h39m38
    year, month, day, time = name.split('-')
    hour, minsec = time.split('h')
    minut, sec = minsec.split('m')
    return year, month, day, hour, minut


def main(input_dir, output_csv):
    extension = '.txt'
    label_files = sorted(glob.glob(os.path.join(input_dir, '*' + extension)))
    with open(output_csv, 'w') as csv:
        csv.write(','.join(['year', 'month', 'day', 'hour', 'minute',
                            'type', 'count', 'xgeo', 'ygeo', 'bbox [x1 y1 x2 y2]']))
        csv.write('\n')
        for lfile in label_files:
            with open(lfile, 'r') as l:
                lines = l.readlines()
                lines = lines[1:]

                count = 0
                for line in lines:
                    # count classes
                    xtl, ytl, xbr, ybr, cat = line.strip().split()
                    if cat in classes_for_counting:
                        count += 1

                for line in lines:
                    # coordinates
                    xtl, ytl, xbr, ybr, cat = line.strip().split()
                    x, y = get_point_from_bbox(int(float(xtl)), int(float(ytl)),
                                               int(float(xbr)), int(float(ybr)))
                    # time
                    name = os.path.basename(lfile).strip(extension)
                    year, month, day, hour, minut = parse_name(name)

                    csv.write(','.join([year, month, day, hour, minut,
                                       cat, str(count), str(x), str(y),
                                       '[{} {} {} {}]'.format(xtl, ytl, xbr, ybr)]))
                    csv.write('\n')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "ERROR: Missing input or output"
    else:
        input_dir = sys.argv[1]
        output_csv = sys.argv[2]
        main(input_dir, output_csv)
