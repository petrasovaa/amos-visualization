#!/bin/bash
#for ANGLE in `seq 360 -10 200` 
for ANGLE in `seq 0 10 360` 
do
printf -v NAME "out_%03d" $ANGLE
echo $NAME
X=`python -c "import math;print 0.5*math.cos(${ANGLE}./180.*math.pi)+0.5"`
Y=`python -c "import math;print -0.5*math.sin(${ANGLE}./180.*math.pi)+0.5"`
printf -v XX "%0.2f" ${X}
printf -v YY "%0.2f" ${Y}
echo $XX, $YY
XXL=`python -c "print 2*${XX} -1"`
YYL=`python -c "print -2*${YY} +1"`

N=3760
m.nviz.image -nb elevation_map=value@PERMANENT -a mode=fine resolution_fine=1 color_map=camera_${N} volume=map3d_${N} volume_shading=gouraud volume_resolution=1 isosurf_level=1:0.02 isosurf_color_map=time  position=${XX},${YY} height=1734 perspective=36 twist=0 zexag=0.400000  light_position=${XXL},${YYL},0.40 light_brightness=80 light_ambient=20 light_color=255:255:255 output=${NAME} format=ppm size=826,784

convert ${NAME}.ppm legend.png -gravity West -geometry +0-130 -compose over -composite ${NAME}.png
rm ${NAME}.ppm
done
convert -delay 1x2  `seq -f out_%03g.png 270 -10 180` -coalesce -layers OptimizeTransparency tmp.gif
convert tmp.gif \( +clone -set delay 500 \) +swap +delete  tmp2.gif
convert tmp2.gif -crop 750x550+0+150 +repage animation.gif
rm tmp.gif tmp2.gif
