# -*- coding: utf-8 -*-
"""
Created on Wed Sep 30 08:24:17 2020
@author: eneemann
Exploring the state's ALI data for San Juan county

30 Sep 2020: first version of code (EMN)
"""

import arcpy
from arcpy import env
import os
import time
import pandas as pd
import numpy as np
from Levenshtein import StringMatcher as Lv
from matplotlib import pyplot as plt
import re
import timeit
import csv
from tqdm import tqdm

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script start time is {}".format(readable_start))

tqdm.pandas()
today = time.strftime("%Y%m%d")

work_dir = r'C:\E911\1 - Utah ALI Data'
ali_csv = os.path.join(work_dir, 'ali_out.csv')
city_file = os.path.join(work_dir, 'cities.txt')
quads_file = os.path.join(work_dir, 'addquads.txt')
places_file = os.path.join(work_dir, 'all_places.txt')
bad_file = os.path.join(work_dir, 'bad_cities.txt')
not_found = os.path.join(work_dir, 'not_found.txt')
uni_file = os.path.join(work_dir, 'ali_unique_addresses.csv')

cities = []
with open(city_file, "r+") as file:
    city_lines = file.readlines()
    for line in city_lines:
        cities.append(line.upper())

cities = [x.replace(' MT', '').strip() for x in cities]

quads = []
with open(quads_file, "r+") as file2:
    all_quads = file2.readlines()
    for item in all_quads:
        quads.append(item.upper().strip())
    
unique_quads = set(quads)

all_cities = list(set(cities + list(unique_quads)))

all_places = []
with open(places_file, "r+") as placefile:
    allplaces = placefile.readlines()
    for item in allplaces:
        all_places.append(item.upper().strip())

# Pad with leading space and remove duplicates
all_places = list(set(all_places))
all_places = [' ' + x for x in all_places]


col_names = ['FUNCTION CODE', 'TELEPHONE NUMBER', 'ADDRESS',
            'CITY', 'STATE', 'COMMUNITY']

# # ali = pd.read_csv(ali_file, sep=' ', engine='python', header=None, names=col_names)
ali = pd.read_csv(ali_csv)


print(ali.shape)

unique = ali.drop_duplicates(subset=['ADDRESS', 'CITY'], keep='first')
print(unique.shape)
unique.to_csv(os.path.join(work_dir, 'ali_unique_addresses.csv'))


sj_cities = ['ANETH', 'BLANDING', 'BLUFF', 'DEER CANYON', 'EASTLAND', 'FRY CANYON', 'HALLS CROSSING',
             'LA SAL', 'LA SAL JCT', 'LA SAL JUNCTION', 'MEXICAN HAT', 'MONTEZUMA CREEK', 'MONTICELLO', 'OLJATO',
             'SUMMIT POINT', 'UCOLO', 'WHITE MESA']

sj = unique[unique.CITY.isin(sj_cities)]
sj.to_csv(os.path.join(work_dir, 'ali_SanJuan_addresses.csv'))



temp = unique.head(100)
# temp = temp.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
unique_cities = ali.drop_duplicates('CITY', keep='first')
city_list = list(unique_cities.CITY)


with open(bad_file, "w", newline='') as bad:
    for item in city_list:
        if item in all_cities:
            continue
        else:
            # print(f'Not in all_cities list:    {item}')
            bad.write(f'Not in all_cities list:    {item}\n')
            

uni = pd.read_csv(os.path.join(work_dir, 'ali_unique_addresses.csv'))

dirs = ['NORTH', 'SOUTH', 'EAST', 'WEST']

def count_dirs(row):
    dir_count = 0
    for d in dirs:
        if d in row['ADDRESS']:
            temp_ct = row['ADDRESS'].count(d)
            dir_count += temp_ct
            
    row['DIR_COUNT'] = dir_count
    
    return row
            

uni = uni.progress_apply(count_dirs, axis=1)

uni.to_csv(os.path.join(work_dir, 'unique_address_dirs.csv'))

print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))

