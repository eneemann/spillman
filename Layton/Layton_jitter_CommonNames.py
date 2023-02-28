# -*- coding: utf-8 -*-
"""
Created on Tue Feb 7 15:37:17 2023

@author: eneemann
Script to "jitter" the coordinates of Layton/Davis POIs to ensure that
POIs associated with the same address have different coordinates.
"""

import arcpy
import os
import time
import random

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
print("The script start time is {}".format(readable_start))

######################
#  Set up variables  #
######################

# Set up databases (SGID must be changed based on user's path)
# main_db = r"C:\E911\Layton\LaytonGeoValidation.gdb"
staging_db = r"C:\E911\Layton\Layton_staging.gdb"

arcpy.env.workspace = staging_db
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False

today = time.strftime("%Y%m%d")

common_names = os.path.join(staging_db, 'PointsOfInterest_update_20201023')
poi_update = os.path.join(staging_db, 'PointsOfInterest_update_' + today + '_jitter')

print(f"Copying PointsOfInterest to: {poi_update} ...")
arcpy.management.Copy(common_names, poi_update)

def jitter(val):
    new_val = val + 0.0000003*random.randint(-9,9)
    return new_val    


field_list = ['SHAPE@', 'SHAPE@X', 'SHAPE@Y']
with arcpy.da.UpdateCursor(poi_update, field_list) as update_cursor:
    print("Looping through rows in FC ...")
    for row in update_cursor:
        row[1] = jitter(row[1])
        row[2] = jitter(row[2])
        update_cursor.updateRow(row)


print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))
