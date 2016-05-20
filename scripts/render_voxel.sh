for I in `g.list type=raster_3d pattern="map3d_*"`
do
N=`python -c "print '${I}'.split('_')[-1]"`
g.region raster3d=$I res=1
r3.colors map=$I rules='-' <<EOF
0 blue
0.01 blue
0.02 yellow
0.03 red
1 red
EOF

#m.nviz.image -nb elevation_map=value@PERMANENT -a mode=fine resolution_fine=1 color_map=camera_${N} volume=map3d_${N} volume_shading=gouraud volume_resolution=1 isosurf_level=1:0.01,1:0.02,1:0.03 isosurf_color_map=map3d_${N},map3d_${N},map3d_${N} isosurf_transp_value=170,119,30 position=0.39,0.93 height=2234 perspective=36 twist=0 zexag=0.400000 focus=340,341,1 light_position=-0.22,-0.21,0.80 light_brightness=80 light_ambient=20 light_color=255:255:255 output=voxel_${N} format=ppm size=826,784

for S in 0.01 0.02 0.03
do
m.nviz.image -nb elevation_map=value@PERMANENT -a mode=fine resolution_fine=1 color_map=camera_${N} volume=map3d_${N} volume_shading=gouraud volume_resolution=1 isosurf_level=1:${S} isosurf_color_map=time  position=0.39,0.93 height=1734 perspective=36 twist=0 zexag=0.400000 focus=340,341,1 light_position=-0.81,-0.85,0.40 light_brightness=80 light_ambient=20 light_color=255:255:255 output=voxel_time_${N}_${S} format=ppm size=826,784
done
done
