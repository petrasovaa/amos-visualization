# -*- coding: utf-8 -*-
"""
@author: Anna Petrasova
"""

import os
import sys
import glob
import datetime
import sqlite3
import csv


# we don't count class ML and Geo together, only one of them
# because they mark the same person
classes_for_counting = ('both', 'Geo')


def parse_location(name):
    """Get county, city, park, camera from directory name"""
    # uses this convention: No_Wo_Wo_TL1
    name = os.path.basename(name)
    county, city, park, camera = name.split('_')
    return county, city, park, camera


def parse_timestamp(name):
    """Get date and time based on file name"""
    # uses this convention: 2017-08-10-19h39m38
    year, month, day, time = name.split('-')
    hour, minsec = time.split('h')
    minut, sec = minsec.split('m')
    return year, month, day, hour, minut


def process_dir(input_dir, output_csv_file):
    county, city, park, camera = parse_location(input_dir)
    extension = '.txt'
    label_files = sorted(glob.glob(os.path.join(input_dir, '*' + extension)))
    for lfile in label_files:
        with open(lfile, 'r') as l:
            lines = l.readlines()
            num = int(lines[0].strip())
            # time
            name = os.path.basename(lfile).strip(extension)
            year, month, day, hour, minut = parse_timestamp(name)
            isodate = datetime.datetime(int(year), int(month), int(day), int(hour), int(minut))
            weekday = str(isodate.isoweekday())
            isodate = str(isodate)
            # write record with no people in image
            if num == 0:
                output_csv_file.write(','.join([county, city, park, camera, isodate, year, month, day, hour, minut, weekday, '0']))
                output_csv_file.write('\n')
                continue
            lines = lines[1:]
            count = 0
            for line in lines:
                # count classes
                xtl, ytl, xbr, ybr, cat = line.strip().split()
                if cat in classes_for_counting:
                    count += 1
            # time
            output_csv_file.write(','.join([county, city, park, camera, isodate, year, month, day, hour, minut, weekday, str(count)]))
            output_csv_file.write('\n')

def db_dump(output_csv, output_sqlite):
    con = sqlite3.connect(output_sqlite)
    cur = con.cursor()
    cur.execute("CREATE TABLE counts (county TEXT, city TEXT, park TEXT, camera TEXT, isodate TEXT, year INTEGER, month INTEGER, day INTEGER, hour INTEGER, minute INTEGER, weekday INTEGER, count INTEGER);") # use your column names here

    with open(output_csv, 'rb') as fin:
        # csv.DictReader uses first line in file for column headings by default
        dr = csv.DictReader(fin) # comma is default delimiter
        to_db = [(i['county'], i['city'], i['park'], i['camera'], i['isodate'], i['year'], i['month'], i['day'], i['hour'], i['minute'], i['weekday'], i['count']) for i in dr]

    cur.executemany("INSERT INTO counts (county, city, park, camera, isodate, year, month, day, hour, minute, weekday, count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", to_db)
    con.commit()
    con.close()


def main(label_dir, output_csv, output_sqlite):
    dirs_to_process = glob.glob(os.path.join(label_dir, '*_*_*_*'))
    with open(output_csv, 'w') as f:
        f.write(','.join(["county", "city", "park", "camera", "isodate", "year", "month", "day", "hour", "minute", "weekday", "count"]))
        f.write('\n')
        for dir_to_process in dirs_to_process:
            print "Processing: " + dir_to_process
            process_dir(dir_to_process, f)
    db_dump(output_csv, output_sqlite)

# example query: select park, strftime('%Y-%m-%d', isodate) as yr_mo_day, sum(count) from counts group by park, yr_mo_day;

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "ERROR: Missing input or output"
    else:
        label_dir = '.'
        output_csv = sys.argv[1]
        output_sqlite = sys.argv[2]
        main(label_dir, output_csv, output_sqlite)

