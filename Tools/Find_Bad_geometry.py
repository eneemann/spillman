import arcpy
from arcpy import env
import os
import time

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script start time is {}".format(readable_start))

database = r"C:\E911\MillardCo\MillardCo_UTM.gdb"
# wgs84_db = r"C:\E911\StGeorgeDispatch\StGeorgeDispatch_WGS84.gdb"
# utm_db = r"C:\Users\eneemann\Desktop\Neemann\Spillman\TestData\MillardCo\TEST_MillardCo_UTM.gdb"
# wgs84_db = r"C:\Users\eneemann\Desktop\Neemann\Spillman\TestData\MillardCo\TEST_MIllard_Co_WGS84.gdb"
# env.workspace = r"C:\Users\eneemann\Desktop\Neemann\Spillman\MillardCo"
env.workspace = database

fclist = arcpy.ListFeatureClasses()

#fc_layer = "Streets"
#
#fields = arcpy.ListFields(fc_layer)
#
#for field in fields:
#    print("{0} is a type of {1} with a length of {2}"
#          .format(field.name, field.type, field.length))


###############
#  Functions  #
###############


def find_bad_geom(fc):
#    update_count = 0
#    flist = ['SHAPE@XY', 'OBJECTID']  # for points
#    flist = ['Shape', 'OBJECTID']  # for polylines/polygons
    flist = ['Shape', 'OID@']  # for polylines/polygons
    with arcpy.da.SearchCursor(fc, flist) as cursor:
        print("Looping through rows in {}...".format(arcpy.Describe(fc).name))
        for row in cursor:
            # print row
            if row[0][0] == None or row[0][1] == None:
                print(row)

##########################
#  Call Functions Below  #
##########################

for fc in fclist:
    find_bad_geom(fc)

print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))










