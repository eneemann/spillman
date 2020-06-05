# -*- coding: utf-8 -*-
"""
Created on Tue Jun 2 08:51:17 2020
@author: eneemann
Script to compare address points to road centerlines for quality control.
* 

2 June 2020: first version of code (EMN)
"""

import arcpy
from arcpy import env
import os
import time
import pandas as pd
import numpy as np
from Levenshtein import StringMatcher as Lv
from matplotlib import pyplot as plt
from tqdm import tqdm

tqdm.pandas()


# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print(f"The script start time is {readable_start}")
today = time.strftime("%Y%m%d")

# Create variables
working_db = r"C:\E911\RichfieldComCtr\richfield_staging.gdb"
env.workspace = working_db
env.overwriteOutput = True

work_dir = r'C:\E911\RichfieldComCtr\Addpts_working_folder'
data_name = 'richfield'

streets = os.path.join(working_db, "streets_update_20200515_UTM")  # Point to current roads in working_db
addpts = os.path.join(working_db, "address_points_update_20200526")  # Point to current addpts in working_db

# Input street component fields that will be used for each feature class
street_fields = {"predir": "PREDIR",
            "name": "STREETNAME",
            "sufdir": "SUFDIR",
            "type": "STREETTYPE",
            "l_f_add": "L_F_ADD",
            "l_t_add": "L_T_ADD",
            "r_f_add": "R_F_ADD",
            "r_t_add": "R_T_ADD",}


addpt_fields = {"addnum": "AddNum",
                "predir": "PrefixDir",
                "name": "StreetName",
                "sufdir": "SuffixDir",
                "type": "StreetType"}


# Insert full address field here in order to use it
fulladd_field = False
# fulladd_field = 'ADDRESS'

if fulladd_field:
    address_parts = False
else:
    address_parts = True

print(f'Using address component fields: {address_parts}')


# Copy current address points into a working FC and add fields
working_addpts = os.path.join(working_db, "zzz_AddPts_working_" + today)
if arcpy.Exists(working_addpts):
    arcpy.Delete_management(working_addpts)
arcpy.CopyFeatures_management(addpts, working_addpts)

arcpy.AddField_management(working_addpts, "Notes", "TEXT", "", "", 50)
arcpy.AddField_management(working_addpts, "full_street", "TEXT", "", "", 50)

# Copy current roads into a working FC and add 'FULL_STREET' field
working_roads = os.path.join(working_db, "zzz_Streets_working_" + today)
if arcpy.Exists(working_roads):
    arcpy.Delete_management(working_roads)
arcpy.CopyFeatures_management(streets, working_roads)

arcpy.AddField_management(working_roads, "FULL_STREET", "TEXT", "", "", 50)

###############
#  Functions  #
###############

unit_list = ['UNIT', 'TRLR', 'APT', 'STE', 'SPC', 'BSMT', 'LOT', '#', 'BLDG',
             'HNGR', 'OFC', 'OFFICE', 'SP', 'HANGAR', 'REAR']

def calc_street_addpts_fulladd(working, full_add):
    update_count = 0
    
    fields = [full_add, 'full_street']
    with arcpy.da.UpdateCursor(working, fields) as cursor:
        print("Looping through rows in addpts FC ...")
        for row in cursor:
            # break off and discard the house number
            parts = row[0].split(' ')
            if parts[0].isdigit():
                temp = " ".join(parts[1:])
            else:
                print(f"    Address {row[0]} does not have a valid house number")
            
            final = temp

            # check parts of remaining address for a unit type separator
            # if found split at unit type and discard everything after
            temp_parts = temp.split(' ')
            for i in np.arange(len(temp_parts)):
                print(i)
                if temp_parts[i].upper() in unit_list:
                    # print(f'{temp_parts[i]} is in the unit list')
                    splitter = temp_parts[i]
                    final = temp.split(splitter, 1)[0]
                    break
                    # print(f'{temp_parts[i]} is NOT in the unit list')

            row[1] = final.strip().replace("  ", " ").replace("  ", " ").replace("  ", " ")
            update_count += 1
            cursor.updateRow(row)  

def calc_street_addpts(working, add_flds):
    
    update_count = 0
    
    flist = arcpy.ListFields(working)
    fnames = [f.name for f in flist]
    # print(fnames)

    if 'STREET' in fnames:
        # Calculate 'full_street' field where applicable
        fields = ['STREET', 'full_street']
        with arcpy.da.UpdateCursor(working, fields) as cursor:
            print("Looping through rows in addpts FC ...")
            for row in cursor:
                if row[0] is None: row[0] = ''
                row[1] = row[0].strip().replace("  ", " ").replace("  ", " ").replace("  ", " ")
                update_count += 1
                cursor.updateRow(row)    
    else:    
        # Calculate 'full_street' field where applicable
        fields = [add_flds['predir'], add_flds['name'], add_flds['sufdir'], add_flds['type'], 'full_street']
        with arcpy.da.UpdateCursor(working, fields) as cursor:
            print("Looping through rows in addpts FC ...")
            for row in cursor:
                if row[0] is None: row[0] = ''
                if row[1] is None: row[1] = ''
                if row[2] is None: row[2] = ''
                if row[3] is None: row[3] = ''
                parts = [row[0], row[1], row[2], row[3]]
                row[4] = " ".join(parts)
                row[4] = row[4].strip()
                row[4] = row[4].replace("  ", " ").replace("  ", " ").replace("  ", " ")
    #            print(f"New value for {fields[4]} is: {row[4]}")
                update_count += 1
                cursor.updateRow(row)
            
    print(f"Total count of updates: {update_count}")
    
    
def calc_street_roads(working, st_flds):
    
    update_count = 0
    
    flist = arcpy.ListFields(working)
    fnames = [f.name for f in flist]
    # print(fnames)

    if 'STREET' in fnames:
        # Calculate 'full_street' field where applicable
        fields = ['STREET', 'FULL_STREET']
        with arcpy.da.UpdateCursor(working, fields) as cursor:
            print("Looping through rows in roads FC ...")
            for row in cursor:
                if row[0] is None: row[0] = ''
                row[1] = row[0].strip().replace("  ", " ").replace("  ", " ").replace("  ", " ")
                update_count += 1
                cursor.updateRow(row)
    else:
        # Calculate 'FULL_STREET' field where applicable
        fields = [st_flds['predir'], st_flds['name'], st_flds['sufdir'], st_flds['type'], 'FULL_STREET']
        with arcpy.da.UpdateCursor(working, fields) as cursor:
            print("Looping through rows in roads FC ...")
            for row in cursor:
                if row[0] is None: row[0] = ''
                if row[1] is None: row[1] = ''
                if row[2] is None: row[2] = ''
                if row[3] is None: row[3] = ''
                parts = [row[0], row[1], row[2], row[3]]
                row[4] = " ".join(parts)
                row[4] = row[4].strip()
                row[4] = row[4].replace("  ", " ").replace("  ", " ").replace("  ", " ")
    #            print(f"New value for {fields[4]} is: {row[4]}")
                update_count += 1
                cursor.updateRow(row)
    print(f"Total count of updates: {update_count}")
            
            
def check_nearby_roads(pts, add_flds, streets, st_flds, gdb):
    """
    Function performs near table analysis to find 8 closest roads w/i 400m of each address point.
    It then uses pandas dataframes to join address point and street attributes to near table.
    Calls 'logic_checks' function to compare address point and street attributes.
    This searches for address point street names that match near street segment names.
    Then, the house number is checked to ensure if falls w/i address range of nearby street segment.
    Based on appropriate results, Notes field is populated with one of the following:
        - 'good address point'
        - 'near street found, but address range mismatch'
        - 'near street not found'
    Results are exported to 'neartable_final.csv', which can later be joined back to the
    address points layer using the 'IN_FID' field to update the 'Notes' field in a FC.
    """
    func_start_time = time.time()
    # Need to make a layer from working address points feature class here
    arcpy.MakeFeatureLayer_management(pts, "temp_pts")
    result = arcpy.GetCount_management("temp_pts")
    total = int(result.getOutput(0))
    print(f"temp_pts layer feature count: {total}")

    # Create table name (in memory) for neartable
    neartable = 'in_memory\\near_table'
    # Perform near table analysis
    print("Generating near table ...")
    near_start_time = time.time()
    arcpy.GenerateNearTable_analysis ("temp_pts", streets, neartable, '400 Meters', 'NO_LOCATION', 'NO_ANGLE', 'ALL', 8, 'GEODESIC')
    print("Time elapsed generating near table: {:.2f}s".format(time.time() - near_start_time))
    print(f"Number of rows in near table: {arcpy.GetCount_management(neartable)}")
    
    # Convert neartable to pandas dataframe
    neartable_arr = arcpy.da.TableToNumPyArray(neartable, '*')
    near_df = pd.DataFrame(data = neartable_arr)
    print(near_df.head(5).to_string())
    
    # Convert address points to pandas dataframe
    keep_addpt_fields = ['OBJECTID', add_flds['addnum'], 'full_street', 'Notes']
    addpts_arr = arcpy.da.FeatureClassToNumPyArray(pts, keep_addpt_fields)
    addpts_df = pd.DataFrame(data = addpts_arr)
    print(addpts_df.head(5).to_string())
    
    # Convert roads to pandas dataframe
    keep_street_fields = ['OBJECTID', st_flds['l_f_add'], st_flds['l_t_add'],
                          st_flds['r_f_add'], st_flds['r_t_add'], 'FULL_STREET']
    streets_arr = arcpy.da.FeatureClassToNumPyArray(streets, keep_street_fields)
    streets_df = pd.DataFrame(data = streets_arr)
    print(streets_df.head(5).to_string())
    
    # Join address points to near table
    join1_df = near_df.join(addpts_df.set_index('OBJECTID'), on='IN_FID')
    print(join1_df.head(5).to_string())
    # path = r'C:\E911\StGeorgeDispatch\Addpts_working_folder\stgeorge_neartable_join1.csv'
    path = os.path.join(work_dir, data_name + '_neartable_join1.csv')
    join1_df.to_csv(path)
    
    # Join streets to near table
    join2_df = join1_df.join(streets_df.set_index('OBJECTID'), on='NEAR_FID')
    print(join2_df.head(5).to_string())
    # path = r'C:\E911\StGeorgeDispatch\Addpts_working_folder\stgeorge_neartable_join2.csv'
    path = os.path.join(work_dir, data_name + '_neartable_join2.csv')
    join2_df.to_csv(path)
    
    # Apply logic_checks function to rows (axis=1) and output new df as CSV
    print("Starting logic checks ...")
    logic_start_time = time.time()
    near_df_updated = join2_df.progress_apply(logic_checks, axis=1, args=(add_flds, st_flds))
    print("Time elapsed in 'logic checks': {:.2f}s".format(time.time() - logic_start_time))
    # path = r'C:\E911\StGeorgeDispatch\Addpts_working_folder\neartable_updated.csv'
    path = os.path.join(work_dir, data_name + '_neartable_updated.csv')
    near_df_updated.to_csv(path)
    
    # Separate rows with a good nearby street into a separate dataframe
    is_goodstreet = near_df_updated['goodstreet'] == True      # Create indexes
    # Grab rows with good streets, sort by near rank from near table, remove address point duplicates
    # This preserves the only the record with the nearest good street to the address point
#    goodstreets_df = near_df_updated[is_goodstreet].sort_values('NEAR_RANK').drop_duplicates('IN_FID')
    goodstreets_df = near_df_updated[is_goodstreet].sort_values('NEAR_RANK')
    
    # Separate rows with no good nearby street into a separate dataframe
    not_goodstreet = near_df_updated['goodstreet'] == False    # Create indexes
    # Grab rows with bad streets, sort by near rank from near table, remove address point duplicates
    # This preserves the only the record with the nearest bad street to the address point
#    badstreets_df = near_df_updated[not_goodstreet].sort_values('NEAR_RANK').drop_duplicates('IN_FID')
    badstreets_df = near_df_updated[not_goodstreet].sort_values('NEAR_RANK')
    
    # Combine good and bad street dataframes, sort so good streets are at the top, then remove duplicates of address points
    # If a good streets are found, nearest one will be used; otherwise nearest bad street will be used ("near street not found")
#    filtered_df = goodstreets_df.append(badstreets_df).sort_values('goodstreet', ascending=False).drop_duplicates('IN_FID')
    # Sort by multiple columns (goodstreet, then goodnum) to ensure 2nd nearest street with good num will get used
#    filtered_df = goodstreets_df.append(badstreets_df).sort_values(['goodstreet', 'goodnum'], ascending=False).drop_duplicates('IN_FID')
    filtered_df = goodstreets_df.append(badstreets_df).sort_values(['IN_FID','goodstreet', 'goodnum', 'edit_dist', 'NEAR_DIST'],
                                       ascending=[True,False, False, True, True])
    out_name = os.path.join(work_dir, data_name + '_neartable_all.csv')
    filtered_df.to_csv(out_name)
    # Re-sort data frame on address point ID for final data set
    final_df = filtered_df.drop_duplicates('IN_FID')
    # path = r'C:\E911\StGeorgeDispatch\Addpts_working_folder\stgeorge_neartable_final.csv'
    path = os.path.join(work_dir, data_name + '_neartable_final.csv')
    final_df.to_csv(path)
    
#    # Testing best method to sort data to resturn best candidate for non-matches
#    test_df = goodstreets_df.append(badstreets_df).sort_values(['IN_FID','goodstreet', 'goodnum', 'edit_dist', 'NEAR_DIST'], ascending=[True,False, False, True, True])
#    test_df.to_csv(r'C:\E911\StGeorgeDispatch\Addpts_working_folder\stgeorge_neartable_test_edit.csv')
    
    # Create new dataframe that will be used to join to address point feature class with arcpy
    join_df = final_df[['IN_FID', 'Notes', 'edit_dist', 'NEAR_DIST', 'NEAR_RANK']]
    # Rename 'Notes' column to 'Notes_near' -- prevents conflict with 'Notes' field already in FC table
    join_df.columns = ['IN_FID', 'Notes_near', 'edit_dist', 'NEAR_DIST', 'NEAR_RANK']
    # join_path = r'C:\E911\StGeorgeDispatch\Addpts_working_folder\stgeorge_neartable_join.csv'
    join_path = os.path.join(work_dir, data_name + '_neartable_join.csv')
    join_df.to_csv(join_path)
        
    # Convert CSV output into table and join to working address points FC
    env.workspace = gdb
    env.qualifiedFieldNames = False
    if arcpy.Exists("neartable_join"):
        arcpy.Delete_management("neartable_join")
    arcpy.TableToTable_conversion(join_path, gdb, "neartable_join")
    joined_table = arcpy.AddJoin_management(pts, "OBJECTID", "neartable_join", "IN_FID")
    if arcpy.Exists(pts + "_final"):
        arcpy.Delete_management(pts + "_final")
    # Copy joined table to "_final" feature class
    # This is a copy of the address points feature class with new joined fields
    arcpy.CopyFeatures_management(joined_table, pts + "_final")
                                                          
    # Update 'Notes' field in working address points with joined table notes
    # ArcPy makes a mess of the field names after the join, so we need to make
    # sure the proper fields are pulled and updated
    fields = ['Notes', 'Notes_near']
    with arcpy.da.UpdateCursor(pts + "_final", fields) as cursor:
        print(f"Looping through rows in {os.path.basename(pts) + '_final'} to update 'Notes' field ...")
        for row in cursor:
            # Only update 'Notes' field if joined 'Near_notes' not null
            if row[1] is not None:
                if len(row[1]) > 0:
                    row[0] = row[1]
            cursor.updateRow(row)
                                 
    print("Time elapsed in 'check_nearby_roads' function: {:.2f}s".format(time.time() - func_start_time))
    
    
def logic_checks(row, a_flds, s_flds):
    """
    Function calculates new values for 'Notes' field by comparing address
    point to nearby roads' full street name and address range
    """
    goodstreet = False
    goodnum = False
    if row['full_street'] == row['FULL_STREET']:
        goodstreet = True
        if (int(row[a_flds['addnum']].split()[0]) >= row[s_flds['l_f_add']] and int(row[a_flds['addnum']].split()[0]) <= row[s_flds['l_t_add']]) or (
                int(row[a_flds['addnum']].split()[0]) >= row[s_flds['r_f_add']] and int(row[a_flds['addnum']].split()[0]) <= row[s_flds['r_t_add']]):
            goodnum = True
    # Update Notes field based on if street and number are good from near analysis
    if goodstreet and goodnum:
        row['Notes'] = 'good address point'
    elif goodstreet and not goodnum:
        row['Notes'] = 'near street found, but address range mismatch'
    elif not goodstreet:
        row['Notes'] = 'near street not found'
    row['goodstreet'] = goodstreet
    row['goodnum'] = goodnum
    row['edit_dist'] = Lv.distance(row['full_street'], row['FULL_STREET'])
    # Check edit distance for roads that might have typos, predir, or sufdir errors
    if row['Notes'] == 'near street not found' and row['edit_dist'] in (1, 2):
        row['Notes'] = 'no near st: possible typo, predir, or sufdir error'
    # Check for likely predir/sufdir errors: road nearly matches, range is good
    # Replace needed in logic to catch potential range in address number (e.g., '188-194')
    if row['Notes'] == 'no near st: possible typo, predir or sufdir error':
        if (int(row[a_flds['addnum']].replace('-', ' ').split()[0]) >= row[s_flds['l_f_add']] and int(row[a_flds['addnum']].replace('-', ' ').split()[0]) <= row[s_flds['l_t_add']]) or (
                int(row[a_flds['addnum']].replace('-', ' ').split()[0]) >= row[s_flds['r_f_add']] and int(row[a_flds['addnum']].replace('-', ' ').split()[0]) <= row[s_flds['r_t_add']]):
            goodnum = True
            row['Notes'] = 'no near st: likely predir or sufdir error'
            row['goodnum'] = goodnum
    # Check for a good house number regardless of street name match or condition
    if (int(row[a_flds['addnum']].replace('-', ' ').split()[0]) >= row[s_flds['l_f_add']] and int(row[a_flds['addnum']].replace('-', ' ').split()[0]) <= row[s_flds['l_t_add']]) or (
            int(row[a_flds['addnum']].replace('-', ' ').split()[0]) >= row[s_flds['r_f_add']] and int(row[a_flds['addnum']].replace('-', ' ').split()[0]) <= row[s_flds['r_t_add']]):
        goodnum = True
        row['goodnum'] = goodnum
    return row
    

##########################
#  Call Functions Below  #
##########################
if address_parts:
    calc_street_addpts(working_addpts, addpt_fields)
else:
    calc_street_addpts_fulladd(working_addpts, fulladd_field)
        
calc_street_roads(working_roads, street_fields)


arcpy.Delete_management("temp_pts")
arcpy.Delete_management('in_memory\\near_table')
check_nearby_roads(working_addpts, addpt_fields, working_roads, street_fields, working_db)


############################
#  Generate Plots & Stats  #
############################
print("Generating a few plots and stats ...")

# Plot histogram of Edit Distances
print("Creating edit distance histogram ...")
df = pd.read_csv(os.path.join(work_dir, data_name + '_neartable_final.csv'))
plt.figure(figsize=(6,4))
plt.hist(df['edit_dist'], bins = np.arange(0, df['edit_dist'].max(), 1)-0.5, color='red', edgecolor='black')
plt.xticks(np.arange(0, df['edit_dist'].max(), 2))
plt.title('Address/Street Edit Distance Histogram')
plt.xlabel('Edit Distance')
plt.ylabel('Count')
plt.show()

df['edit_dist'].max()

# Plot bar chart of Notes column
print("Creating notes bar chart ...")
plt.figure(figsize=(6,4))
plt.hist(df['Notes'], color='lightblue', edgecolor='black')
# plt.xticks(np.arange(0, df['Notes'].max(), 2))
plt.xticks(rotation='vertical')
plt.title('Address Point Categories')
plt.xlabel('Category')
plt.ylabel('Count')
plt.show()

print(df.groupby('Notes').count())

print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print(f"The script end time is {readable_end}")
print("Time elapsed: {:.2f}s".format(time.time() - start_time))