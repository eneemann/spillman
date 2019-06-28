# -*- coding: utf-8 -*-
"""
Created on Wed Jun 5 14:15:04 2019
@author: eneemann

Script to identify null geometries in a feature class with open source tools
"""

import os
import time
import geopandas as gpd
import fiona

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script start time is {}".format(readable_start))

# Get list of feature classes in a geodatabase
database = r"C:\E911\TOC\TOC_Data_UTM.gdb"
#database = r"C:\E911\StGeorgeDispatch_TEST\Bad_Geometries_TEST.gdb"
fclist = fiona.listlayers(database)

# Loop through feature classes, process differntly if point, line, or polygon
for fc in fclist:
    layer = fiona.open(database, layer=fc)
    if layer.schema['geometry'] == ('Point' or 'MultiPoint'):
        print("{} geometry type is: Point, looping through features ...".format(layer.name, layer.schema['geometry']))
        # Assign x and y min/max values from layer bounds and use to verify each point
        xmin, ymin, xmax, ymax = layer.bounds[0], layer.bounds[1], layer.bounds[2], layer.bounds[3]
        for feature in layer:
            geom = feature['geometry']
            if geom is None:
                print("Geometry is invalid (null) for ID: {}".format(feature['id']))
            # Check for points with coordinates outside of layer bounds, these are invalid
            elif geom['coordinates'][0] < xmin or geom['coordinates'][0] > xmax:
                print("Geometry is invalid (outside of bounds) for ID: {}".format(feature['id']))
            elif geom['coordinates'][1] < ymin or geom['coordinates'][1] > ymax:
                print("Geometry is invalid (outside of bounds) for ID: {}".format(feature['id']))
        
    elif layer.schema['geometry'] in ['LineString','MultiLineString']:
        print("{} geometry type is: {}, looping through features ...".format(layer.name, layer.schema['geometry']))
        # Loop through line features, find those with empty coordinate tuples
        for feature in layer:
            geom = feature['geometry']
            if geom is None:
                print("Geometry is invalid (null) for ID: {}".format(feature['id']))
            elif len(geom['coordinates'][0]) == 0:
                print("Geometry is invalid (empty) for ID: {}".format(feature['id']))
                
    elif layer.schema['geometry'] in ['Polygon', 'MultiPolygon']:
        print("{} geometry type is: {}, looping through features ...".format(layer.name, layer.schema['geometry']))
        # Loop through polygon features, find those with empty coordinate tuples
        for feature in layer:
            geom = feature['geometry']
            if geom is None:
                print("Geometry is invalid (null) for ID: {}".format(feature['id']))
            elif len(geom['coordinates'][0]) == 0:
                print("Geometry is invalid (empty) for ID: {}".format(feature['id']))


###############
#  Functions  #
###############


def find_bad_geom(db, data):
    layer = fiona.open(db, layer=data)
    if layer.schema['geometry'] == ('Point' or 'MultiPoint'):
        # Unsure how to ID null geometries in point data right now
        print("{} geometry type is: {}, skipping this geometry type ...".format(layer.name, layer.schema['geometry']))
    elif layer.schema['geometry'] in ['LineString','MultiLineString']:
        print("{} geometry type is: {}, looping through features ...".format(layer.name, layer.schema['geometry']))
        # Loop through line features, find those with empty coordinate tuples
        for feature in layer:
            geom = feature['geometry']
            if geom is None or len(geom['coordinates'][0]) == 0:
                print("Geometry is invalid for ID: {}".format(feature['id']))
    elif layer.schema['geometry'] in ['Polygon', 'MultiPolygon']:
        print("{} geometry type is: {}, looping through features ...".format(layer.name, layer.schema['geometry']))
        # Loop through polygon features, find those with empty coordinate tuples
        for feature in layer:
            geom = feature['geometry']
            if geom is None or len(geom['coordinates'][0]) == 0:
                print("Geometry is invalid for ID: {}".format(feature['id']))

##########################
#  Call Functions Below  #
##########################

#for fc in sorted(fclist):
#    find_bad_geom(database, fc)

print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))
