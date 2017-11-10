# -*- coding: utf-8 -*-
"""
@author: Anna Petrasova
"""
import sys
import numpy as np
from numpy.linalg import inv

from skimage import transform as tf
from skimage import io


def main(image, gcp_file, point_file, out_point_file, out_image):

    im = io.imread(image)
    dst = []
    src = []
    with open(gcp_file) as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            dstx, dsty, srcx, srcy = line.split()
            dst.append((float(dstx), float(dsty)))
            src.append((float(srcx), float(srcy)))
    dst = np.array(dst)
    src = np.array(src)
    # src2 = copy.copy(src)
    dst[:, 1] = im.shape[0] - dst[:, 1]

    centerx, centery = np.min(src[:, 0]), np.min(src[:, 1])
    src[:, 0] -= centerx
    src[:, 1] -= centery
    revers = 1400
    src[:, 1] = revers - src[:, 1]

    tform3 = tf.ProjectiveTransform()
    tform3.estimate(src, dst)
    warped = tf.warp(im, tform3)
    io.imsave(out_image, warped)

    # rectify points
    H = inv(tform3.params)
    with open(point_file, 'r') as inp_points:
        with open(out_point_file, 'w') as out_points:
            for line in inp_points.readlines():
                year, month, day, hour, minute, type, count, xgeo, ygeo, bbox = line.split(',')
                if type not in ('Geo', 'both'):
                    continue
                xx, yy = float(xgeo), float(ygeo)
                yy = im.shape[0] - yy
                Z = xx * H[2, 0] + yy * H[2, 1] + H[2, 2]
                X = (xx * H[0, 0] + yy * H[0, 1] + H[0, 2]) / Z
                Y = (xx * H[1, 0] + yy * H[1, 1] + H[1, 2]) / Z
                X += centerx
                Y = revers - Y + centery
                out_points.write('{},{},{},{},{},{},{},{}\n'.format(year, month, day, hour, minute, count, X, Y))
    return


if __name__ == '__main__':
    if len(sys.argv) != 6:
        print 'USAGE: python georeference.py /path/to/image.jpg /path/to/gcp_file.txt /path/to/point_file.csv /path/tp/out_point_file.csv /path/to/out_image.jpg'
    else:
        image = sys.argv[1]
        gcp_file = sys.argv[2]
        point_file = sys.argv[3]
        out_point_file = sys.argv[4]
        out_image = sys.argv[5]
        main(image, gcp_file, point_file, out_point_file, out_image)
