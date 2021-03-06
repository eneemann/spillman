# -*- coding: utf-8 -*-
"""
Created on Tue Mar 5 12:38:21 2019
@author: eneemann
Script to build Weber Area Dispatch's QuickestRoute network
"""

import arcpy
from arcpy import env
import os
import time

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script start time is {}".format(readable_start))
today = time.strftime("%Y%m%d")

# Check out Network Analyst license if available. Fail if the Network Analyst license is not available.
if arcpy.CheckExtension("Network") == "Available":
    arcpy.CheckOutExtension("Network")
else:
    raise arcpy.ExecuteError("Network Analyst Extension license is not available.")

## Prep data for network

# Set up variables
weber_staging = r"C:\E911\WeberArea\Staging103"
weber_db = r"C:\E911\WeberArea\Staging103\WeberSGB.gdb"
weber_streets = os.path.join(weber_db, "Streets_Map")
network_db = os.path.join(weber_staging,'QuickestRoute_TEST_' + today +  '.gdb')
network_dataset = os.path.join(network_db, 'QuickestRoute')
env.workspace = network_db

# Create new geodatabase for the network and dataset within it
if arcpy.Exists(network_db):
    arcpy.Delete_management(network_db)
arcpy.CreateFileGDB_management(weber_staging, 'QuickestRoute_TEST_' + today +  '.gdb')
arcpy.CreateFeatureDataset_management(network_db, 'QuickestRoute', weber_streets)

# Create XML Template from current dataset
original_network = r"C:\E911\WeberArea\Staging103\QuickestRoute.gdb\QuickestRoute\QuickestRoute_ND"
output_xml_file = r"C:\E911\WeberArea\Staging103\Network Dataset Template\NDTemplate.xml"
if arcpy.Exists(output_xml_file):
    arcpy.Delete_management(output_xml_file)
arcpy.na.CreateTemplateFromNetworkDataset(original_network, output_xml_file)

# Import current "Streets_Map" data
network_streets = os.path.join(network_dataset, 'Streets')
arcpy.CopyFeatures_management(weber_streets, network_streets)

# Calculated necessary travel time fields
sr_utm12N = arcpy.SpatialReference("NAD 1983 UTM Zone 12N")
arcpy.CalculateGeometryAttributes_management(network_streets, [["Distance", "LENGTH_GEODESIC"]], "MILES_US", "", sr_utm12N)

# Calculate travel time field
update_count = 0
#             0            1         2    
fields = ['TrvlTime', 'Distance', 'SPEED']
with arcpy.da.UpdateCursor(network_streets, fields) as cursor:
    print("Looping through rows to calculate TrvlTime ...")
    for row in cursor:
        row[0] = (row[1]/row[2])*60
        update_count += 1
        cursor.updateRow(row)
print("Total count of TrvlTime updates is {}".format(update_count))

# Calculate "One_Way" field
update_count_oneway = 0
#                    0         1  
fields_oneway = ['ONEWAY', 'One_Way']
with arcpy.da.UpdateCursor(network_streets, fields_oneway) as cursor:
    print("Looping through rows to calculate One_Way field ...")
    for row in cursor:
        if row[0] == '0' or row[0] == None:
#        if row[0] == '0':      
            row[1] = 'B'
            update_count_oneway += 1
        elif row[0] == '1':
            row[1] = 'FT'
            update_count_oneway += 1
        elif row[0] == '2':
            row[1] = 'TF'
            update_count_oneway += 1
        cursor.updateRow(row)
print("Total count of One_Way updates is {}".format(update_count_oneway))

# Recalculate travel times based on multiplication factors
# Interstates to not get an additional multiplication factor applied
# First, multiply state and federal highways by 1.5
update_count1 = 0
#              0
fields1 = ['TrvlTime', 'Multiplier']
# where_clause1 = "HWYNAME IS NOT NULL AND HWYNAME NOT IN ('I-15', 'I-80', 'I-84') AND STREETTYPE <> 'RAMP'"
# 3/11/2019 Update: added 'STREETTYPE IS NULL' to where clause to catch highway segments correctly
# 1/2/2020 Update: added some segments with 'QR FIX' in HWYNAME field to improve routing with 1.5 multiplier
where_clause1 = "HWYNAME IS NOT NULL AND HWYNAME NOT IN ('I-15', 'I-80', 'I-84') AND (STREETTYPE <> 'RAMP' OR STREETTYPE IS NULL)"
with arcpy.da.UpdateCursor(network_streets, fields1, where_clause1) as cursor:
    print("Looping through rows to multiply TrvlTime on state and federal highways ...")
    for row in cursor:
        row[0] = row[0]*1.5
        row[1] = 1.5
        update_count1 += 1
        cursor.updateRow(row)
print("Total count of TrvlTime updates is {}".format(update_count1))

# Second, multiply all other streets by 2
update_count2 = 0
#              0
fields2 = ['TrvlTime', 'Multiplier']
where_clause2 = "HWYNAME IS NULL AND (STREETTYPE IS NULL OR STREETTYPE <> 'RAMP')"
with arcpy.da.UpdateCursor(network_streets, fields2, where_clause2) as cursor:
    print("Looping through rows to multiply TrvlTime on all other roads ...")
    for row in cursor:
        row[0] = row[0]*2
        row[1] = 2
        update_count2 += 1
        cursor.updateRow(row)
print("Total count of TrvlTime updates is {}".format(update_count2))

# Third, populate Multiplier field with 1 for interstates and ramps
update_count3 = 0
#              0
fields3 = ['Multiplier']
where_clause3 = "(HWYNAME IS NOT NULL AND HWYNAME IN ('I-15', 'I-80', 'I-84')) OR STREETTYPE = 'RAMP'"
with arcpy.da.UpdateCursor(network_streets, fields3, where_clause3) as cursor:
    print("Looping through rows to assign Multiplier on ramps and interstates ...")
    for row in cursor:
        row[0] = 1
        update_count3 += 1
        cursor.updateRow(row)
print("Total count of ramp and interstate Multiplier updates is {}".format(update_count3))

## Create network dataset   
# Use previously created XML template
xml_template = output_xml_file

# Create the new network dataset in the output location using the template.
# The output location must already contain feature classes with the same
# names and schema as the original network
arcpy.na.CreateNetworkDatasetFromTemplate(xml_template, network_dataset)
print("Done creating network, now building it ...")

# Build the new network dataset
arcpy.na.BuildNetwork(os.path.join(network_dataset, "QuickestRoute_ND"))
print("Done building the network ...")

arcpy.CheckInExtension("network")

print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))