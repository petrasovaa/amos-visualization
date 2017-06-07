import os
path = '/home/anna/Documents/Projects/Hipp_STC/filtering'
orthos = ['map_points_points_9266_2012_people',
           'map_points_points_8794_2015_people',
           'map_points_points_5751_2015_people',
           'map_points_points_5751_2014_people',
           'map_points_points_3760_2014_people',
           'map_points_points_3760_2012_people',
           'map_points_points_3451_2014_people']
volumes = ['map3d_points_points_9266_2012_people',
           'map3d_points_points_8794_2015_people',
           'map3d_points_points_5751_2015_people',
           'map3d_points_points_5751_2014_people',
           'map3d_points_points_3760_2014_people',
           'map3d_points_points_3760_2012_people',
           'map3d_points_points_3451_2014_people']
           
for ortho, volume in zip(orthos, volumes):
    f = open('state_template.pvsm', 'r')
    a = f.read()
    b = a.format(raster3d=volume, raster3dfile=os.path.join(path, volume + '.vtk'),
                 ortho=ortho, orthofile=os.path.join(path, ortho + '.vtk'))
    g = open('state_{}.pvsm'.format(ortho), 'w')
    g.write(b)
    g.close()
    f.close()


