# -*- coding: utf-8 -*-
"""
@author: Anna Petrasova
"""

import sys
import datetime


def main(input_csv, output_csv):

    with open(output_csv, 'w') as ocsv:
        ocsv.write(','.join(['year', 'month', 'day', 'hour', 'weekday', 'count', 'n_samples']))
        ocsv.write('\n')
        with open(input_csv, 'r') as icsv:
            last_time = [None, None, None, None]
            last_minute = None
            sum_count = None
            n_samples = 0
            for line in icsv.readlines()[1:]:
                year, month, day, hour, minute, typ, count, x, y, xgeo, ygeo, bbox = line.split(',')
                time = [year, month, day, hour]
                if time == last_time:
                    if minute != last_minute:
                        last_minute = minute
                        sum_count += int(count)
                        n_samples += 1
                else:
                    if sum_count is not None:
                        wkday = datetime.datetime(int(last_time[0]), int(last_time[1]), int(last_time[2])).weekday()
                        ocsv.write(','.join([last_time[0], last_time[1], last_time[2], last_time[3], str(wkday), str(sum_count), str(n_samples)]))
                        ocsv.write('\n')

                    last_minute = minute
                    last_time = time
                    sum_count = int(count)
                    n_samples = 1


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "ERROR: Missing input or output"
    else:
        input_csv = sys.argv[1]
        output_csv = sys.argv[2]
        main(input_csv, output_csv)
