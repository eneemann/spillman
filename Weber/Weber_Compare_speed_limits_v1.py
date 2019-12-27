# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 13:15:13 2019
@author: eneemann
Script to generate report of Weber Area speed limit changes when comparing
current data to updated data (downloaded from AGOL Web App)
"""

import arcpy
from arcpy import env
import os
import time
import pandas as pd
import numpy as np

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script start time is {}".format(readable_start))
today = time.strftime("%Y%m%d")

## Prep data for network

# Set up variables
weber_staging = r"C:\E911\WeberArea\Staging103"
speed_limit_db = r"C:\E911\WeberArea\Staging103\Weber_Speed_Limits.gdb"
original_streets = os.path.join(speed_limit_db, "Streets_Map_from_20190301")
updated_streets = os.path.join(speed_limit_db, "Streets_Map_updates_20191227_WGS84")
working_dir = r"C:\Users\eneemann\Desktop\Neemann\Spillman\Random Work\Weber Area Speed Limits"
env.workspace = speed_limit_db

# Compare Features
print("Comparing {0} to {1} ...".format(os.path.basename(original_streets), os.path.basename(updated_streets)))
out_file = os.path.join(working_dir, "Speed_Limits_" + today + "_Compare_TEST.csv")
if arcpy.Exists(out_file):
    arcpy.Delete_management(out_file)
arcpy.FeatureCompare_management (original_streets, updated_streets, "OBJECTID_1",
                                 "ALL", "", "", "", "", "", "", "CONTINUE_COMPARE",
                                 out_file)

comp_table = "compare_table_" + today
if arcpy.Exists(comp_table):
    arcpy.Delete_management(comp_table)
arcpy.TableToTable_conversion(out_file, speed_limit_db, comp_table)

# Change to working directory
os.chdir(working_dir)

# Export result to numpy array, pandas dataframe
print("Exporting to pandas dataframes ...")
compare_arr = arcpy.da.TableToNumPyArray(comp_table, "*")
compare_df = pd.DataFrame(data = compare_arr)
print(compare_df.head(5).to_string())

# Export street names and address ranges as dataframe to join to compare dataframe
fields = ["OBJECTID_1", "STREET", "L_F_ADD", "L_T_ADD", "R_F_ADD", "R_T_ADD"]
updated_arr = arcpy.da.FeatureClassToNumPyArray(updated_streets, fields)
updated_df = pd.DataFrame(data = updated_arr)
print(updated_df.head(5).to_string())

# Merge dataframes to add street and address range fields
merged_df = pd.merge(compare_df, updated_df, left_on='ObjectID', right_on='OBJECTID_1')

print(merged_df.head(5).to_string())

#col = {"OBJECTID_1":"Index", "Has_error":"Has_change", "Base_value":"Original_value", "Test_value":"New_value"}
col = {"OBJECTID_1_x":"Index", "Has_error":"Has_change", "Base_value":"Original_value", "Test_value":"New_value"}

merged_df.rename(columns = col, inplace=True)

def count_speed(row):
    if 'SPEED' in row['Message']:
        row['temp'] = 1
    return row

final_df = merged_df.apply(count_speed, axis=1)
total = final_df['temp'].sum()
final_df.loc[0, 'Speed_changes'] = final_df['temp'].sum()
final_df.drop(columns = 'temp', inplace = True)
col_order = ["Index", "Has_change", "Identifier", "Message", "Original_value", "New_value", "ObjectID", "STREET", "L_F_ADD", "L_T_ADD", "R_F_ADD", "R_T_ADD", "Speed_changes"]
final_df = final_df[col_order]
print(final_df.head(5).to_string())

filename = "Speed_Limits_" + today + "_Compare_final.csv"
print("Exporting final table to {} ...".format(filename))
final_df.to_csv(filename)

print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))

