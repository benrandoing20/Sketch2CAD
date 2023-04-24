import adsk.core
import adsk.fusion
import traceback
import json
import os
import sys
import time
from pathlib import Path
import importlib
import csv


# Add the common folder to sys.path
COMMON_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

import exporter
importlib.reload(exporter)
import view_control
from logger import Logger
from sketch_extrude_importer import SketchExtrudeImporter

class Reconverter():
    """Reconstruction Converter
        Takes a reconstruction json file and converts it
        to different formats"""

    def __init__(self, json_file, out):
        self.json_file = json_file
        # Export data to this directory
        self.output_dir = json_file.parent.parent / "output"
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)
        # References to the Fusion design
        self.app = adsk.core.Application.get()
        self.design = adsk.fusion.Design.cast(self.app.activeProduct)
        # Counter for the number of design actions that have taken place
        self.inc_action_index = 0
        # Size of the images to export
        self.width = 1024
        self.height = 1024
        self.camera = 0
        #CAD representation
        self.rep = out
        self.ind = 0
        self.dict = {}

    def reconstruct(self):
        """Reconstruct the design from the json file"""
        self.home_camera = self.app.activeViewport.camera
        self.front_camera = self.app.activeViewport.camera
        self.right_camera = self.app.activeViewport.camera
        self.top_camera = self.app.activeViewport.camera
        self.front_camera.viewOrientation = 3
        self.right_camera.viewOrientation = 9
        self.top_camera.viewOrientation = 10
        self.home_camera.isSmoothTransition = False
        self.home_camera.isFitView = True
        self.front_camera.isSmoothTransition = False
        self.front_camera.isFitView = True
        self.right_camera.isSmoothTransition = False
        self.right_camera.isFitView = True
        self.top_camera.isSmoothTransition = False
        self.top_camera.isFitView = True
        self.app.activeViewport.camera = self.top_camera
        importer = SketchExtrudeImporter(self.json_file)
        importer.reconstruct(self.inc_export)
        

    def inc_export(self, data):
        """Callback function called whenever a the design changes
            i.e. when a curve is added or an extrude
            This enables us to save out incremental data"""
        if "curve" in data:
            self.inc_export_curve(data)
        elif "sketch" in data:
            # No new geometry is added
            pass
        elif "extrude" in data:
            self.inc_export_extrude(data)
        self.inc_action_index += 1

    def inc_export_curve(self, data):
        """Save out incremental sketch data as reconstruction takes place"""
        png_file = f"{self.json_file.stem}_{self.inc_action_index:04}.png"
        png_file_path = self.output_dir / png_file
        # Show all geometry
        view_control.set_geometry_visible(True, True, True)

    def inc_export_extrude(self, data):
        """Save out incremental extrude data as reconstruction takes place"""
        
        # Show bodies, sketches, and hide profiles
        view_control.set_geometry_visible(True, False, False)#view_control.set_geometry_visible(True, True, False)
        # Restore the home camera
        self.app.activeViewport.camera = self.home_camera
        self.app.activeViewport.camera.isFitView = True
        # save view of bodies enabled, sketches turned off
        png_file = f"home_{self.json_file.stem}_{self.inc_action_index:04}.png"
        png_file_path = self.output_dir / png_file
        if self.ind<len(self.rep):
            exporter.export_png_from_component(
                png_file_path,
                self.design.rootComponent,
                reset_camera=True,
                width=self.width,
                height=self.height
            )
            self.dict[png_file] = self.rep[:self.ind+1]
            self.ind += 1

    def export(self):
        """Export the final design in a different format"""
        # Image
        png_file = self.output_dir / f"{self.json_file.stem}.png"
        # Hide sketches
        view_control.set_geometry_visible(True, False, False)
        self.app.activeViewport.camera = self.home_camera
        png_file = f"home_{self.json_file.stem}.png"
        png_file_path = self.output_dir / png_file
        exporter.export_png_from_component(
            png_file_path,
            self.design.rootComponent,
            reset_camera=True,
            width=self.width,
            height=self.height
        )

def json_to_rep(jsonfile):
    with open(jsonfile, 'r') as f:
        data = json.load(f)
    steps = len(data["entities"].keys())//2
    keys = list(data["entities"].keys())
    

    # Check that the data is an alternated Sketch Extrusion
    types = []
    for i in range(len(keys)):
        key_type = data["entities"][keys[i]]["type"]
        if types != []:
            if key_type == types[-1]:
                if key_type == "Sketch":
                    keys = keys[:i-1]
                    steps = len(keys)//2
                    break
                else:
                    keys = keys[:i]
                    steps = len(keys)//2
                    break
            else:
                types.append(key_type)
        else:
            types.append(key_type)

    # Remove Extrusions that aren't CutFeatureOperation or NewBodyFeatureOperation, 
    # Sketches that don't have curves and Sketches with SketchEllipse or SketchFittedSpline
    for i in range(len(keys)):
        key_type = data["entities"][keys[i]]["type"]
        # Remove Extrusions that aren't CutFeatureOperation or NewBodyFeatureOperation,
        if key_type != "Sketch":
            op = data["entities"][keys[i]]["operation"]
            if op not in ["CutFeatureOperation", "NewBodyFeatureOperation"]:
                keys = keys[:i-1]
                steps = len(keys)//2
                break
        else:
            # Sketches that don't have curves
            if "curves" not in list(data["entities"][keys[i]].keys()):
                keys = keys[:i]
                steps = len(keys)//2
                break
            # Remove sketches with SketchEllipse or SketchFittedSpline
            else:
                curves = list(data["entities"][keys[i]]["curves"].keys())
                curvetypes = [data["entities"][keys[i]]["curves"][curve]["type"] for curve in curves]
                if "SketchEllipse" in curvetypes or "SketchFittedSpline" in curvetypes:
                    keys = keys[:i]
                    steps = len(keys)//2
                    break

    # # Final representation of the CAD
    # out = []

    # for step in range(steps):
    #     sketch = []
    #     # Get the plane where the sketch is made
    #     plane = data["entities"][keys[step*2]]["reference_plane"]
    #     plane_origin = plane["plane"]["origin"]
    #     plane_normal = plane["plane"]["normal"]
    #     sketch.append([plane_origin["x"], plane_origin["y"], plane_origin["z"], plane_normal["x"], plane_normal["y"], plane_normal["z"]])
        
    #     # Get the points of the sketch
    #     sketch_points = []
    #     sketch_points_labels = []
    #     points = data["entities"][keys[step*2]]["points"]

    #      # Get the curves of the sketch
    #     curves = data["entities"][keys[step*2]]["curves"]

    #     # Create the representation of the sketch
    #     for point in points.keys():
    #         for curve in curves.keys():
    #             if curves[curve]["type"] == "SketchCircle":
    #                 if curves[curve]["center_point"] == point:
    #                     for p in [points[point]["x"], points[point]["y"], points[point]["z"]]:
    #                         sketch_points.append(p)
    #                     sketch_points_labels.append(curves[curve]["radius"])
    #             elif curves[curve]["type"] == "SketchLine":
    #                 if curves[curve]["start_point"] == point:
    #                     for p in [points[point]["x"], points[point]["y"], points[point]["z"]]:
    #                         sketch_points.append(p)
    #                     sketch_points_labels.append(0)
    #             elif curves[curve]["type"] == "SketchArc":
    #                 if curves[curve]["start_point"] == point:
    #                     for p in [points[point]["x"], points[point]["y"], points[point]["z"]]:
    #                         sketch_points.append(p)
    #                     sketch_points_labels.append(1)
    #                 elif curves[curve]["center_point"] == point:
    #                     for p in [points[point]["x"], points[point]["y"], points[point]["z"]]:
    #                         sketch_points.append(p)
    #                     sketch_points_labels.append(2)
    #     sketch.append(sketch_points)
    #     sketch.append(sketch_points_labels)
    #     # Get if we have a positive of negative extrusion
    #     direction = data["entities"][keys[step*2+1]]["operation"]
    #     if direction == "CutFeatureOperation":
    #         direction = -1
    #     else:
    #         direction = 1

    #     # Get the final representation of one step
    #     out.append([sketch,direction * data["entities"][keys[step*2+1]]["extent_one"]["distance"]["value"]])
    
    planes_poss = {"XZ":0, "XY":1, "YZ":2}

    # Final representation of the CAD
    out = []

    for step in range(min(1,steps)):
        #Get the plane where the sketch is made
        # plane = data["entities"][keys[step*2]]["reference_plane"]
        # plane_origin = plane["plane"]["origin"]
        # plane_normal = plane["plane"]["normal"]
        # sketch_plane = [plane_origin["x"], plane_origin["y"], plane_origin["z"], plane_normal["x"], plane_normal["y"], plane_normal["z"]]

        plane = planes_poss[data["entities"][keys[step*2]]["reference_plane"]["name"]]
        
        # Get the points of the sketch
        points = data["entities"][keys[step*2]]["points"]

         # Get the curves of the sketch
        curves = data["entities"][keys[step*2]]["curves"]

        sketch_lines = []
        sketch_circles = []
        sketch_arcs = []
        for curve in curves.keys():
            if curves[curve]["construction_geom"] == False:
                if curves[curve]["type"] == "SketchCircle":
                    for point in points.keys():
                        if curves[curve]["center_point"] == point:
                            sketch_circles.append([points[point]["x"], points[point]["y"], points[point]["z"],curves[curve]["radius"]])
                elif curves[curve]["type"] == "SketchLine":
                    start = []
                    end = []
                    for point in points.keys():
                        if curves[curve]["start_point"] == point:
                            start = (points[point]["x"], points[point]["y"], points[point]["z"])
                        if curves[curve]["end_point"] == point:
                            end = (points[point]["x"], points[point]["y"], points[point]["z"])
                    sketch_lines.append([start[0],start[1],start[2],end[0],end[1],end[2]])
                elif curves[curve]["type"] == "SketchArc":
                    start = []
                    center = []
                    angle = 0
                    for point in points.keys():
                        if curves[curve]["start_point"] == point:
                            start = (points[point]["x"], points[point]["y"], points[point]["z"])
                        # if curves[curve]["end_point"] == point:
                        #     end = (points[point]["x"], points[point]["y"], points[point]["z"])
                        if curves[curve]["center_point"] == point:
                            center = (points[point]["x"], points[point]["y"], points[point]["z"])
                    sketch_arcs.append([start[0], start[1], start[2], center[0], center[1], center[2], curves[curve]["end_angle"]])

        # Get if we have a positive of negative extrusion
        direction = data["entities"][keys[step*2+1]]["operation"]
        if direction == "CutFeatureOperation":
            operation = 0
        else:
            operation = 1
        if data["entities"][keys[step*2+1]]["extent_type"] == 'OneSideFeatureExtentType':
            extent_type = 0
        else:
            extent_type = 1
        # Get the final representation of one step
        out.append([[plane, sketch_lines,sketch_circles,sketch_arcs], [operation, extent_type, data["entities"][keys[step*2+1]]["extent_one"]["distance"]["value"]]])

    return out, steps != 0


def run(context):
    try:
        app = adsk.core.Application.get()
        # Logger to print to the text commands window in Fusion
        logger = Logger()
        # Fusion requires an absolute path
        lis = []
        folder_path = Path(__file__).resolve().parent / "reconstruction" # Replace with the path to your folder
        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                lis.append(folder_path / filename)
                
        json_files = lis[:20]

        main_dict = {}
        json_count = len(json_files)
        for i, json_file in enumerate(json_files, start=1):
            try:
                out, legal = json_to_rep(json_file)
                if legal == 0:
                    continue
                logger.log(f"[{i}/{json_count}] Reconstructing {json_file}")
                reconverter = Reconverter(json_file, out)
                reconverter.reconstruct()
                for key in reconverter.dict.keys():
                    main_dict[key] = reconverter.dict[key]
                with open(reconverter.output_dir / 'my_dict.csv', mode='w', newline='') as csv_file:
                    # Create a CSV writer object
                    writer = csv.writer(csv_file)
                    # Write the header row
                    writer.writerow(main_dict.keys())
                    # Write the data rows
                    writer.writerow(main_dict.values())
                # At this point the final design
                # should be available in Fusion
                #reconverter.export()
                

            except Exception as ex:
                logger.log(f"Error reconstructing: {ex}")
            
            finally:
                # Close the document
                # Fusion automatically opens a new window
                # after the last one is closed
                app.activeDocument.close(False)
        
    except:
        print(traceback.format_exc())
