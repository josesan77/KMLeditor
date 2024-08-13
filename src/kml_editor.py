# -*- coding: utf-8 -*-
"""
(Google) KML file editor, version 0.2 - editing Google map path coordinates (without map background)
Read (Google maps) KML file: The read_kml_file() function reads the selected KML file and extracts the KML geo-data from it.
It removes the first XML declaration if exists before further processing by fastkml module.
Extracting coordinates: The function extract_coordinates() extracts the coordinates from the KML file.
Calculation of the bounding box: The calculate_bounding_box() function calculates the smallest (geo-coordinate based) bounding box for the given coordinates.
Displaying coordinates: The software displays the coordinates on a 2D canvas (software window), where individual points can be moved interactively.
If any change occurs in the coordinates, the modified path can be saved as a basic (Google map compatible) kml file. Supplementary informations may be lost, modified path is suggested to be saved as a copy!
This code allows you to graphically display the coordinates of Google Maps KMZ files and move points interactively. If you need additional functions, the code can be further developed.

Notes: 
    Google map path contains multiple points as parts of a Linestring which defines a set of geo-coordinates which should be connected (on the map by a line) in the order of appearence. https://developers.google.com/maps/documentation/javascript/examples/polyline-simple
    Google map is not loaded to serve as background as it requires Google API key. Not part of this basic software!

Prerequisites: in command line prompt, install the following modules by typing:
pip install fastkml tkinter shapely

Check existance of pygeoif module in Python IDLE (or IDE) by an import test:
from pygeoif import Point, LineString

@author: Data4every1
Created on Mon Aug 10 14:12:27 2024
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from fastkml import kml
from pygeoif import Point, LineString
import sys, os

global bounding_box


# KML fájl beolvasása és parszolása
def read_kml_file(file_path):
    #load kml file from given path, removes XML declaration from file start if exists because fastkml module does not support XML declarations
    with open(file_path, 'rt', encoding='utf-8') as file:
        kml_data = file.read()
        # XML deklaráció eltávolítása
    if kml_data.startswith('<?xml'):
        kml_data = kml_data.split('?>', 1)[1]  # Keeps part after XML declaration
    kml_d = kml.KML()
    kml_d.from_string(kml_data)
    
    return kml_d

# Extracting coordinates from KML file
def extract_coordinates(kml_obj):
    coordinates = []

    for feature in kml_obj.features():
        for placemark in feature.features():
            if isinstance(placemark.geometry, Point):
                # single point coordinates
                coordinates.append((placemark.geometry.y, placemark.geometry.x))
            elif isinstance(placemark.geometry, LineString):
                # Line(string) coordinates
                for coord in placemark.geometry.coords:
                    coordinates.append((coord[1], coord[0]))  # (lat, lon)
    return coordinates

# Calculation of bounding rectangle
def calculate_bounding_box(coords):
    global bounding_box, lat_max, lon_min, lat_height, lon_width
    lats, lons = zip(*coords)
    bounding_box = (min(lats), max(lats)), (min(lons), max(lons))
    lat_max = max(bounding_box[0])
    lon_min = min(bounding_box[1])
    lat_height = (bounding_box[0][1]-bounding_box[0][0])
    lon_width = (bounding_box[1][1]-bounding_box[1][0])
    return bounding_box

def open_kml_file():
    root = tk.Tk() # pointing root to Tk() to use it as Tk() in program.
    root.withdraw() # Hides small tkinter window.
    root.attributes('-topmost', True) # Opened windows will be active. above all windows despite of selection.
    filepath = None
    try:
        filepath = filedialog.askopenfilename(title='Select KML file', \
                                filetypes=[('Google KMl files', '*.kml')],\
                                initialdir= os.getcwd()) # 
        print('Opening KML file: ' + str(filepath) + '/n')
    except Exception as e:
        if filepath is None:
            print('No file has been selected. Exit.')
        print(e)
        sys.exit()
    return filepath

class PointMoverApp:
    def __init__(self, root, coordinates, bounding_box):
        self.root = root
        self.root.title("Google KML Geo-point Editor App v 0.2")
        self.modified = False

        # Creating Panel (on TOP)
        self.panel = tk.Frame(root, bg="lightblue", height=30)
        self.panel.pack(side=tk.TOP, fill=tk.X)

        # Adding text to Panel
        self.label = tk.Label(self.panel, text="Drag&drop point(s), then save as a copy!", bg="lightgray", fg="darkblue", font=("Arial", 12))
        self.label.pack(side=tk.LEFT, padx=10, pady=5)

        # Save (as copy) button, on the RIGHT
        self.save_button = tk.Button(self.panel, text="Save (as copy!)", state=tk.DISABLED, command=self.save_kml)
        self.save_button.pack(side=tk.RIGHT, padx=10)

        # Creating Canvas for display
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()

        # Handling coordinates
        self.points = []
        for coord in coordinates:
            self.create_point(coord)
        
        self.selected_point = None
        self.modified = False

    def create_point(self, coord):
        x, y = self.coord_to_canvas(coord)
        point = self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red")
        self.canvas.tag_bind(point, "<B1-Motion>",\
                             lambda event, pt=point: self.move_point(event, pt))
        self.points.append((point, coord))

    def coord_to_canvas(self, coord):
        # Geo-coordinate translation to Canvas coordinates
        lat, lon = coord
        x = 10+ ( lon - lon_min) * (780 / lon_width)  # 800 px width canvas
        y = 10+ ( lat_max - lat ) * (580 / lat_height)   # 
        return x, y

    def canvas_to_coord(self, x, y):
        # Canvas coordinate conversion to Geo-coordinates
        global bounding_box
        # lat, lon = x, y
        lon = (x-10)/780*lon_width + lon_min # 800 px width canvas, 10px padding
        lat = lat_max - (y-10)/580*lat_height # 600 px width canvas, 10px padding
        return lat, lon

    def move_point(self, event, point):
        self.canvas.coords(point, event.x-5, event.y-5, event.x+5, event.y+5)
        new_coord = self.canvas_to_coord(event.x, event.y)
        print(new_coord)
        for i, (pt, coord) in enumerate(self.points):
            if pt == point:
                self.points[i] = (pt, new_coord)
                break
        if not self.modified:
            self.save_button.config(state=tk.NORMAL)
            self.modified = True

    def save_kml(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".kml",\
                                            filetypes=[("KML files", "*.kml")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.generate_kml_content())
            messagebox.showinfo("File saved", "File saved successfully.")
            self.save_button.config(state=tk.DISABLED)

    def generate_kml_content(self):
        kml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        kml_content += '<kml xmlns="http://www.opengis.net/kml/2.2">\n' #xmlns:gx="http://www.google.com/kml/ext/2.2">
        kml_content += '<Document>\n'
        kml_content += f'  <Placemark>\n'
        kml_content += f'    <LineString>\n'
        kml_content += f'      <coordinates>'
        for _, coord in self.points:
            kml_content += f'{coord[1]},{coord[0]},0 '
        kml_content += f'      </coordinates>\n'
        kml_content += f'    </LineString>\n'
        kml_content += f'  </Placemark>\n'
        kml_content += '</Document>\n'
        kml_content += '</kml>'
        return kml_content
    
    
    def save_kml(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".kml",\
                                                 filetypes=[("KML files", "*.kml")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.generate_kml_content())
            tk.messagebox.showinfo("Saved", "File saved successfully.\n" + file_path)

def on_closing():
    # Safety question before closing
    if messagebox.askokcancel("Exit", "Do you really want to exit?"):
        root.destroy()  # Closing software window

if __name__ == "__main__":
    #main software
    filepath = open_kml_file()
    kml_obj = read_kml_file(filepath)
    coordinates = extract_coordinates(kml_obj)
    bounding_box = calculate_bounding_box(coordinates)
    root = tk.Tk()
    # Setting event handler for window closing
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.title("Google KML file editor - 2024 v 0.1")
    app = PointMoverApp(root, coordinates, bounding_box)

    root.mainloop()