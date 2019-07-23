# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 16:10:21 2019
@author: eneemann
Script to detect possible new street segments by comparing new data to current data

- Input Roads
- Merge input roads into single feature
- Buffer input roads
- Create SGID roads layer from specific counties
- Select SGID roads not in buffer
- Export possible new SGID roads

22 Jul 2019: Created initial version of code (EMN).
"""

import arcpy
from arcpy import env
import os
import time


# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script start time is {}".format(readable_start))

staging_db = r"C:\E911\Box Elder CO\BoxElder_Staging.gdb"
SGID = r"C:\Users\eneemann\AppData\Roaming\ESRI\ArcGISPro\Favorites\sgid.agrc.utah.gov.sde"
current_streets = os.path.join(staging_db, "BoxElder_Streets_updates_20190718")
sgid_roads = os.path.join(SGID, "SGID10.TRANSPORTATION.Roads")
env.workspace = staging_db
env.overwriteOutput = True

# Export roads from SGID into new FC based on desired counties
today = time.strftime("%Y%m%d")
export_roads = os.path.join(staging_db, "Roads_SGID_export_" + today)

where_SGID = "COUNTY_L IN ('49003')"      # Box Elder
#arcpy.FeatureClassToFeatureClass_conversion (sgid_roads, staging_db, export_roads, where_SGID)

# Create a 10m buffer around current streets data to use for selection
#arcpy.MakeFeatureLayer_management(export_roads, "export_roads_lyr")
roads_buff = os.path.join(staging_db, "temp_roads_buffer")
if arcpy.Exists(roads_buff):
    arcpy.Delete_management(roads_buff)
print("Buffering {} ...".format(current_streets))
arcpy.Buffer_analysis(current_streets, roads_buff, "10 Meters", "FULL", "ROUND", "ALL")

# Need to make a layer from SGID roads feature class here
arcpy.MakeFeatureLayer_management(sgid_roads, "sgid_roads_lyr", where_SGID)
print("SGID roads layer feature count: {}".format(arcpy.GetCount_management("sgid_roads_lyr")))
# Select all features within 5m of current addpts FC
fields = ['Notes']
arcpy.SelectLayerByLocation_management("sgid_roads_lyr", "HAVE_THEIR_CENTER_IN", roads_buff,
                                                     "", "", "INVERT")
outname = os.path.join(staging_db, "SGID_roads_to_review_" + today)
arcpy.CopyFeatures_management("sgid_roads_lyr", outname)


print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))