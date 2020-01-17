# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 16:03:07 2020
@author: eneemann
Script to detect possible address points by comparing new data to current data

Need to call get_SGID_addpts function first, then comment out the call and run the script
"""

import arcpy
from arcpy import env
import os
import time
import pandas as pd
import numpy as np
from Levenshtein import StringMatcher as Lv
from matplotlib import pyplot as plt

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script start time is {}".format(readable_start))

weber_db = r"C:\E911\WeberArea\Staging103\WeberSGB.gdb"
staging_db = r"C:\E911\WeberArea\Staging103\Weber_Staging.gdb"
env.workspace = weber_db
env.overwriteOutput = True

weber_streets = os.path.join(weber_db, "Streets_Map")
weber_addpts = "AddressPoints_SGB_20200116"    # Point to current addpts in staging_db
current_addpts = os.path.join(staging_db, weber_addpts)

today = time.strftime("%Y%m%d")
new_addpts = "AddressPoints_SGID_export_" + today
#new_addpts = "Addpts_more_to_test_20190906"
#new_addpts = "AddressPoints_SGID_export_20190408"    # Use if SGID data was already exported
possible_addpts = os.path.join(staging_db, new_addpts)


# Copy current address points into a working FC
working_addpts = os.path.join(staging_db, "zzz_AddPts_new_TEST_working_" + today)
arcpy.CopyFeatures_management(possible_addpts, working_addpts)

# Add field to working FC for notes
arcpy.AddField_management(working_addpts, "notes", "TEXT", "", "", 50)
arcpy.AddField_management(working_addpts, "street", "TEXT", "", "", 50)

###############
#  Functions  #
###############

def get_SGID_addpts(out_db):
    today = time.strftime("%Y%m%d")
    SGID = r"C:\Users\eneemann\AppData\Roaming\ESRI\ArcGISPro\Favorites\agrc@opensgid@opensgid.agrc.utah.gov.sde"
    sgid_pts = os.path.join(SGID, "opensgid.location.address_points")
    new_pts = "AddressPoints_SGID_export_" + today
    if arcpy.Exists(new_pts):
        arcpy.Delete_management(new_pts)
    where_SGID = "countyid IN ('49057', '49029')"   # Weber, Morgan County
    print("Exporting SGID address points to: {}".format(new_pts))
    arcpy.FeatureClassToFeatureClass_conversion (sgid_pts, out_db, new_pts, where_SGID)


def calc_street(working):
    update_count = 0
    # Calculate "street" field where applicable
#    where_clause = "STREETNAME IS NOT NULL AND STREET IS NULL"
    fields = ['prefixdir', 'streetname', 'suffixdir', 'streettype', 'street']
    with arcpy.da.UpdateCursor(working, fields) as cursor:
        print("Looping through rows in FC ...")
        for row in cursor:
            if row[0] is None: row[0] = ''
            if row[2] is None: row[2] = ''
            if row[3] is None: row[3] = ''
            parts = [row[0], row[1], row[2], row[3]]
            row[4] = " ".join(parts)
            row[4] = row[4].lstrip().rstrip()
            row[4] = row[4].replace("  ", " ").replace("  ", " ").replace("  ", " ")
#            print "New value for {0} is: {1}".format(fields[4], row[4])
            update_count += 1
            cursor.updateRow(row)
    print("Total count of updates to {0} field: {1}".format(fields[4], update_count))


def remove_duplicates(current, possible, working):
    count = 0
    # Need to make a layer from possible address points feature class here
    arcpy.MakeFeatureLayer_management(working, "working_lyr")

    # Create list of features in the current Weber address points feature class
    current_dict = {}
    fields = ['fulladd']
    with arcpy.da.SearchCursor(current, fields) as cursor:
        print("Looping through rows in {} ...".format(current))
        for row in cursor:
            current_dict.setdefault(row[0])
    print("Total current address points: {}".format(str(len(current_dict))))

    # Loop through possible layer and select features that aren't in current Weber add pts list (avoid duplicates)
    fields = ['fulladd', 'notes']
    with arcpy.da.UpdateCursor("working_lyr", fields) as cursor:
        print("Looping through rows in {} ...".format("working_lyr"))
        for row in cursor:
            count += 1
            if row[0] not in current_dict:
                row[1] = 'not name duplicate'
            else:
                row[1] = 'name duplicate'
            cursor.updateRow(row)
            if count % 10000 == 0:
                print("'remove_duplicates' function has completed row {}".format(count))
    where_final = "notes = 'not name duplicate'"
    final_selection = arcpy.SelectLayerByAttribute_management("working_lyr", "NEW_SELECTION", where_final)
    print("Number of features in new_selection after checking duplicates is: {}"
          .format(arcpy.GetCount_management(final_selection)))

    # Write selected features out to a new FC
    non_duplicates = os.path.join(staging_db, "zzz_AddPts_NW_TEST_nodup1_" + today)
    print("Writing out non-duplicates to: {}".format(non_duplicates))
    arcpy.CopyFeatures_management("working_lyr", non_duplicates)
    return non_duplicates


def mark_near_addpts(current, possible, working):
    where_clause = "notes <> 'name duplicate'"
    # Need to make a layer from possible address points feature class here
    arcpy.MakeFeatureLayer_management(working, "working_lyr_2", where_clause)
    print("Working layer feature count: {}".format(arcpy.GetCount_management("working_lyr_2")))
    
    # Select all features within 5m of current Weber FC
    fields = ['notes']
    arcpy.SelectLayerByLocation_management("working_lyr_2", "WITHIN_A_DISTANCE_GEODESIC", current,
                                                         "5 meters", "NEW_SELECTION")
    
    with arcpy.da.UpdateCursor("working_lyr_2", fields) as cursor:
        print("Looping through rows in {} ...".format("working_lyr_2"))
        for row in cursor:
            row[0] = 'likely unit or spatial duplicate'
            cursor.updateRow(row)
            
            
def check_nearby_roads(working, streets, gdb):
    """
    Function performs near table analysis to find 5 closest roads w/i 100m of each address point.
    It then uses pandas dataframes to join address point and street attributes to near table.
    Calls 'logic_checks' function to compare address point and street attributes.
    This searches for address point street names that match near street segment names.
    Then, the house number is checked to ensure if falls w/i address range of nearby street segment.
    Based on appropriate results, notes field is populated with one of the following:
        - 'good address point'
        - 'near street found, but address range mismatch'
        - 'near street not found'
    Results are exported to 'neartable_final.csv', which can later be joined back to the
    address points layer using the 'IN_FID' field to update the 'notes' field in a FC.
    """
    func_start_time = time.time()
    # look at features that aren't name duplicates
    where_clause = "notes = 'not name duplicate'"
    # Need to make a layer from possible address points feature class here
    arcpy.MakeFeatureLayer_management(working, "working_nodups", where_clause)
    result = arcpy.GetCount_management("working_nodups")
    total = int(result.getOutput(0))
    print("Working layer feature count: {}".format(total))

    # Create table name (in memory) for neartable
    neartable = 'in_memory\\near_table'
    # Perform near table analysis
    print("Generating near table ...")
    arcpy.GenerateNearTable_analysis ("working_nodups", streets, neartable, '100 Meters', 'NO_LOCATION', 'NO_ANGLE', 'ALL', 5, 'GEODESIC')
    print("Number of rows in Near Table: {}".format(arcpy.GetCount_management(neartable)))
    
    # Convert neartable to pandas dataframe
    neartable_arr = arcpy.da.TableToNumPyArray(neartable, '*')
    near_df =pd.DataFrame(data = neartable_arr)
    print(near_df.head(5).to_string())
    
    # Convert address points to pandas dataframe
    addpt_fields = ['OID@', 'addnum', 'street', 'zipcode', 'notes']
    addpts_arr = arcpy.da.FeatureClassToNumPyArray(working, addpt_fields)
    addpts_df =pd.DataFrame(data = addpts_arr)
    print(addpts_df.head(5).to_string())
    
    # Convert roads to pandas dataframe
    street_fields = ['OID@', 'L_F_ADD', 'L_T_ADD', 'R_F_ADD', 'R_T_ADD', 'STREET']
    streets_arr = arcpy.da.FeatureClassToNumPyArray(streets, street_fields)
    streets_df =pd.DataFrame(data = streets_arr)
    print(streets_df.head(5).to_string())
    
    # Join address points to near table
    join1_df = near_df.join(addpts_df.set_index('OID@'), on='IN_FID')
    print(join1_df.head(5).to_string())
    path = r'C:\E911\WeberArea\Staging103\Addpts_working_folder\neartable_join1.csv'
    join1_df.to_csv(path)
    
    # Join streets to near table
    join2_df = join1_df.join(streets_df.set_index('OID@'), on='NEAR_FID')
    print(join2_df.head(5).to_string())
    path = r'C:\E911\WeberArea\Staging103\Addpts_working_folder\neartable_join2.csv'
    join2_df.to_csv(path)
    
    # Apply logic_checks function to rows (axis=1) and output new df as CSV
    near_df_updated = join2_df.apply(logic_checks, axis=1)
    path = r'C:\E911\WeberArea\Staging103\Addpts_working_folder\neartable_updated.csv'
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
    filtered_df.to_csv(r'C:\E911\WeberArea\Staging103\Addpts_working_folder\weber_neartable_all.csv')
    # Re-sort data frame on address point ID for final data set
    final_df = filtered_df.drop_duplicates('IN_FID')
    path = r'C:\E911\WeberArea\Staging103\Addpts_working_folder\weber_neartable_final.csv'
    final_df.to_csv(path)
    
#    # Testing best method to sort data to resturn best candidate for non-matches
#    test_df = goodstreets_df.append(badstreets_df).sort_values(['IN_FID','goodstreet', 'goodnum', 'edit_dist', 'NEAR_DIST'], ascending=[True,False, False, True, True])
#    test_df.to_csv(r'C:\E911\WeberArea\Staging103\Addpts_working_folder\weber_neartable_test_edit.csv')
    
    # Create new dataframe that will be used to join to address point feature class with arcpy
    join_df = final_df[['IN_FID', 'notes', 'edit_dist']]
    # Rename 'notes' column to 'notes_near' -- prevents conflict with 'notes' field already in FC table
    join_df.columns = ['IN_FID', 'notes_near', 'edit_dist']
    join_path = r'C:\E911\WeberArea\Staging103\Addpts_working_folder\weber_neartable_join.csv'
    join_df.to_csv(join_path)
        
    # Convert CSV output into table and join to working address points FC
    env.workspace = gdb
    env.qualifiedFieldNames = False
    if arcpy.Exists("neartable_join"):
        arcpy.Delete_management("neartable_join")
    arcpy.TableToTable_conversion(join_path, gdb, "neartable_join")
    joined_table = arcpy.AddJoin_management(working, "OBJECTID", "neartable_join", "IN_FID")
    if arcpy.Exists(working + "_final"):
        arcpy.Delete_management(working + "_final")
    # Copy joined table to "_final" feature class
    # This is a copy of the address points feature class with new joined fields
    arcpy.CopyFeatures_management(joined_table, working + "_final")
                                                          
    # Update 'notes' field in working address points with joined table notes
    # ArcPy makes a mess of the field names after the join, so we need to make
    # sure the proper fields are pulled and updated
#    field1 = os.path.basename(working) + "_notes"
#    field2 = "neartable_join" + "_notes_near"
#    fields = [field1, field2]
#    for field in fields:
#        print(field)
    fields = ['notes', 'notes_near']
    with arcpy.da.UpdateCursor(working + "_final", fields) as cursor:
        print("Looping through rows in {} to update 'notes' field ...".format(os.path.basename(working) + "_final"))
        for row in cursor:
            # Only update 'notes' field if joined 'Near_notes' not null
            if row[1] is not None:
                if len(row[1]) > 0:
                    row[0] = row[1]
            cursor.updateRow(row)
                                 
    print("Time elapsed in 'check_nearby_roads' function: {:.2f}s".format(time.time() - func_start_time))
    
    
def logic_checks(row):
    """
    Function calculates new values for 'notes' field by comparing address
    point to nearby streets' name and address range
    """
    goodstreet = False
    goodnum = False
    add_num = ''.join(i for i in row['addnum'] if i.isdigit())
    
    if add_num.isdigit():
        if row['street'] == row['STREET']:
            goodstreet = True
            if (int(add_num.split()[0]) >= row['L_F_ADD'] and int(add_num.split()[0]) <= row['L_T_ADD']) or (
                    int(add_num.split()[0]) >= row['R_F_ADD'] and int(add_num.split()[0]) <= row['R_T_ADD']):
                goodnum = True
        # Update notes field based on if street and number are good from near analysis
        if goodstreet and goodnum:
            row['notes'] = 'good address point'
        elif goodstreet and not goodnum:
            row['notes'] = 'near street found, but address range mismatch'
        elif not goodstreet:
            row['notes'] = 'near street not found'
        row['goodstreet'] = goodstreet
        row['goodnum'] = goodnum
        row['edit_dist'] = Lv.distance(row['street'], row['STREET'])
        # Check edit distance for roads that might have typos, predir, or sufdir errors
        if row['notes'] == 'near street not found' and row['edit_dist'] in (1, 2):
            row['notes'] = 'no near st: possible typo predir or sufdir error'
        # Check for likely predir/sufdir errors: road nearly matches, range is good
        # Replace needed in logic to catch potential range in address number (e.g., '188-194')
        if row['notes'] == 'no near st: possible typo predir or sufdir error':
            if (int(add_num.replace('-', ' ').split()[0]) >= row['L_F_ADD'] and int(add_num.replace('-', ' ').split()[0]) <= row['L_T_ADD']) or (
                    int(add_num.replace('-', ' ').split()[0]) >= row['R_F_ADD'] and int(add_num.replace('-', ' ').split()[0]) <= row['R_T_ADD']):
                goodnum = True
                row['notes'] = 'no near st: likely predir or sufdir error'
                row['goodnum'] = goodnum
        # Check for a good house number regardless of street name match or condition
        if (int(add_num.replace('-', ' ').split()[0]) >= row['L_F_ADD'] and int(add_num.replace('-', ' ').split()[0]) <= row['L_T_ADD']) or (
                int(add_num.replace('-', ' ').split()[0]) >= row['R_F_ADD'] and int(add_num.replace('-', ' ').split()[0]) <= row['R_T_ADD']):
            goodnum = True
            row['goodnum'] = goodnum
    
    return row
    

##########################
#  Call Functions Below  #
##########################

#section_time = time.time()
#get_SGID_addpts(staging_db)
#print("Time elapsed in 'get_SGID_addpts' function: {:.2f}s".format(time.time() - section_time))


calc_street(working_addpts)
working_nodups = remove_duplicates(current_addpts, possible_addpts, working_addpts)
print(arcpy.GetCount_management(working_nodups))
mark_near_addpts(current_addpts, possible_addpts, working_addpts)

arcpy.Delete_management("working_nodups")
arcpy.Delete_management('in_memory\\near_table')
check_nearby_roads(working_addpts, weber_streets, staging_db)


print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))


print("Creating edit distance histogram ...")
df = pd.read_csv(r'C:\E911\WeberArea\Staging103\Addpts_working_folder\weber_neartable_final.csv')
plt.figure(figsize=(6,4))
plt.hist(df['edit_dist'], bins = np.arange(0, df['edit_dist'].max(), 1)-0.5, color='red', edgecolor='black')
plt.xticks(np.arange(0, df['edit_dist'].max(), 2))
plt.title('Address/Street Edit Distance Histogram')
plt.xlabel('Edit Distance')
plt.ylabel('Count')
plt.show()