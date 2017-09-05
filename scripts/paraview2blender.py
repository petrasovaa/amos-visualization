# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 16:06:07 2017

@author: anna
"""
import os
import math
import numpy as np
from paraview.simple import LegacyVTKReader, Contour, Slice, CameraKeyFrame, CompositeKeyFrame, Text,\
    Show, Hide, GetActiveViewOrCreate, SetActiveSource,  \
    ColorBy, _DisableFirstRenderCameraReset, WriteAnimation,ExportView, Transform


def addOrtho(path, ortho, renderView, zexag):
    # create a new 'Legacy VTK Reader'
    orthoObject = LegacyVTKReader(FileNames=[os.path.join(path, ortho + '.vtk')])
    # show data in view
    orthoObjectDisplay = Show(orthoObject, renderView)
    # trace defaults for the display properties.
    #orthoObjectDisplay.Scale = [1.0, 1.0, zexag]
    # Properties modified on orthoObjectDisplay
    orthoObjectDisplay.MapScalars = 0
    # set active source
    Hide(orthoObject, renderView)
    SetActiveSource(orthoObject)
    return orthoObject


def addVolume(path, volume, renderView):
    # create a new 'Legacy VTK Reader'
    volumeObject = LegacyVTKReader(FileNames=[os.path.join(path, volume + '.vtk')])

    # show data in view
    Show(volumeObject, renderView)
    # hide data in view
    Hide(volumeObject, renderView)
    SetActiveSource(volumeObject)
    return volumeObject


def addIsosurface(volume, volumeObject, renderView, zexag, hide=False):
    # create a new 'Contour'
    contour1 = Contour(Input=volumeObject)
    contour1.ContourBy = ['POINTS', volume]
    # show data in view
    contour1Display = Show(contour1, renderView)
    # Properties modified on contour1
    contour1.Isosurfaces = [0.05]
    # Properties modified on contour1Display
    #contour1Display.Scale = [1.0, 1.0, zexag]
    # Properties modified on contour1Display
    contour1Display.MapScalars = 0
    # set scalar coloring
    ColorBy(contour1Display, ('CELLS', 'RGB_Voxel'))
    # set active source
    SetActiveSource(contour1)
    Hide(contour1Display, renderView)
    return contour1



def export_x3d(camera, ortho, volume, path, zexag):
    # disable automatic camera reset on 'Show'
    _DisableFirstRenderCameraReset()
    # get active view
    renderView = GetActiveViewOrCreate('RenderView')
    renderView.OrientationAxesVisibility = 0
    ortho = addOrtho(path, ortho, renderView, zexag=1)
    volObject = addVolume(path, volume, renderView)
    bbox = volObject.GetDataInformation().DataInformation.GetBounds()
    tx = (bbox[0] + bbox[1]) / 2.
    ty = (bbox[2] + bbox[3]) / 2.
    transform1 = Transform(Input=volObject)
    transform1.Transform = 'Transform'
    transform1Display = Show(transform1, renderView)
    transform1.Transform.Translate = [-tx, -ty, 0]
    transform1.Transform.Scale = [1, 1, 3]
    isosurface = addIsosurface(volume, transform1, renderView, zexag=1)
    transform1Display.ColorArrayName = [None, '']

    # create a new 'Transform'
    transform2 = Transform(Input=ortho)
    transform2.Transform = 'Transform'
    transform2Display = Show(transform2, renderView)
    transform2.Transform.Translate = [-tx, -ty, 0.0]
    transform2.Transform.Scale = [1, 1, 3]
    # trace defaults for the display properties.
    transform2Display.ColorArrayName = [None, '']


# Properties modified on transform1.Transform
    
    ExportView('/tmp/test.x3d', view=renderView)



camera = '3760_2014'
type = 'people'
path = '/home/anna/Documents/Projects/Hipp_STC/filtering/'
ortho = 'map_points_points_{}_{}'.format(camera, type)
volume = 'map3d_points_points_{}_{}'.format(camera, type)
export_x3d(camera, ortho=ortho, volume=volume, path=path, zexag=3)

