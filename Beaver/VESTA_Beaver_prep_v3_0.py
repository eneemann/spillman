# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 15:13:41 2019

@author: eneemann

EMN: On 4 Apr 2019, created script to build Beaver County VESTA data.  Includes
adding data from surrounding counties for several feature classes.
"""

import arcpy
from arcpy import env
import os
import time

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script start time is {}".format(readable_start))

utm_db = r"C:\E911\Beaver Co\Beaver_Spillman_UTM.gdb"
wgs84_db = r"C:\E911\Beaver Co\Beaver_Spillman_WGS84.gdb"
#wgs84_db = r"C:\E911\Beaver Co_TEST\Beaver_Spillman_WGS84.gdb"
staging_db = r"C:\E911\Beaver Co\Beaver_VESTA_staging.gdb"
vesta_db = r"C:\E911\Beaver Co\Beaver_VESTA_final.gdb"
SGID = r"C:\Users\eneemann\AppData\Roaming\ESRI\ArcGISPro\Favorites\sgid.agrc.utah.gov.sde"

env.workspace = utm_db
fc_layer = "Streets"
streets_fc_utm = os.path.join(utm_db, fc_layer)
streets_cad_wgs84 = os.path.join(wgs84_db, "Streets_CAD")

###############
#  Main code  #
###############

# Add external addpts to address points layer
addpts = os.path.join(staging_db, "AddressPoints")
SGID_addpts = os.path.join(SGID, "AddressPoints")


def export_shapefiles_select_fields(fc, folder, field_list):
    print("Output folder is: {}".format(folder))
    print("Exporting {} to shapefile with the following fields:".format(fc))
    for field in field_list:
        print(field)
    env.workspace = wgs84_db
    infile = os.path.join(wgs84_db, fc)
    d = {}                              # create dictionary to hold FieldMap objects
    fms = arcpy.FieldMappings()         # create FieldMappings objects
    for index, field in enumerate(field_list):
        d["fm{}".format(index)] = arcpy.FieldMap()                              # create FieldMap object in dictionary
        d["fm{}".format(index)].addInputField(infile, field)                    # add input field
        # add output field
        d["fname{}".format(index)] = d["fm{}".format(index)].outputField
        d["fname{}".format(index)].name = field
        d["fm{}".format(index)].outputField = d["fname{}".format(index)]
        fms.addFieldMap(d["fm{}".format(index)])                                # add FieldMap to FieldMappings object
    arcpy.FeatureClassToFeatureClass_conversion(fc, folder, fc, field_mapping=fms)


def export_shapefiles_select_fields_rename(fc, folder, field_list, outname):
    print("Output folder is: {}".format(folder))
    print("Exporting {} to shapefile with the following fields:".format(fc))
    for field in field_list:
        print(field)
    env.workspace = wgs84_db
    infile = os.path.join(wgs84_db, fc)
    d = {}                              # create dictionary to hold FieldMap objects
    fms = arcpy.FieldMappings()         # create FieldMappings objects
    for index, field in enumerate(field_list):
        d["fm{}".format(index)] = arcpy.FieldMap()                              # create FieldMap object in dictionary
        d["fm{}".format(index)].addInputField(infile, field)                    # add input field
        # add output field
        d["fname{}".format(index)] = d["fm{}".format(index)].outputField
        d["fname{}".format(index)].name = field
        d["fm{}".format(index)].outputField = d["fname{}".format(index)]
        fms.addFieldMap(d["fm{}".format(index)])                                # add FieldMap to FieldMappings object
    arcpy.FeatureClassToFeatureClass_conversion(fc, folder, outname, field_mapping=fms)

#######################################
#  Prep variables for function calls  #
#######################################

WGS84_files_to_delete = ["AddressPoints", "AddressPoints_CAD", "Beaver_County", "CityCodes", "CommonPlaces", "CommonPlaces_Exits",
                         "CommonPlaces_All", "CommonPlaces_MP", "CommonPlaces_RRMP", "CommonPlaces_RRX", "Ems_zone",
                         "Fire_zone", "Law_area", "Law_zone", "Streets", "Streets_CAD", "tbzones"]
UTM_files_to_delete = ["AddressPoints_CAD", "Streets_CAD", "CommonPlaces_All"]

# Create variables for address points
address_pts = os.path.join(utm_db, "AddressPoints")

# Create variables for common places
commonplaces = os.path.join(utm_db, "CommonPlaces")

# Create variable for tbzones
tbzones = os.path.join(utm_db, "tbzones")

# Create variables for projecting
FCs_to_project = ["AddressPoints", "Beaver_County", "CityCodes", "CommonPlaces", "CommonPlaces_All", "CommonPlaces_Exits", "CommonPlaces_MP",
                  "CommonPlaces_RRMP", "CommonPlaces_RRX", "Ems_zone", "Fire_zone", "Law_area", "Law_zone", "Streets", "Streets_CAD",
                  "Communities", "railroads"]

######################################################################################################################
#  There are two options for exporting shapefiles.  Choose desired option and comment out the other before running:  #
#  Option 1: Exports ALL FCs to shapefiles in bulk and includes all fields in the output                             #
#  Option 2: Individually exports each FC to shapefile, trims output down to specified fields                        #
######################################################################################################################

# Create variables for shapefiles
FCs_to_export = FCs_to_project
today = time.strftime("%Y%m%d")
spill_dir = r"C:\E911\Beaver Co\0 Shapefiles"
spillman_folder = "Spillman_Shapefiles_Beaver_" + today
out_folder_spillman = os.path.join(spill_dir, spillman_folder)
vesta_dir = r"C:\E911\Beaver Co\0 VESTA Files"
vesta_folder = "VESTA_Shapefiles_Beaver_" + today
out_folder_vesta = os.path.join(vesta_dir, vesta_folder)

# Comment out this line if the folder already exists (like if code was already run once today)
os.mkdir(out_folder_spillman)
os.mkdir(out_folder_vesta)

# Option 1: Exports ALL FCs to shapefiles in bulk and includes all fields in the output
# export_shapefiles_all_fields(FCs_to_export, out_folder)
# Option 2: Individually exports each FC to shapefile, trims output down to specified fields
# -----> See last set of function calls

addpt_fields = ["FullAdd", "LABEL"]
commplc_fields = ["ALIAS", "ADDRESS"]
exit_fields = ["ALIAS", "ADDRESS"]
milepost_fields = ["ALIAS", "ADDRESS"]
rrmp_fields = ["ALIAS", "ADDRESS"]
rrx_fields = ["ALIAS", "ADDRESS"]
street_fields = ["L_F_ADD", "L_T_ADD", "R_F_ADD", "R_T_ADD", "ZIPLEFT", "ZIPRIGHT", "STREET", "L_CITYCD", "R_CITYCD"]
ezone_fields = ["ZONEDESC", "ZONEID"]
fzone_fields = ["ZONEDESC", "ZONEID"]
larea_fields = ["ZONEDESC", "ZONEID"]
lzone_fields = ["ZONEDESC", "ZONEID"]
citycd_fields = ["ZONEDESC", "CITYCD"]
muni_fields = ["NAME", "SHORTDESC", "POPLASTCENSUS"]
railroad_fields = ["LABEL"]
river_fields = ["GNIS_Name", "LengthKM"]
trail_fields = ["PrimaryName","DesignatedUses"]
gnis_fields = ["FEATURE_NAME", "FEATURE_CLASS", "ELEV_IN_FT"]
parcel_fields = ["Label", "NAME", "ACRES"]
county_fields = ["NAME"]
# other_fields = ["NAME", "CITYCD", "Length", "Area"]

# VESTA Shapefile field lists
vesta_addpt_fields = ["FullAdd", "AddNum", "PrefixDir", "StreetName", "StreetType", "SuffixDir", "UnitID", "STREET", "X",
                     "Y"] #, "ZipCode", "State", "COMM"]
vesta_commplc_fields = ["ALIAS", "CITYCD", "STREET", "BEGNUMB", "ENDNUMB", "FULL_ADDRE", "COMM"]
vesta_street_fields = ["CARTOCODE", "L_F_ADD", "L_T_ADD", "R_F_ADD", "R_T_ADD", "PREDIR", "STREETNAME", "STREETTYPE",
                      "SUFDIR", "ALIAS1", "ALIAS1TYPE", "ALIAS2", "ALIAS2TYPE", "ACSALIAS", "ACSNAME", "ACSSUF",
                      "ZIPLEFT", "ZIPRIGHT", "STREET", "COMM_LEFT", "COMM_RIGHT", "Shape_Length"]
vesta_muni_fields = ["NAME", "POPLASTCENSUS", "CITYCD"]
# VESTA Shapefile outnames
vesta_addpt_out = "AddressPoints"
vesta_commplc_out = "CommonPlaces"
vesta_street_out = "Streets"
vesta_muni_out = "Municipalities"
# Additional VESTA Shapefiles to export
vesta_to_export = ["Ems_zone", "Fire_zone", "Law_zone", "Communities"]

##########################
#  Call Functions Below  #
##########################

#################################################################

# Spillman Shapefiles Export
export_shapefiles_select_fields("AddressPoints", out_folder_spillman, addpt_fields)
export_shapefiles_select_fields("CommonPlaces", out_folder_spillman, commplc_fields)
export_shapefiles_select_fields("CommonPlaces_Exits", out_folder_spillman, exit_fields)
export_shapefiles_select_fields("CommonPlaces_MP", out_folder_spillman, milepost_fields)
export_shapefiles_select_fields("CommonPlaces_RRMP", out_folder_spillman, rrmp_fields)
export_shapefiles_select_fields("CommonPlaces_RRX", out_folder_spillman, rrx_fields)
export_shapefiles_select_fields("Streets", out_folder_spillman, street_fields)
export_shapefiles_select_fields("Ems_zone", out_folder_spillman, ezone_fields)
export_shapefiles_select_fields("Fire_zone", out_folder_spillman, fzone_fields)
export_shapefiles_select_fields("Law_zone", out_folder_spillman, lzone_fields)
export_shapefiles_select_fields("Law_area", out_folder_spillman, larea_fields)
export_shapefiles_select_fields("CityCodes", out_folder_spillman, citycd_fields)
export_shapefiles_select_fields("Municipalities", out_folder_spillman, muni_fields)
export_shapefiles_select_fields("railroads", out_folder_spillman, railroad_fields)
export_shapefiles_select_fields("Rivers", out_folder_spillman, river_fields)
export_shapefiles_select_fields("RecreationTrails", out_folder_spillman, trail_fields)
export_shapefiles_select_fields("GNIS_PlaceNames", out_folder_spillman, gnis_fields)
export_shapefiles_select_fields("Parcels", out_folder_spillman, parcel_fields)
export_shapefiles_select_fields("Beaver_County", out_folder_spillman, county_fields)

# VESTA Shapefiles Export
#export_shapefiles_select_fields_rename("AddressPoints_CAD", out_folder_vesta, vesta_addpt_fields, vesta_addpt_out)
#export_shapefiles_select_fields_rename("CommonPlaces", out_folder_vesta, vesta_commplc_fields, vesta_commplc_out)
#export_shapefiles_select_fields_rename("Streets", out_folder_vesta, vesta_street_fields, vesta_street_out)
#export_shapefiles_select_fields_rename("Municipalities", out_folder_vesta, vesta_muni_fields, vesta_muni_out)
#export_shapefiles_all_fields(vesta_to_export, out_folder_vesta)
#env.workspace = out_folder_vesta
#arcpy.Rename_management("Communities.shp", "Communities.shp")

print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))










