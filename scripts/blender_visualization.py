# -*- coding: utf-8 -*-
"""
@author: anna
"""

import bpy
import os

fileName = '/home/anna/Documents/Projects/Hipp_STC/tmp/export.x3d'
orthoPath = '/home/anna/Documents/Projects/Hipp_STC/blender/ortho_3760_2014.png'

bpy.context.scene.render.engine = 'CYCLES'

objs = bpy.data.objects
for obj in reversed(bpy.data.objects):
    if obj.name in ("Shape_IndexedFaceSet", "Plane", "Shape_IndexedFaceSet.001", "Shape_IndexedLineSet", "Viewpoint", "Cube"):
        objs.remove(obj, True)
    elif "DirectLight" in obj.name:
        objs.remove(obj, True)
        
        
bpy.ops.import_scene.x3d(filepath=fileName, axis_forward='Z', axis_up='Z')
objs = bpy.data.objects
for obj in reversed(bpy.data.objects):
    if "Shape_IndexedLineSet" in obj.name:
        objs.remove(obj, True)
        
bpy.data.objects['Shape_IndexedFaceSet'].select = True
isosurface = bpy.data.objects['Shape_IndexedFaceSet']
bpy.context.scene.objects.active = bpy.data.objects['Shape_IndexedFaceSet']




plane_dim = bpy.data.objects['Shape_IndexedFaceSet.001'].dimensions
bpy.ops.mesh.primitive_plane_add(radius=1, view_align=False,
                                 enter_editmode=False, location=(0, 0, 0))

plane = bpy.data.objects['Plane']
plane.dimensions = (plane_dim[1], plane_dim[0], plane_dim[2])
for obj in reversed(bpy.data.objects):
    if "Shape_IndexedFaceSet.001" in obj.name:
        objs.remove(obj, True)


# Subdivision render engine to cycles
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.subdivide(number_cuts=4, smoothness=0.2)
bpy.ops.object.mode_set(mode='OBJECT')
modifier = isosurface.modifiers.new('smoothBlob', 'SMOOTH')
modifier.iterations = 2
modifier.factor = 2
bpy.ops.object.modifier_apply( modifier = modifier.name )
bpy.ops.object.shade_smooth()

# ortho
matName = "ortho"
mat = (bpy.data.materials.get(matName) or bpy.data.materials.new(matName))

plane.data.materials.append(mat)
mat.use_nodes = True
node_tree = mat.node_tree
nodes = node_tree.nodes
links = node_tree.links
for node in nodes:
    nodes.remove(node)

textureCoordinateNode = node_tree.nodes.new("ShaderNodeTexCoord")
textureMappingNode = node_tree.nodes.new("ShaderNodeMapping")
diffuseNode = node_tree.nodes.new("ShaderNodeBsdfDiffuse")
outputNode = node_tree.nodes.new("ShaderNodeOutputMaterial")
imageNode = node_tree.nodes.new("ShaderNodeTexImage")

imageNode.image = bpy.data.images.load(orthoPath)
textureMappingNode.rotation[2] = -90 / 180 * 3.1416

links.new (textureCoordinateNode.outputs["Generated"], textureMappingNode.inputs["Vector"])
links.new (textureMappingNode.outputs["Vector"], imageNode.inputs["Vector"])
links.new (imageNode.outputs["Color"], diffuseNode.inputs["Color"])
links.new (diffuseNode.outputs["BSDF"], outputNode.inputs["Surface"])
bpy.data.objects['Plane'].select = True
bpy.ops.mesh.uv_texture_add()
bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.dissolve_limited()
bpy.ops.object.mode_set(mode = 'OBJECT')


bpy.data.objects['Shape_IndexedFaceSet'].select = True

# stc material
matName = "stc"
mat = (bpy.data.materials.get(matName) or bpy.data.materials.new(matName))

isosurface.data.materials.append(mat)
isosurface.data.materials.pop(0)
# Get material tree , nodes and links #
mat.use_nodes = True
node_tree = mat.node_tree
nodes = node_tree.nodes
links = node_tree.links
for node in nodes:
    nodes.remove(node)


geometryNode = node_tree.nodes.new("ShaderNodeNewGeometry")
xyzNode = node_tree.nodes.new("ShaderNodeSeparateXYZ")
minNode = node_tree.nodes.new("ShaderNodeValue")
maxNode = node_tree.nodes.new("ShaderNodeValue")
math1Node = node_tree.nodes.new("ShaderNodeMath")
math2Node = node_tree.nodes.new("ShaderNodeMath")
math3Node = node_tree.nodes.new("ShaderNodeMath")
colorRampNode = node_tree.nodes.new("ShaderNodeValToRGB")
mixerNode = node_tree.nodes.new("ShaderNodeMixShader")
glassNode = node_tree.nodes.new("ShaderNodeBsdfGlass")
diffuseNode = node_tree.nodes.new("ShaderNodeBsdfDiffuse")
outputNode = node_tree.nodes.new("ShaderNodeOutputMaterial")


minNode.outputs[0].default_value = 0
maxNode.outputs[0].default_value = 55.9

math1Node.operation = 'SUBTRACT'
math2Node.operation = 'SUBTRACT'
math3Node.operation = 'DIVIDE'

colorRampNode.color_ramp.interpolation = 'CONSTANT'
elements = colorRampNode.color_ramp.elements
for i, c in zip((0, 9, 11, 13, 17), ((0, 0, 1, 1), (0, 1, 0, 1), (1, 0.8, 0, 1), (1, 0.1, 0, 1), (1, 0, 0, 1))):
    elem = elements.new(i * 3 / 55.9)
    elem.color = c

glassNode.inputs[1].default_value = 0.02
mixerNode.inputs[0].default_value = 0.5


links.new (geometryNode.outputs["Position"], xyzNode.inputs["Vector"])

links.new(maxNode.outputs["Value"], math2Node.inputs[0])
links.new(minNode.outputs["Value"], math2Node.inputs[1])

links.new(xyzNode.outputs["Z"], math1Node.inputs[0])
links.new(minNode.outputs["Value"], math1Node.inputs[1])

links.new(math1Node.outputs["Value"], math3Node.inputs[0])
links.new(math2Node.outputs["Value"], math3Node.inputs[1])

links.new (math3Node.outputs["Value"], colorRampNode.inputs["Fac"])
links.new (colorRampNode.outputs["Color"], diffuseNode.inputs["Color"])
links.new (diffuseNode.outputs["BSDF"], mixerNode.inputs[1])
links.new (glassNode.outputs["BSDF"], mixerNode.inputs[2])
links.new (mixerNode.outputs["Shader"], outputNode.inputs["Surface"])

lamp = bpy.data.objects['Lamp']
lamp.data.type = 'SUN'
lamp.location[2] = 100
lamp = bpy.data.lamps["Lamp"]
lamp.use_nodes = True
lamp.node_tree.nodes["Emission"].inputs[1].default_value = 6
lamp.shadow_soft_size = 10
lamp.cycles.max_bounces = 100

bpy.context.scene.cycles.caustics_reflective = False
bpy.context.scene.cycles.caustics_refractive = False
bpy.context.scene.cycles.sample_clamp_indirect = 3

# export blend4web
bpy.data.objects['Shape_IndexedFaceSet'].select = True
bpy.context.scene.render.engine = 'BLEND4WEB'
bpy.ops.object.shade_smooth()
lamp.energy = 10
lamp.color = (1, 0.98, 0.63)

camera = bpy.data.objects['Camera']
camera.location[0] = 100
camera.location[1] = 0
camera.location[2] = 100
camera.rotation_euler[0] = 0.87
camera.rotation_euler[2] = 1.5708
bpy.data.cameras["Camera"].clip_end = 1e+06
bpy.data.cameras["Camera"].b4w_move_style = 'TARGET'
bpy.data.cameras["Camera"].b4w_target = (-150, 0, 0)

bpy.context.scene.world.b4w_sky_settings.procedural_skydome = True
bpy.context.scene.world.b4w_sky_settings.procedural_skydome = True
bpy.context.scene.world.b4w_sky_settings.render_sky = True

transparentNode = node_tree.nodes.new("ShaderNodeBsdfTransparent")
links.new(transparentNode.outputs["BSDF"], mixerNode.inputs[2])
mixerNode.inputs[0].default_value = 0.1
