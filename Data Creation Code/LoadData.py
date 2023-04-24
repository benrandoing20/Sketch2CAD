import adsk.core, adsk.fusion, adsk.cam

import sys
import os

import math
import csv
import ast 
import adsk.core
import adsk.fusion
import traceback
import json
import time
from pathlib import Path
import importlib
import csv
import exporter
importlib.reload(exporter)


# Add the common folder to sys.path
COMMON_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

with open(Path(__file__).resolve().parent / 'my_dict.csv', mode='r') as csv_file:
    # Create a CSV reader object
    reader = csv.reader(csv_file)
    # Read the header row
    header_row = next(reader)
    # Read the data rows
    data_rows = [row for row in reader]

# Create a dictionary from the header and data rows
main_dict = {header_row[i]: data_rows[0][i] for i in range(len(header_row))}
for key in main_dict.keys():
    main_dict[key] = ast.literal_eval(main_dict[key])

keys = list(main_dict.keys())

def rotate_points(points, axis_point, axis_vector, angle):
    # Convert angle to radians
    angle = math.radians(angle)

    # Translate points so that the axis of rotation passes through the origin
    translated_points = []
    for point in points:
        translated_point = tuple(coord - axis_coord for coord, axis_coord in zip(point, axis_point))
        translated_points.append(translated_point)

    # Create rotation matrix
    ux, uy, uz = axis_vector
    norm = math.sqrt(ux**2 + uy**2 + uz**2)
    if norm != 0:
        ux /= norm
        uy /= norm
        uz /= norm
    cos = math.cos(angle)
    sin = math.sin(angle)
    rot_matrix = [
        [cos + ux**2 * (1-cos), ux*uy*(1-cos) - uz*sin, ux*uz*(1-cos) + uy*sin],
        [uy*ux*(1-cos) + uz*sin, cos + uy**2 * (1-cos), uy*uz*(1-cos) - ux*sin],
        [uz*ux*(1-cos) - uy*sin, uz*uy*(1-cos) + ux*sin, cos + uz**2 * (1-cos)]
    ]

    # Rotate points
    rotated_points = []
    for point in translated_points:
        rotated_point = [
            point[0] * rot_matrix[0][0] + point[1] * rot_matrix[0][1] + point[2] * rot_matrix[0][2],
            point[0] * rot_matrix[1][0] + point[1] * rot_matrix[1][1] + point[2] * rot_matrix[1][2],
            point[0] * rot_matrix[2][0] + point[1] * rot_matrix[2][1] + point[2] * rot_matrix[2][2]
        ]
        rotated_points.append(rotated_point)

    # Translate points back to original position
    final_points = []
    for point in rotated_points:
        final_point = tuple(coord + axis_coord for coord, axis_coord in zip(point, axis_point))
        final_points.append(final_point)

    return final_points

def bisector(v1, v2):
    # Compute the norm of each vector
    norm_v1 = sum(x ** 2 for x in v1) ** 0.5
    norm_v2 = sum(x ** 2 for x in v2) ** 0.5

    # Compute the dot product of the two vectors
    dot_product = sum(x * y for x, y in zip(v1, v2))

    if dot_product == -norm_v1 * norm_v2:
        # vectors are pointing in opposite directions, choose any vector in plane
        v3 = [1, 0, 0]  # or any other vector in the plane
    else:
        # Compute the sum of the two normalized vectors
        sum_vectors = [(x / norm_v1) + (y / norm_v2) for x, y in zip(v1, v2)]
        
        # Compute the norm of the sum vector
        norm_sum_vectors = sum(x ** 2 for x in sum_vectors) ** 0.5
        
        # Compute the normalized bisector vector
        v3 = [x / norm_sum_vectors for x in sum_vectors]

    return v3


def create_arc(arcs, point1, point2, angle):
    # Define three points
    # u = [center[i] - point1[i] for i in range(3)]
    # v = [center[i] - point3[i] for i in range(3)]
    # bis = bisector(u,v)
    # point2 = [center[i] + bis[i] for i in range(3)]
    points = rotate_points([point1, point2], [0,0,0], [0,0,1], 90)
    point1 = points[0]
    point2 = points[1]
    # point3 = points[2]
    startPoint = adsk.core.Point3D.create(point1[0], point1[1], point1[2])
    alongPoint = adsk.core.Point3D.create(point2[0], point2[1], point2[2])
    #endPoint = adsk.core.Point3D.create(point3[0], point3[1], point3[2])

    # Create an arc using three points along the arc.
    #arc = arcs.addByThreePoints(startPoint, alongPoint, endPoint)
    arcs.addByCenterStartSweep(alongPoint, startPoint, angle)

def create_line(sketchPoints, lines, point1, point2):
    # Define two points
    points = rotate_points([point1, point2], [0,0,0], [0,0,1], 90)
    #points = rotate_points(points, [0,0,0], [0,0,1], 90)
    point1 = points[0]
    point2 = points[1]
    start = adsk.core.Point3D.create(point1[0], point1[1], point1[2])
    end = adsk.core.Point3D.create(point2[0], point2[1], point2[2])

    # Create a line using two points.
    line = lines.addByTwoPoints(start, end)

def create_circle(circles, point, radius, u, v):
    # Define one points
    norm_u = math.sqrt(u[0]**2+u[1]**2+u[2]**2)
    u = [u[i]*radius/norm_u for i in range(3)]
    norm_v = math.sqrt(v[0]**2+v[1]**2+v[2]**2)
    v = [v[i]*radius/norm_v for i in range(3)]
    p1 = [point[i] + u[i] for i in range(3)]
    p2 = [point[i] + v[i] for i in range(3)]
    p3 = [point[i] - u[i] for i in range(3)]
    points = rotate_points([p1, p2, p3], [0,0,0], [0,0,1], 90)
    #points = rotate_points(points, [0,0,0], [0,0,1], 90)
    p1 = points[0]
    p2 = points[1]
    p3 = points[2]
    point1 = adsk.core.Point3D.create(p1[0], p1[1], p1[2])
    point2 = adsk.core.Point3D.create(p2[0], p2[1], p2[2])
    point3 = adsk.core.Point3D.create(p3[0], p3[1], p3[2])
    circles.addByThreePoints(point1, point2, point3)


def run(context):
    ui = None
    try:
        for key in keys[13:14]:
            cad = main_dict[key]
            step = cad[0]
            app = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app.activeProduct)
            rootComp = design.rootComponent
            step_sketch = step[0]
            extrusion = step[1]
            plane_ind = step_sketch[0]

            sketches = rootComp.sketches
            
            point1 = [0,0,0]
            point2 = [1,0,0]
            point3 = [0,1,0]
            # Create sketch
            if plane_ind == 0:
                sketch2 = sketches.add(rootComp.xZConstructionPlane)

            elif plane_ind == 1:
                sketch2 = sketches.add(rootComp.xYConstructionPlane)
                
            else:
                sketch2 = sketches.add(rootComp.yZConstructionPlane)

            sketchPoints = sketch2.sketchPoints

            lines = sketch2.sketchCurves.sketchLines
            for l in step_sketch[1]:
                create_line(sketchPoints, lines, l[:3], l[3:])

            circles = sketch2.sketchCurves.sketchCircles
            for c in step_sketch[2]:
                point = c[:3]
                # points = rotate_points([point], [0,0,0], [1,0,0], 90)
                # points = rotate_points(points, [0,0,0], [0,0,1], 90)
                # point = points[0]
                create_circle(circles, c[:3], c[3], [point1[i] - point2[i] for i in range(3)], [point1[i] - point3[i] for i in range(3)])

            arcs = sketch2.sketchCurves.sketchArcs
            for a in step_sketch[3]:
                create_arc(arcs, a[:3], a[3:6], a[6])

            # Create another extrude feature based on the circle in the new sketch.
            prof = sketch2.profiles.item(int(sketch2.profiles.count)-1)
            extrudes = rootComp.features.extrudeFeatures
            if extrusion[0] == 0:
                extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
            else:
                extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

            distance = adsk.core.ValueInput.createByReal(extrusion[2])

            if extrusion[1] == 0:
                extInput.setDistanceExtent(False, distance)
            else:
                symmetricExtent = adsk.fusion.SymmetricExtentDefinition.create(distance, False)
                extInput.setOneSideExtent(symmetricExtent, adsk.fusion.ExtentDirections.PositiveExtentDirection)

            extrude = extrudes.add(extInput)

            app.activeViewport.camera.isFitView = True
            png_file = "pics/"+key
            png_file_path = Path(__file__).resolve().parent / png_file
            exporter.export_png_from_component(
                png_file_path,
                design.rootComponent,
                reset_camera=True,
                width=1024,
                height=1024
            )

            # ui = app.userInterface

            # # Define the prompt message for the input box
            # prompt = "Press Enter:"

            # # Show the input box and get the user's input
            # result = ui.inputBox(prompt)

            #app.activeDocument.close(False)


    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



