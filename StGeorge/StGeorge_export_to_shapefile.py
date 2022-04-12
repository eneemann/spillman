# -*- coding: utf-8 -*-
"""
Created on Wed Mar 2 10:15:56 2022
@author: eneemann

2 Mar 2022 - extremely simple script to export shapefiles to a folder
    - This was created from the Weber script
"""

import arcpy
from arcpy import env
import time

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script start time is {}".format(readable_start))

# staging_db = r"C:\E911\StGeorgeDispatch\StGeorge_Staging.gdb"
live_db = r"C:\E911\StGeorgeDispatch\StGeorgeDispatch_WGS84.gdb"
env.workspace = live_db
output_folder = r"C:\E911\StGeorgeDispatch\1 Geovalidation_update_20220317"

#input_features = ['StGeorge_Dispatch_Common_Place_Points',
#                  'StGeorge_Dispatch_AddressPoints',
#                  'StGeorge_Dispatch_Streets_All',
#                  'StGeorge_Dispatch_Fire_Zones',
#                  'StGeorge_Dispatch_Law_Zones',
#                  'StGeorge_Dispatch_CITYCD',
#                  'StGeorge_Dispatch_POI',
#                  'StGeorgeDispatch_Municipalities']

#input_features = ['StGeorge_Dispatch_Common_Place_Points',
#                  'StGeorge_Dispatch_AddressPoints',
#                  'StGeorge_Dispatch_Streets_All',
#                  'StGeorge_Dispatch_Law_Zones']

#input_features = ['StGeorge_Dispatch_AddressPoints',
#                  'StGeorge_Dispatch_Common_Place_Points',
#                  'StGeorge_Dispatch_Streets_All']

#input_features = ['StGeorge_Dispatch_AddressPoints',
#                  'StGeorge_Dispatch_Common_Place_Points',
#                  'StGeorge_Dispatch_Streets_All',
#                  'StGeorge_Dispatch_CITYCD']

input_features = ['StGeorge_Dispatch_Law_Zones']

arcpy.conversion.FeatureClassToShapefile(input_features, output_folder)

print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))