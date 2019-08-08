# -*- coding: utf-8 -*-
'''
Created on Thu Aug 8 13:54:56 2019
@author: eneemann
Script to identify empty geometries in a feature class with ArcPy
'''

#import os
import time
import arcpy
from arcpy import env

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
print('The script start time is {}'.format(readable_start))

# Get list of feature classes in a geodatabase
# database = r'C:\E911\Box Elder CO\BoxElder_Spillman_WGS84.gdb'
database = r'C:\E911\StGeorgeDispatch_TEST\Bad_Geometries_TEST.gdb'
env.workspace = database
fclist = arcpy.ListFeatureClasses()


               
###############
#  Functions  #
###############


def delete_empty_geom(db, lyr):
    del_count = 0
    fields = ['OID@', 'Shape', 'SHAPE@']  # for point, polylines, or polygons
    with arcpy.da.UpdateCursor(lyr, fields) as Ucursor:
        print("Looping through rows in '{}' ...".format(lyr))
        for row in Ucursor:
            bad_geom = False
            # Check if geometry object is null
            if row[2] is None:
                print("     OID {} has null (None) geometry".format(row[0]))
                bad_geom = True
            # Check shape centroid has a null coordinate
            elif row[1][0] == None or row[1][1] == None:
                print("     OID {} has empty geometry".format(row[0]))
                bad_geom = True
            
            if bad_geom == True:
                print("     --> Deleting OID {} ... ".format(row[0]))
                Ucursor.deleteRow()
                del_count += 1
    print("Total number of rows deleted: {}".format(del_count))


##########################
#  Call Functions Below  #
##########################

if __name__ == '__main__':
    for fc in sorted(fclist):
        delete_empty_geom(database, fc)

print('Script shutting down ...')
# Stop timer and print end time in UTC
readable_end = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
print('The script end time is {}'.format(readable_end))
print('Time elapsed: {:.2f}s'.format(time.time() - start_time))