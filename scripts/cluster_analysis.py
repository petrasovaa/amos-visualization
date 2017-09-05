# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 21:10:59 2016

@author: anna
"""
import os
import sys
import copy
import numpy as np
import grass.script as gscript
from grass.exceptions import CalledModuleError

CSV_PATH = '/home/anna/Documents/Projects/Hipp_STC/filtering/'


def main(vector):
    out = gscript.read_command('v.db.select', map=vector, columns="distinct time, date").strip()
    unique = []
    for line in out.splitlines()[1:]:
        unique.append(line.split('|'))

    with open(os.path.join(CSV_PATH, vector + '.csv'), 'w') as f:
        f.write('date,time,num_of_groups,mean_size,max_count,1,2,3,4,5,6+\n')
        for time, date in unique:
            output = '{v}__{d}__{t}'.format(v=vector, t=time.replace(':', '_'), d=date.replace('/', '_'))
            gscript.run_command('v.extract', input=vector, where='time = "{time}" and date = "{date}"'.format(time=time, date=date),
                                output=output, overwrite=True)

            gscript.run_command('v.cluster', flags='2', input=output, output='cluster_' + output, min=2,
                                method='optics2', distance=3, overwrite=True)
            try:
                hist = gscript.read_command('v.category', input='cluster_' + output, layer=2, option='print').strip().splitlines()
                hist = [int(each) for each in hist]
                cats, counts = np.unique(hist, return_counts=True)
                res = dict(zip(cats, counts))
                clusters = copy.copy(res)
                if 0 in res:
                    del clusters[0]

                group_size, n = np.unique(clusters.values(), return_counts=True)
                groups = dict(zip(group_size, n))
                sumg = 0
                for i in range(6, 50):
                    sumg += groups.get(i, 0)
                record = [date, time, max(cats), np.mean(clusters.values()), max(clusters.values()), res.get(0, 0), groups.get(2, 0), groups.get(3, 0),
                          groups.get(4, 0), groups.get(5, 0), sumg]
            except CalledModuleError:
                record = [date, time, 0, 0, 0, 0, 0, 0, 0, 0, 0]

            record = [str(r) for r in record]
            f.write(','.join(record))
            f.write('\n')


if __name__ == '__main__':
    for vector in sys.argv[1:]:
        main(vector)
