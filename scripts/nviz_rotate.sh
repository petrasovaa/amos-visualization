#!/bin/bash
for ANGLE in `seq 360 -10 200` 
do
printf -v NAME "out_%03d" $ANGLE
echo $NAME
X=`python -c "import math;print 0.5*math.cos(${ANGLE}./180.*math.pi)+0.5"`
Y=`python -c "import math;print -0.5*math.sin(${ANGLE}./180.*math.pi)+0.5"`
printf -v XX "%0.2f" ${X}
printf -v YY "%0.2f" ${Y}
echo $XX, $YY


m.nviz.image elevation_map=value@PERMANENT -a mode=fine resolution_fine=1 color_map=camera_10823@PERMANENT volume=map3d_10823@PERMANENT volume_shading=gouraud volume_resolution=1 isosurf_level=1:1e-08,1:3e-08,1:4e-08 isosurf_color_map=map3d_10823@PERMANENT,map3d_10823@PERMANENT,map3d_10823@PERMANENT isosurf_transp_value=89,158,2 position=$XX,$YY height=2000 perspective=25 twist=0 zexag=0.500000 focus=315,170,360 light_position=0.68,-0.68,0.80 light_brightness=80 light_ambient=20 light_color=255:255:255 output=${NAME} format=ppm size=413,342 -n

done
convert -delay 1x2  `seq -f out_%03g.ppm 360 -10 200` -coalesce -layers OptimizeTransparency tmp.gif
convert tmp.gif \( +clone -set delay 500 \) +swap +delete  animation.gif
rm tmp.gif 
