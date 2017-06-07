# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 16:06:07 2017

@author: anna
"""
import os
import math
import numpy as np
from paraview.simple import LegacyVTKReader, Contour, CameraKeyFrame, CompositeKeyFrame, Text,\
    Show, Hide, GetActiveViewOrCreate, SetActiveSource, GetCameraTrack, GetAnimationTrack, GetAnimationScene, \
    ColorBy, _DisableFirstRenderCameraReset, WriteAnimation, SetActiveView, PythonAnimationCue


def generatePath(center, distance, height):
    angle = np.arange(0, 360, 30) - 90
    angle = angle * math.pi / 180
    x = center[0] + distance * np.cos(angle)
    y = center[1] + distance * np.sin(angle)
    z = np.ones(angle.shape[0]) * height
    return np.stack((x, y, z), axis=-1).flatten()


def addOrtho(path, ortho, renderView, zexag):
    # create a new 'Legacy VTK Reader'
    orthoObject = LegacyVTKReader(FileNames=[os.path.join(path, ortho + '.vtk')])
    # show data in view
    orthoObjectDisplay = Show(orthoObject, renderView)
    # trace defaults for the display properties.
    orthoObjectDisplay.Scale = [1.0, 1.0, zexag]
    # Properties modified on orthoObjectDisplay
    orthoObjectDisplay.MapScalars = 0
    # set active source
    SetActiveSource(orthoObject)


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
    Hide(contour1Display)
    # Properties modified on contour1
    contour1.Isosurfaces = [0.0]
    # Properties modified on contour1Display
    contour1Display.Scale = [1.0, 1.0, zexag]
    # Properties modified on contour1Display
    contour1Display.MapScalars = 0
    # set scalar coloring
    ColorBy(contour1Display, ('CELLS', 'RGB_Voxel'))
    # set active source
    SetActiveSource(contour1)

    return contour1


def addText(label, renderView, pos=None):
    text = Text()
    text.Text = label
    textDisplay = Show(text, renderView)
    textDisplay.FontSize = 12
    # Properties modified on text1Display
    if pos:
        textDisplay.WindowLocation = pos
    return text


def renderAnimation(camera, ortho, volume, path, zexag, numFrames, output):
    # disable automatic camera reset on 'Show'
    _DisableFirstRenderCameraReset()
    # get active view
    renderView = GetActiveViewOrCreate('RenderView')
    renderView.OrientationAxesVisibility = 0
    # uncomment following to set a specific view size
    renderView.ViewSize = [1000, 700]

    addOrtho(path, ortho, renderView, zexag)
    volObject = addVolume(path, volume, renderView)
    bbox = volObject.GetDataInformation().DataInformation.GetBounds()
    minv, maxv = volObject.CellData.GetArray(volume).GetRange(0)
    distance = ((bbox[1] - bbox[0]) + (bbox[3] - bbox[2])) / 2.
    distance *= 1
    height = distance * np.tan(45 / 180. * 3.1415)
    pathpoints = generatePath(((bbox[0] + bbox[1]) / 2, (bbox[2] + bbox[3]) / 2), distance=distance, height=height)
    focalpoint = ((bbox[0] + bbox[1]) / 2, (bbox[2] + bbox[3]) / 2, 0)
    isosurface = addIsosurface(volume, volObject, renderView, zexag)
    # text
    addText('', renderView)
    cam = camera.split('_')
    label = 'Camera {cam} '.format(cam=cam[0])
    if len(cam) > 1:
        label += "in " + cam[1]
    addText(label, renderView, 'UpperLeftCorner')

    #
    # Animation
    #
    # get camera animation track for the view
    cameraAnimationCue1 = GetCameraTrack(view=renderView)

    # create keyframes for this animation track

    keyFrameCam1 = CameraKeyFrame()
    keyFrameCam1.KeyTime = 0.0
    keyFrameCam1.KeyValues = [0.0]
    keyFrameCam1.ViewUp = [0.0, 0.0, 1.0]
    keyFrameCam1.ViewAngle = 30.0
    keyFrameCam1.ParallelScale = 103
    keyFrameCam1.PositionMode = 'Path'
    keyFrameCam1.FocalPointMode = 'Path'
    keyFrameCam1.ClosedFocalPath = 0
    keyFrameCam1.ClosedPositionPath = 1
    keyFrameCam1.Position = focalpoint
    keyFrameCam1.FocalPoint = focalpoint
    keyFrameCam1.PositionPathPoints = pathpoints
    keyFrameCam1.FocalPathPoints = focalpoint

    # create a key frame
    keyFrameCam2 = CameraKeyFrame()
    keyFrameCam2.KeyTime = 1.0
    keyFrameCam2.KeyValues = [0.0]
    keyFrameCam2.Position = focalpoint
    keyFrameCam2.FocalPoint = focalpoint
    keyFrameCam2.ViewUp = [0.0, 0.0, 1.0]
    keyFrameCam2.ViewAngle = 30.0
    keyFrameCam2.ParallelScale = 103
    keyFrameCam2.PositionPathPoints = [zexag, 0.0, 0.0, zexag, zexag, 0.0, zexag, 0.0, 0.0]
    keyFrameCam2.FocalPathPoints = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    keyFrameCam2.PositionMode = 'Path'
    keyFrameCam2.FocalPointMode = 'Path'
    keyFrameCam2.ClosedFocalPath = 0
    keyFrameCam2.ClosedPositionPath = 0

    # initialize the animation track
    cameraAnimationCue1.TimeMode = 'Normalized'
    cameraAnimationCue1.StartTime = 0.0
    cameraAnimationCue1.EndTime = 1.0
    cameraAnimationCue1.Enabled = 1
    cameraAnimationCue1.Mode = 'Path-based'
    cameraAnimationCue1.KeyFrames = [keyFrameCam1, keyFrameCam2]
    cameraAnimationCue1.DataSource = None

    # get animation track
    contour1ContourValuesTrack = GetAnimationTrack('ContourValues', index=-1, proxy=isosurface)

    # create a key frame
    keyFrame1 = CompositeKeyFrame()
    keyFrame1.KeyValues = [0]
    keyFrame1.Base = 2.0
    keyFrame1.StartPower = 10.0
    keyFrame1.EndPower = 0.0
    keyFrame1.Interpolation = 'Exponential'

    # create a key frame
    keyFrame2 = CompositeKeyFrame()
    keyFrame2.KeyTime = 1.0
    keyFrame2.KeyValues = [maxv]
    keyFrame2.Base = 2.0
    keyFrame2.StartPower = 10.0
    keyFrame2.EndPower = 0.0
    keyFrame2.Interpolation = 'Exponential'

    # initialize the animation track
    contour1ContourValuesTrack.KeyFrames = [keyFrame2, keyFrame1]

    # get animation track for text
    PythonAnimationCue1 = PythonAnimationCue()
    PythonAnimationCue1.Script = """
from paraview.simple import *
def start_cue(self): pass

def tick(self):
    c = FindSource("Contour1").Isosurfaces[0]
    t = FindSource("Text1")
    t.Text = "Isosurface {:.5f}".format(c)

def end_cue(self): pass
    """
    isovalues = np.logspace(np.log10(1e-5), np.log10(maxv), num=numFrames)
    isocount = 0
    for isovalue in isovalues:
        isosurface.Isosurfaces = [isovalue]
        keyFrame1.KeyValues = [isovalue]
        keyFrame2.KeyValues = [isovalue]
        # get animation scene
        animationScene1 = GetAnimationScene()
        # Properties modified on animationScene1
        animationScene1.NumberOfFrames = numFrames
        animationScene1.Cues.append(PythonAnimationCue1)

        # save animation images/movie
        WriteAnimation(os.path.join('{o}.{v:04d}.png'.format(o=output, v=isocount)),
                       Magnification=1, FrameRate=20.0, Compression=True)
        isocount += 1
    SetActiveSource(None)
    # set active view
    SetActiveView(None)
    renderView.ResetCamera()


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        sys.exit()
    camera = sys.argv[1]
    path = '/home/anna/Documents/Projects/Hipp_STC/filtering/'
    ortho = 'map_points_points_{}_people'.format(camera)
    volume = 'map3d_points_points_{}_people'.format(camera)
    renderAnimation(camera, ortho=ortho, volume=volume, path=path, zexag=3, numFrames=20,
                    output=ortho)

#for I in 3451_2014 3760_2012 3760_2014 5751_2014 5751_2015 8794_2015 9266_2012;do python render_volume1.py $I;done