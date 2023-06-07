# Spillman
 - The scripts in this repository are used to stage, clean, and prepare Spillman data for Utah PSAPs
 - Each PSAP has its own folder with scripts to process and prep data for that location
 - **There are variables in each script will need to be updated to point to local data sources, connection files, etc.**

 ## Overview of common scripts
 - `{psap_name}_copy_update_needs.py`
   - Script that projects a list of data layers from the WGS84 geodatabase into UTM 12N in the staging geodatabase for working on an update.  This ensures the layers for the update are created from the latest in-use data. Output feature classes are controlled by the list or dictionary in the script and have `_update_{yyyymmdd}` appended on the end of their name.
- `{psap_name}_Road_Finder.py`
   - Script that searches for new roads from SGID.TRANSPORTATION.Roads (or optionally, a county's raw roads layer) that are not in the current Spillman streets layer (`current_streets` variable). A definition query filters the search down to counties relevent for the specific PSAP.  The output feature class (`SGID_roads_to_review_{yyyymmdd}`) only contains roads whose centroid falls outside of a 10m buffer around the existing Spillman roads.
- `{psap_name}_road_calculations.py`
   - Script that calculates specific fields in the Spillman roads layer and converts blanks to NULLs. (ex: STREET, JoinID, alias fields, etc.)
- `{psap_name}_check_for_new_addpts.py`
   - Script that searches for new address points from SGID.LOCATION.AddressPoints (or optionally, a county's raw address points layer)
   - Compares possible new points to current address points
      - Checks for duplicates based on the full address
      - Checks for likely unit/spatial duplicate if new point is within 5m of an existing point
   - Checks up to 10 nearby roads within 800m of a new point
      - To see if the street names match between the road and address point
      - To see if the house number fits within the roads address range
   - Categories each address point into one of the following groups in the `Notes` field:
      - 'good address point' - new and matches to a street segment
      - 'name duplicate' - the full address already exists
      - 'likely unit or spatial duplicate' - w/i 5m of exisiting addpt
      - 'near street found, but address range mismatch' - the street name matches a road segment, but the address range doesn't
      - 'no near st: possible typo predir or sufdir error' - nearly-matching street with an edit distance of 1 or 2 was found
      - 'no near st: likely predir or sufdir error' - nearly-matching street with an edit distance of 1 or 2 was found and the house number correctly falls within the nearby segments address range
      - 'near street not found' - a matching street wasn't found w/i 800m
      - 'not name duplicate' - catchall if the full address doesn't already exist, but the point didn't fall into another category

- `{psap_name}_addpts_calculations.py`
   - Script that calculates specific fields in the Spillman address points layer and converts blanks to NULLs (ex: STREET, Label, JoinID, etc.)
- `Spillman_classic_{psap_name}_prep.py`
   - Script to prep data for Spillman Classic. Creates new working copies of geodatabases, calculates `STREET` and alias fields on streets layer, cleans up data.  Creates AddressPoints_CAD layer by removing unit addresses (if necessary). Copies TBZONES table to WGS84 geodatabse, projects data layers to WGS84, appends streets in buffer to `Streets_All` (if necessary).  Sets attributes to NULL that will populated from polygon data using the Spillman Toolbar.
