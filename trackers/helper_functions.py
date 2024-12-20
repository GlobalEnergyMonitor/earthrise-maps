from mimetypes import suffix_map
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, LineString
from shapely import wkt
import math
# import polyline
# import pygsheets
import gspread
# import xlwings
import json
from gspread.exceptions import APIError
import time
from itertools import permutations
import copy
import os
from datetime import date
import openpyxl
import xlsxwriter
from all_config import *
import re
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.styles import Alignment
import pickle


# #### useful general functions ####

# def track_missing_data(dict_list_dfs_by_map, acro, maptype):
#     for mapname, list_dfs in dict_list_dfs_by_map.items():
#         if mapname == maptype:
#             for df in list_dfs:
#                 if df['tracker-acro'].iloc[0] == acro:    
#                     # print(f'This is the current count of all units for tracker {acro} in map: {mapname}:')
#                     # print(len(df[df['tracker-acro']==acro]))
#                     # input('Check that this number aligns with the number of units in the map')
#     return 


def remove_illegal_characters(value):
    if isinstance(value, str):
        # Define a regex pattern to match illegal characters
        illegal_characters = re.compile(r'[\x00-\x1F\x7F-\x9F]')
        # Replace illegal characters with an empty string
        return illegal_characters.sub('', value)
    return value

def set_up_df(df, t_name, acro, release):
    df['tracker-official'] = t_name
    df['tracker-acro'] = acro
    df['release-date'] = release
    
    df['tracker-official'] = df['tracker-official'].fillna('')
    df = df[df['tracker-official'] != '']
    # drop empty rows
    df = df.replace('*', pd.NA).replace('Unknown', pd.NA).replace('--', pd.NA)
    print(df)
    print(len(df))
    # input('Check df length, ggit-lng turns into a string?')
    # df = df.fillna('')
    df.columns = df.columns.str.strip()  # Strip blank spaces from column names

    # if acro == 'GNPT':
    #     print(df.columns)
    #     input('check columns in GNPT')
        
    # rename df 
    renaming_dict_sel = renaming_cols_dict[acro]
    df_renamed = df.rename(columns=renaming_dict_sel) 
    df_renamed.reset_index(drop=True, inplace=True)  # Reset index in place
    # print('and look into the default dict nonsense that will help')

    return df_renamed
                
    

def split_multiple_delimiters(text, delimiters):
    regex_pattern = '|'.join(map(re.escape, delimiters))
    return re.split(regex_pattern, text)

def gspread_access_file_read_only(key, tab_list):
    """
    key = Google Sheets unique key in the URL
    title = name of the sheet you want to read
    returns a df of the sheet
    """
    gspread_creds = gspread.oauth(
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        credentials_filename=client_secret_full_path,
        # authorized_user_filename=json_token_name,
    )
    list_of_dfs = []
       # # add in an exponential backoff 

    for tab in tab_list:
        if tab == gcmt_closed_tab:
            # print(tab)
            wait_time = 5
            time.sleep(wait_time)
            gsheets = gspread_creds.open_by_key(key)
            # Access a specific tab
            spreadsheet = gsheets.worksheet(tab)

            df = pd.DataFrame(spreadsheet.get_all_records(expected_headers=[]))
            if 'Status' in df.columns:
                print('Look at GCMT closed tab status col should not be there but is?')
            else:
                df['Status'] = 'Retired'
            list_of_dfs.append(df)
        else: 
            print(tab)
            wait_time = 5
            time.sleep(wait_time)
            gsheets = gspread_creds.open_by_key(key)
            # Access a specific tab
            # print(tab)
            # input('review tab to diagnose error')
            spreadsheet = gsheets.worksheet(tab)

            df = pd.DataFrame(spreadsheet.get_all_records(expected_headers=[]))

            list_of_dfs.append(df)
    if len(list_of_dfs) > 1: 
        # df = pd.concat(list_of_dfs, sort=False).reset_index(drop=True).fillna('')
        
        df = pd.concat(list_of_dfs, sort=False).reset_index(drop=True)

    return df
 
def create_prep_file(multi_tracker_log_sheet_key, prep_file_tab): # needed_map_list
    
    if local_copy:

        with open(f'local_pkl/prep_df{iso_today_date}.pkl', 'rb') as f:
            prep_df = pickle.load(f)
    else:
        prep_df = gspread_access_file_read_only(multi_tracker_log_sheet_key, prep_file_tab)
        # Add pickle format for prep_df
        prep_df = prep_df[prep_df['official release tab name'] != ''] # skips rows at bottom
        # Convert 'gspread_tabs' and 'sample_cols' to lists
        prep_df['gspread_tabs'] = prep_df['gspread_tabs'].apply(lambda x: x.split(';'))
        # df['sample_cols'] = df['sample_cols'].apply(lambda x: x.split(';'))
        prep_df['gspread_tabs'] = prep_df['gspread_tabs'].apply(lambda lst: [s.strip() for s in lst])
        # df['sample_cols'] = df['sample_cols'].apply(lambda lst: [s.strip() for s in lst])
        prep_df['official name'] = prep_df['official release tab name']

        prep_df.set_index('official release tab name', inplace=True) # sets index on offical name
        # prep_df['tracker-acro'] = prep_df['tracker-acro']
        
        with open(f'local_pkl/prep_df{iso_today_date}.pkl', 'wb') as f:
            pickle.dump(prep_df, f)

    
    return prep_df

# # #### useful geo functions ####

def geom_to_polyline(geom):
    if geom.geom_type == 'MultiLineString':
        # Convert each LineString within the MultiLineString to a polyline
        return [polyline.encode(list(line.coords)) for line in geom.geoms] # problem TypeError: 'MultiLineString' object is not iterable
    elif geom.geom_type == 'LineString':
        return polyline.encode(list(geom.coords))
    elif geom.geom_type == 'Point':
        return Point.encode(list(geom.coords)) # maybe? 
    else:
        raise ValueError("Unsupported geometry type")


def clean_dfs(df):
    # remove uknown, *, etc
    # print(f'length of df at start of cleaned_dfs: {len(df)}')

    non_numeric_rows = []

    cleaned_df = df.copy()
    cleaned_df['Latitude'] = cleaned_df['Latitude'].astype(str)
    cleaned_df['Longitude'] = cleaned_df['Longitude'].astype(str)
    non_numeric_rows = cleaned_df[
        cleaned_df['Latitude'].str.contains(',') |
        cleaned_df['Longitude'].str.contains(',')].index.tolist()
    non_numeric_rows2 = cleaned_df[
        cleaned_df['Latitude'].str.contains('-') |
        cleaned_df['Longitude'].str.contains('-')].index.tolist()
            
    non_numeric_rows = non_numeric_rows + non_numeric_rows2 # + cleaned_df_missing
    # print(f'length of :{len(non_numeric_rows)}')
    cleaned_df = cleaned_df.drop(non_numeric_rows)
    # print("Rows to drop:", non_numeric_rows)
    # print("\nCleaned DataFrame:")
    # print(cleaned_df)
    
    # Create new DataFrames from the lists
    non_numeric_df = pd.DataFrame(non_numeric_rows)

    # print("\nNon-Numeric DataFrame:")
    # print(non_numeric_df)
    non_numeric_df.to_csv(f'{path_for_test_results}non_numeric_df_coords_{today_date}.csv')

                
    # print(f'length of df at end of cleand_dfs removed lat and long empty which is good because all point data:{len(cleaned_df)}')
    return cleaned_df

def df_to_gdf(df, geometry_col, crs='EPSG:4326'):
    # Ensure the geometry column contains valid geometries
    # gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df[geometry_col]))
    # print(crs)
    gdf = gpd.GeoDataFrame(df, geometry=geometry_col, crs=crs)

    return gdf

def gdf_to_geojson(gdf, output_file):
    gdf.to_file(output_file, driver='GeoJSON')
    # print(f"GeoJSON file saved to {output_file}")


def geojson_to_gdf(geojson_file):
    """
    convert to gdf
    """
    
    # Load GeoJSON file into a GeoDataFrame
    gdf = gpd.read_file(geojson_file)

    # get crs for final export
    crs = gdf.crs

    pipes_without_geo = gdf[gdf['geometry']==None]

    return gdf, crs



def get_standard_country_names():
    
    if local_copy:

        with open(f'local_pkl/gem_standard_country_names_{iso_today_date}.pkl', 'rb') as f:
            gem_standard_country_names = pickle.load(f)
    
    else:
        df = gspread_access_file_read_only(
            '1mtlwSJfWy1gbIwXVgpP3d6CcUEWo2OM0IvPD6yztGXI', 
            ['Countries'],
        )
        gem_standard_country_names = df['GEM Standard Country Name'].tolist()
        
        with open(f'local_pkl/gem_standard_country_names_{iso_today_date}.pkl', 'wb') as f:
            pickle.dump(gem_standard_country_names, f)
        
    
    return gem_standard_country_names

# gem_standard_country_names = get_standard_country_names()



def is_number(n):
    is_number = True
    try:
        num = float(n)
        # check for "nan" floats
        is_number = num == num   # or use `math.isnan(num)`
    except ValueError:
        is_number = False
    return is_number

def check_and_convert_int(x):
    if is_number(x):
        return int(x)
    else:
        return np.nan

def check_and_convert_float(x):
    if is_number(x):
        return float(x)
    else:
        return np.nan

def check_in_range(value, min_val, max_val):
    # doesn't handle na because already was handled
    if min_val <= value <= max_val:
         
        return value

    else:
        print('problem with coords:')
        print(f'value:{value}, min_val:{min_val}, max_val:{max_val}')
        return np.nan

def process_wkt_linestring(wkt_format_str, row):
    # split on commas to separate coordinate pairs from each other
    line = wkt_format_str.replace('LINESTRING', '').strip('() ')
    line_list = line.split(', ')

    line_list_rev = [] # initialize
    for pair in line_list:
        try:
            # in WKT, order is lon lat
            lon = pair.split(' ')[0]
            lat = pair.split(' ')[1]
            # put into Google Maps order & format
            line_list_rev += [f"{lat},{lon}:"]
        except:
            print(f"In process_wkt_linestring, couldn't process {pair} (in row {row})")

    google_maps_line = ''.join(line_list_rev).strip(':')

    return google_maps_line

def convert_wkt_to_google_maps(pipes_df):
    """
    GGIT official release has pipeline routes in WKT format only.
    For map file, need to convert to Google Maps format.
    Put Google Maps format into column 'Route'.

    In WKT:
    * Each coordinate pair is longitude then latitude, separated by spaces
    * Within linestrings: Coordinate pairs are separated by commas
    * Within multilinestrings: Linestrings are bookended by parentheses
    
    In Google Maps:
    * Each coordinate pair is latitude then longitude, separated by comma
    * Within linestrings: Coordinate pairs are separated by colons
    * Within multilinestrings: Linestrings are separated by semicolons
    """
    print("Running convert_wkt_to_google_maps")
    truncated = [] # initialize
    for row in pipes_df.index:
        # route = pipes_df.at[row, 'Route']
        wkt_format_str = pipes_df.at[row, 'WKTFormat']
        name = pipes_df.at[row, 'PipelineName']

        # if len(route) > 1:
            # print(f'ROUTE IS MORE THAN 1: {route}')
            # want to keep route information for few cases that it has it feb 2024
            # pass     
        if wkt_format_str == '--':
            # Known empty value
            pass
        else:
            if wkt_format_str.endswith(')') == True:
                # formatted correctly; not truncated
                pass
            elif wkt_format_str.endswith(')') == False:
                # it is truncated; need to get rid of partial coordinates
                truncated += [(
                    pipes_df.at[row, 'PipelineName'], 
                    pipes_df.at[row, 'Countries'], 
                    wkt_format_str[-30:]
                )]
                
                wkt_format_str = wkt_format_str.rsplit(',', 1)[0].strip()
                if wkt_format_str.startswith('LINESTRING'):
                    # close with single parentheses
                    wkt_format_str = f"{wkt_format_str})"
                elif wkt_format_str.startswith('MULTILINESTRING'):
                    # close with double parentheses
                    wkt_format_str = f"{wkt_format_str}))"

            if wkt_format_str.startswith('LINESTRING'):
                google_maps_str = process_wkt_linestring(wkt_format_str, row)
                pipes_df.at[row, 'Route'] = google_maps_str

            elif wkt_format_str.startswith('MULTILINESTRING'):
                wkt_multiline = wkt_format_str.replace('MULTILINESTRING', '').strip('() ')
                # split on '), '--marker of the end of a linestring
                wkt_multiline_list = wkt_multiline.split('), ')

                # clean up:
                wkt_multiline_list = [x.strip('(') for x in wkt_multiline_list]

                multiline_list_rev = [] # initialize
                for wkt_line in wkt_multiline_list:
                    google_maps_line = process_wkt_linestring(wkt_line, row)
                    multiline_list_rev += [google_maps_line]

                google_maps_str = ';'.join(multiline_list_rev)
                pipes_df.at[row, 'Route'] = google_maps_str

            else:
                print("Error!" + f" Couldn't convert to Google Maps: {wkt_format_str}")
                print((name, wkt_format_str))
            
                pass
    
    # after end of for row in pipes_df.index
    if len(truncated) > 0:
        print(f"WKTFormat was truncated for {len(truncated)} pipelines")
        print(truncated)

        for x in truncated:
            print(f"{x[0]} in {x[1]}; last 30 characters: {x[2]}")
            print('-'*40)
            
    return pipes_df

def coordinate_qc(df, col_country_name):
    issues_coords = {} # acro, df line
    df = df.reset_index()
    tracker = df['tracker-acro'].loc[0]
    # wait_time = 5
    # time.sleep(wait_time)
    # gsheets = gspread_creds.open_by_key(multi_tracker_countries_sheet)
    # spreadsheet = gsheets.worksheet('country_centroids')
    # country_centroids = pd.DataFrame(spreadsheet.get_all_records(expected_headers=[]))
    # split on comma, check valid lat lng, 
    # in a float valid range 
    
    # print(len(df))
    # df['WKTFormat'] = df['WKTFormat'].make_valid()
    # print(len(df))
    # input('After make valid')

    if 'WKTFormat' in df.columns: # special for hydrogen europe file
        # df['wktformat_clean'] = df['Route'].apply(lambda x: check_and_convert_float(x))
        pass


    else:
        df['float_col_clean_lat'] = df['Latitude'].apply(lambda x: check_and_convert_float(x))
        
        df['float_col_clean_lng'] = df['Longitude'].apply(lambda x: check_and_convert_float(x))
    # after converting all to float nan, we filter out nan
    # this assumes source data has gone through qc in separate file to find the comma situations
        for row in df.index:
            if pd.isna(df.loc[row, 'float_col_clean_lat']): 
                issues_coords[tracker] = df.loc[row]
                df.drop(index=row, inplace=True)
            elif pd.isna(df.loc[row, 'float_col_clean_lng']): 
                issues_coords[tracker] = df.loc[row]
                df.drop(index=row, inplace=True)

                
        # check that the numbers fall within a range
        acceptable_range = {
            'lat': {'min': -90, 'max': 90},
            'lng': {'min': -180, 'max': 180}
        }
        
        df['float_col_clean_lat'] = df['float_col_clean_lat'].apply(
            lambda x: check_in_range(x, acceptable_range['lat']['min'], acceptable_range['lat']['max'])
        )
        # print(df['float_col_clean_lat'])
        # input('check after check in range or nan')
        df['float_col_clean_lng'] = df['float_col_clean_lng'].apply(
            lambda x: check_in_range(x, acceptable_range['lng']['min'], acceptable_range['lng']['max'])
        )
        # check_in_range could return nan if out of range so need to drop nans
        # this should have been handled in QC the range stuff 
        for row in df.index:
            if pd.isna(df.loc[row, 'float_col_clean_lat']):
                print(df.loc[row]) 
                issues_coords[tracker] = df.loc[row]
                df.drop(index=row, inplace=True)
            elif pd.isna(df.loc[row, 'float_col_clean_lng']): 
                print(df.loc[row])
                issues_coords[tracker] = df.loc[row]
                df.drop(index=row, inplace=True)
    

            else:
                df.loc[row, 'Latitude'] = df.loc[row, 'float_col_clean_lat']
                df.loc[row, 'Longitude'] = df.loc[row, 'float_col_clean_lng']

    return df, issues_coords

# def find_missing_geometry(gdf,col_country_name):
#     if gdf['geometry'] == '':
#         gdf = find_missing_coords(gdf, col_country_name)
#     elif gdf['geometry'] == 'POINT(1 1)':
#         print('point 11 issue again')
#     return gdf
   
def find_missing_cap(df):
    
    # GOGET does not have capacity 
    if df['tracker'].loc[0] == 'GOGET':
        pass
    else:
        df['float_col_clean_cap'] = df['capacity'].apply(lambda x: check_and_convert_float(x))
        
        # # print("Check which rows will be dropped because nan capacity:")
        # print(df[df.isna().any(axis=1)])
        nan_df = df[df.isna().any(axis=1)]
        # nan_df.to_csv(f'{path_for_test_results}{df["tracker"].loc[0]}_nan_capacity_{today_date}.csv')
        # df = df.dropna(subset = ['float_col_clean_cap'])
        
    return df

def insert_incomplete_WKTformat_ggit_eu(df_to_drop):
    # df_to_drop = df_to_drop.copy() # df to drop
    # by project id that we know were cut off because not json file
    # insert json into geometry
    # create geometry column 

    # set up fixed ggit file pd
    ggit_routes = gpd.read_file(ggit_routes_updated)    
    ggit_routes = ggit_routes[['ProjectID', 'geometry']]
    # print(ggit_routes['geometry'])
    # input('this should not be empty ggit routes geo')
    df_to_drop.to_csv(f'issues/check_out_df_to_drop_cols_before_merge_routes {iso_today_date}.csv')

    # Merge ggit_routes with the main gdf on 'id'
    df_to_drop = df_to_drop.merge(ggit_routes[['ProjectID', 'geometry']], on='ProjectID', how='left', suffixes=('', '_new'))    
    
    merged_df = df_to_drop.drop(columns='geometry').merge(ggit_routes, on='ProjectID', how='left')
    # Update the 'route' column in gdf with the new values where there is a match
    print(f'this is length of df_to_drop {len(df_to_drop)} should be 10')
    input('check')
    # df_to_drop.drop(columns=['geometry'], inplace=True)
    # df_to_drop['geometry'] = df_to_drop['geometry_new']
    # # Drop the temporary 'route_new' column
    # df_to_drop.drop(columns=['geometry_new'], inplace=True)
    df_to_drop.to_csv(f'issues/check_out_df_to_drop_cols_after_merge_routes {iso_today_date}.csv')
    print(f'done issues/check_out_df_to_drop_cols_after_merge_routes {iso_today_date}.csv')
    # drop row if geometry equals none
    # df_to_drop = df_to_drop[df_to_drop['geometry'].notna()]
    print(df_to_drop['tracker-acro'])
    print(df_to_drop)
    input('check this after merge and drop geo, should be 10!')

    return df_to_drop

def drop_internal_tabs(df):
    df = df.drop(['tracker-acro','official_name','country_to_check'], axis=1)
    print(df.columns)
    # input('Check to see that tracker-acro and other internal cols are gone')
    return df

def convert_google_to_gdf(df):
    # TODO DOCUMENT HOW EU PIPELINES HY DATA PROCESSED UNTIL HAVE GEOJSON FILE
    df_initial = df.copy()
    print(df.columns)
    # input('check if WKTFormat is there, and also PipelineName')
    df = df[df['WKTFormat'] != '--']
    print(df[['PipelineName', 'WKTFormat']]) # or name
    df['WKTFormat'].fillna('')
    df = df[df['WKTFormat'] != '']
    print(df[['PipelineName', 'WKTFormat']])

    to_drop = []
    for row in df.index:
        if pd.isna(df.loc[row, 'WKTFormat']): 
            to_drop.append(row)
    # df['geometry'] = df['WKTFormat'].apply(lambda x: wkt.loads(x))
    # print(df['geometry'])
    to_drop_again = []
    to_drop_pid = []
    for index, row in df.iterrows():
        # try:
        value = row["WKTFormat"]
        pid = row["ProjectID"]
        try:
            wkt.loads(value)
            # print(value)
                
        except Exception as e:
            print(e)
            # input('DROPPING THIS INDEX IN CONVERT WKFORMAT/GOOGLE TO GDF FUNCTION')
            to_drop_again.append(index)
            to_drop_pid.append(pid)
            # print(f'{index} {value!r}')
        # input('Dropped pipeline')
    print(to_drop_pid)
    print(len(to_drop_again))
    input('check if new json will fix this') # it will
    #['P5853', 'P6206', 'P6202', 'P6203', 'P4383', 'P6212', 'P5850', 'P4418', 'P6220', 'P6223', 'P6224']
    # let's drop them but create a new separate df with them
     
    df_to_drop = df.loc[to_drop_again]
    print(df_to_drop)
    input('Inspect that it is a df and only 10')
    # then add geometry column from separate file and drop wkt, 
    # then concat later in two steps after this main df is a gdf  
    df_to_drop = insert_incomplete_WKTformat_ggit_eu(df_to_drop)
    print(df_to_drop) # check that this has all the old cols and just added geo
    print('df to drop cols')
    # for col in df_to_drop.columns:
    #     print(col)
    df_to_drop.info()
    print('df cols')
    # for col in df.columns:
    #     print(col)
    df.info()
    input('Inspect that it is a df')
    
    df = df.drop(to_drop_again) 
    
    df['geometry'] = df['WKTFormat'].apply(lambda x: wkt.loads(x))
    
    print(len(df))
    df = pd.concat([df, df_to_drop])
    print(len(df))
    input('length after of length of df')
    
    # print(df['geometry'])
    # print(df['PCI5'])
    # input('CHECK PCI5')
    input(f'Check size before and after: now | {len(df)} then | {len(df_initial)}')
    
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
    return gdf

def convert_coords_to_point(df):
    crs = 'EPSG: 4326'
    geometry_col = 'geometry'
    df = df.reset_index(drop=True)

    for row in df.index:
        df.loc[row,'geometry'] = Point(df.loc[row,'Longitude'], df.loc[row,'Latitude'])
    gdf = gpd.GeoDataFrame(df, geometry=geometry_col, crs=crs)
    
    return gdf

def process_gmaps_linestring(gmap_format_str):
    """
    Convert from Google Maps format to WKT format
    """
    
    # split on colons to separate coordinate pairs from each other
    line_list = gmap_format_str.strip().split(':')
    # clean up
    line_list = [x.strip() for x in line_list]

    line_list_rev = [] # initialize
    for pair in line_list:
        # in Google Maps, order is lat, lon
        lat = pair.split(',')[0].strip()
        lon = pair.split(',')[1].strip()
        # put into WKT order & format
        line_list_rev += [f"{lon} {lat},"]

    wkt_line = ' '.join(line_list_rev).strip(',')

    return wkt_line

def convert_google_maps_to_wkt(
    pipes_df, 
):
    """
    GFIT has pipeline routes in Google Maps format (renamed in this notebook to 'Route (Google Maps)'
    For download file, want to use WKT format to be consistent with GGIT.
    Put WKT format into column 'WKTFormat'.

    In WKT:
    * Each coordinate pair is longitude then latitude, separated by spaces
    * Within linestrings: Coordinate pairs are separated by commas
    * Within multilinestrings: Linestrings are bookended by parentheses
    
    In Google Maps:
    * Each coordinate pair is latitude then longitude, separated by comma
    * Within linestrings: Coordinate pairs are separated by colons
    * Within multilinestrings: Linestrings are separated by semicolons
    """
    
    # rename column if not already in this format
    pipes_df = pipes_df.rename(columns={'Route': 'Route (Google Maps)'})
    
    for row in pipes_df.index:
        val = pipes_df.at[row, 'Route (Google Maps)']
        if pd.isna(val)==True:
            # can't convert
            pass
        
        else:
            gmap_format_str = val

            if ';' in gmap_format_str:
                # split on ';' -- the marker of the end of a linestring
                gmap_multiline_list = gmap_format_str.split(';')

                # clean up:
                gmap_multiline_list = [x.strip() for x in gmap_multiline_list]

                multiline_list_rev = [] # initialize

                for gmap_line in gmap_multiline_list:
                    wkt_line = process_gmaps_linestring(gmap_line)
                    # put parentheses around wkt lines
                    wkt_line = f"({wkt_line})"
                    multiline_list_rev += [wkt_line]

                wkt_str = ', '.join(multiline_list_rev)
                # add MULTILINESTRING wrapper
                wkt_str = f"MULTILINESTRING({wkt_str})"
                pipes_df.at[row, 'WKTFormat'] = wkt_str

            elif ';' not in gmap_format_str and ':' in gmap_format_str:
                wkt_str = process_gmaps_linestring(gmap_format_str)
                # add LINESTRING wrapper
                wkt_str = f"LINESTRING({wkt_str})"
                pipes_df.at[row, 'WKTFormat'] = wkt_str

            # elif gmap_format_str in no_route_entries:
            #     # Known values for no route
            #     pass

            else:
                print("Error!" + f" Couldn't convert to WKT format: {gmap_format_str}")
    
    return pipes_df

def convert_WKT_to_geo(df):
    crs = 'EPSG: 4326'
    geometry_col = 'WKTFormat'
    df = df.reset_index(drop=True)
    print(df['WKTFormat'])
    # input('inspect')
    
    # for row in df.index:
    #     df.loc[row,'geometry'] = LineString(df.loc[row,'Route'])
    gdf = gpd.GeoDataFrame(df, geometry=geometry_col, crs=crs)
    
    return gdf

def find_about_page(tracker,key):

        gspread_creds = gspread.oauth(
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
            credentials_filename=client_secret_full_path,
            # authorized_user_filename=json_token_name,
        )
        wait_time = 5
        time.sleep(wait_time)
        gsheets = gspread_creds.open_by_key(key)
            
        # List all sheet names
        sheet_names = [sheet.title for sheet in gsheets.worksheets()]
        # print(f"{tracker} Sheet names:", sheet_names)
        # Access a specific sheet by name
        first_tab = sheet_names[0]
        first_sheet = gsheets.worksheet(first_tab)  # Access the first sheet
        
        last_tab = sheet_names[-1]
        last_sheet = gsheets.worksheet(last_tab)  # Access the last sheet

        # print("First sheet name:", sheet.title)
        if 'About' not in first_sheet.title:
            # print('Looking for about page in last tab now, first one no.')
            # handle for goget and ggit, goit who put it in the last tab
            if 'About' not in last_sheet.title:
                if 'Copyright' not in last_sheet.title:
                    print('Checked first and last tab, no about page found not even for copyright. Pausing.')
                    # input("Press Enter to continue...")
                else:
                    # print(f'Found about page in last tab: {last_tab}')
                    sheet = last_sheet
            else:
                # print(f'Found about page in last tab: {last_tab}')
                sheet = last_sheet
        else:
            # print(f'Found about page in first tab: {first_tab}')
            sheet = first_sheet
        
        data = pd.DataFrame(sheet.get_all_records(expected_headers=[]))
        about_df = data.copy()
    
        return about_df

def find_region_country_colname(df):
    continent_list = ['Africa', 'Americas', 'Oceania', 'Asia', 'Europe']
    cols = df.columns
    col_reg_name = '' # initialize 
    col_country_name = ''
    tracker = df['tracker-acro'].loc[0]
    if tracker in tracker_mult_countries: # GGIT GOIT
        col_country_name = ['StartCountry', 'EndCountry']
        # col_reg_name = ['StartRegion', 'EndRegion'] # Ask Baird if this is reasonable
    # elif df['tracker-acro'].loc[0] == 'GOGET':
    #     col_country_name = 'Country' # not Country List because that is only relevant for some rows 
    elif tracker == 'GHPT':
        col_country_name = ['Country 1', 'Country 2']
        # col_reg_name = ['Region 1', 'Region 2']    
    else:
        for col in cols:
            # random row
            random = int(len(df) / 2)
            # print(random)
            
            if df[col].loc[random] in continent_list and 'region' in col.lower():
                col_reg_name = col 
                # print(f'this is region col: {col_reg_name} to filter on for {tracker}!')
                # input('Check region col')
                continue

            elif df[col].loc[random] in full_country_list and 'country' in col.lower():
                if col == 'ParentHQCountry':
                    continue
                # elif df tracker is pipeline or goget use countries col always!  tracker-acro
                else:
                    col_country_name = col
                    # print(f'this is country col: {col_country_name} to filter on  for {tracker}!')
                    # input('Check country col')
                    continue
    return col_reg_name, col_country_name    

# Define a function to check for valid values
# def is_valid_goget(x):

#     return isinstance(x, (int, float)) and not pd.isna(x) and x != '' and x != 0 and x != 0.0
def handle_goget_gas_only_workaround(goget_orig_file):
    list_ids = []
    df = pd.read_excel(goget_orig_file, sheet_name='Main data')
    df = df[df['Fuel type']!= 'oil'] # 7101
    print(len(df))
    # goget_gas_only_all_regions_march_2024 = []
    list_ids = df['Unit ID'].to_list()
    return list_ids


def pci_eu_map_read(gdf):
    # take columns PCI5 and PCI6 
    # create one column, both, 5, 6, none, all as strings
    print(gdf.head())
    print(gdf['tracker-acro'])
    input('check why no PCI5')
    gdf['pci-list'] = ''
    for row in gdf.index:
        pci5 = gdf.loc[row, 'PCI5']
        pci6 = gdf.loc[row, 'PCI6']
        if pci5 == 'yes' and pci6 == 'yes':
            gdf.at[row, 'pci-list'] = 'both'
        elif pci5 == 'yes':
            gdf.at[row, 'pci-list'] = '5'
        elif pci6 == 'yes':
            gdf.at[row, 'pci-list'] = '6'
        else:
            gdf.at[row, 'pci-list'] = 'none'
        
    return gdf


def assign_eu_hydrogen_legend(gdf):
    # take column fuel and tracker-custom
    # if column == hydrogen and tracker-custom == ggit-eu
    # change tracker-custom to ggit-euhy
    for row in gdf.index:
        fuel = gdf.loc[row, 'fuel']
        tracker_cust = gdf.loc[row, 'tracker-custom']
        if fuel == 'Hydrogen' and tracker_cust == 'GGIT-eu':
            gdf.at[row, 'tracker-custom'] = 'GGIT-euhy'
        elif fuel == 'Hydrogen':
            print('Odd fuel type for infrastructure type')
            print(row)
            input('check the above')

    return gdf

# Function to check if any item in the row's list is in needed_geo
def check_list(row_list, needed_geo):
    return any(item in needed_geo for item in row_list)

def create_filtered_df_list_by_map(trackerdf, col_country_name, col_reg_name, maptype, needed_geo):
    # this function takesa df and filters on appropriate geo for the regional map
    
    # double check clean country and region columns and list of countries
    filtered_df = trackerdf.copy()
    tracker = filtered_df['tracker-acro'].loc[0]
    # print(tracker)
    # print(maptype)
    # print(len(filtered_df))
    # print(needed_geo)
    # print(maptype)
    
    # input('check maptype')
    if maptype in ['GIPT', 'Global']:
        # print('For GIPT we do not filter by geo')
        pass
    else: #maptype == 'latam': # ['latam', 'asia']   
        # if tracker in tracker_mult_countries: # currently no lists like with regions since goit and ggit created countries a list from start and end countries
            # if any of the countries in the country column list is in the needed geo list then keep it if none then filter out
        # this is to go in and filter by country
        # mult and hydro have two columns in country col as a list
        # all others just one column name
        # add the items from the two or just check the two no ad GHPT
        def split_countries(country_str):

            for sep in [';', '-', ',']:
                if sep in country_str:
                    return country_str.strip().split(sep)
                return [country_str]
            
        if tracker == 'GHPT' or tracker in tracker_mult_countries:
            # list of cols to go through
            filtered_df['country_to_check'] = [[] for _ in range(len(filtered_df))]
            # for row in filtered_df.index:
            #     # for col in col_country_name:
            #     print(col_country_name[0])
            #     # add value to list in column country to check
            #     filtered_df['country_to_check'] += filtered_df.loc[row, col_country_name[0]]
            #     print(col_country_name[1]) 
            #     filtered_df['country_to_check'] += filtered_df.loc[row, col_country_name[1]]
            for row in filtered_df.index:                    
                for col in col_country_name:
                    # add value to list in column country_to_check
                    filtered_df.at[row, 'country_to_check'] += [filtered_df.at[row, col]]
            # print(filtered_df['country_to_check'])
            # input('check this')
            filtered_df = filtered_df[filtered_df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]

            
        else:
        # if isinstance(col_country_name, list): # hydro more than one
        #         # print(col_country_na
        #         # me)
        #         filtered_df['country_to_check'] = [[] for _ in range(len(filtered_df))] # makes it a list                # this pulls each country out from start and end country into one list, could also apply this to hydro?
        #         for col in col_country_name:
        #             # TEST THIS
        #             # filtered_df['country_to_check'] = filtered_df[col].str.strip()
        #             filtered_df['country_to_check'] = filtered_df.apply(lambda row: row['country_to_check'] + row[col].strip(), axis=1)

            filtered_df['country_to_check'] = filtered_df.apply(lambda row: split_countries(row[col_country_name]), axis=1)
            # print(filtered_df['country_to_check'])
            # input('check this')
            filtered_df = filtered_df[filtered_df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]


        # for sep in ',;-':
        #     # I want to break up any multiple countries into a list of countries
        #     # then check if any of those are in the needed_geo list
        #     filtered_df['country_to_check'] = filtered_df[col_country_name].str.strip().str.split(sep) 

        # filter the df on the country column to see if any of the countries in that list is in the needed geo
        
        # filtered_df = filtered_df[filtered_df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]
        # # print(tracker)
        # # print(maptype)
        # print(f'len after filter: {len(filtered_df)}')
        # # input(f'Check length for tracker ggit goit after filter')
        # filtered_df = filtered_df.drop(columns=['country_to_check'])

        # else:
        #     # # TODO now that we are only filtering on country for latam we can probalby remove this if else
        #     if isinstance(col_country_name, list): # hydro more than one
        #         # print(col_country_name)
        #         filtered_df['country_to_check'] = [[] for _ in range(len(filtered_df))]

        #         for col in col_country_name:
        #             # TEST THIS
        #             # filtered_df['country_to_check'] = filtered_df[col].str.strip()
        #             filtered_df['country_to_check'] = filtered_df.apply(lambda row: row['country_to_check'] + [row[col].strip()], axis=1)

        #         filtered_df = filtered_df[filtered_df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]
        #         filtered_df = filtered_df.drop(columns=['country_to_check'])

        #     else:
        #         filtered_df['country_to_check'] = filtered_df[col_country_name].str.strip()

        #         # need this by country because not a GEM region, problematic since goget uses region and numbers when filtered by country in the gem region do not match 636 versus 578 for africa
        #         filtered_df = filtered_df[filtered_df['country_to_check'].isin(needed_geo)]
            
        #         filtered_df = filtered_df.drop(columns=['country_to_check'])
    
    
    # non geo filter      
    if maptype in gas_only_maps:
        # filter out oil facilities
        print(f'len before gas only filter {tracker} {len(filtered_df)} for map {maptype}')                

        if tracker == 'GOGET':
            # using this just to filter from columns not in map file but in official release
            goget_orig_file = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/source/Global Oil and Gas Extraction Tracker - 2024-03-08_1205 DATA TEAM COPY.xlsx'

            # filter out oil
            list_ids = handle_goget_gas_only_workaround(goget_orig_file)
            # print(len(ndf)) # 3095 will be less because not all trackers
            # filter = (df['tracker-acro']=='GOGET') & (df['prod-gas']=='') #2788
            # filter = df['id'] in list_ids #2788
            # df = df[(df['tracker-acro']=='GOGET') & (df['id'] in list_ids)]
            drop_row = []
            for row in filtered_df.index:
                # if df.loc[row, 'tracker-acro'] == 'GOGET':
                if filtered_df.loc[row, 'Unit ID'] not in list_ids:
                    drop_row.append(row)
            # drop all rows from df that are goget and not in the gas list ids 
            filtered_df.drop(drop_row, inplace=True)           
            # print(len(ndf)) # 3012 after removing goget 
        elif tracker in ['GGIT-eu', 'GGIT']:
            # filter for hydrogen only, but also gas for pci europe uses this instead of other release
            drop_row = []
            for row in filtered_df.index:
                # if df.loc[row, 'tracker-acro'] == 'GOGPT': # 1751 from 1966 after filter
                if filtered_df.loc[row, 'Fuel'] == 'Oil':
                    drop_row.append(row)
                elif filtered_df.loc[row, 'Fuel'] == '':
                    drop_row.append(row)

            filtered_df.drop(drop_row, inplace=True)  

             
        elif tracker == 'GOGPT':
            # filter2 = (df['tracker-acro']=='GOGPT') & (df['fuel'].contains('liquid')) #2788
            drop_row = []
            for row in filtered_df.index:
                # if df.loc[row, 'tracker-acro'] == 'GOGPT': # 1751 from 1966 after filter
                fuel_cat_list = filtered_df.loc[row, 'Fuel'].split(',')
                new_fuel_cat_list = []
                for fuel in fuel_cat_list:
                    fuel = fuel.split(':')[0]
                    new_fuel_cat_list.append(fuel)
                
                # for Alcudia does not contain gas, or only contains fossil liquids
                
                # fossil liquids: diesel, fossil gas: natural ga...      37.5  operating   
                if len(new_fuel_cat_list) > 1:
                    if new_fuel_cat_list.count('fossil liquids') == len(new_fuel_cat_list):
                            drop_row.append(row)
  
                elif new_fuel_cat_list == ['fossil liquids']:
                    drop_row.append(row)
                        
            # drop all rows from df that are goget and not in the gas list ids 
            filtered_df.drop(drop_row, inplace=True)  
            # print(len(ndf)) # should be 2797
            print(f'len after gas only filter {tracker} {len(filtered_df)}') 
            # input('Check')               
           
        
    #     if maptype == 'asia': 
    #         print(f'len after gas only filter {tracker} {len(filtered_df)}')                
    #         # input('check that gas pipes get in here')
    #         # use the actual list of countries from the sheets so no western asia
    #         needed_geo = asia_countries
    #         if tracker in tracker_mult_countries: # currently no lists like with regions since goit and ggit created countries a list from start and end countries
    #             # if any of the countries in the country column list is in the needed geo list then keep it if none then filter out
    #             for sep in ',;-':
    #                 # I want to break up any multiple countries into a list of countries
    #                 # then check if any of those are in the needed_geo list
    #                 filtered_df['country_to_check'] = filtered_df[col_country_name].str.strip().str.split(sep) 

    #             # filter the df on the country column to see if any of the countries in that list is in the needed geo
    #             filtered_df = filtered_df[filtered_df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]
    #             # print(tracker)
    #             # print(maptype)
    #             # print(filtered_df)
    #             # input(f'Check length for tracker ggit goit after filter')
    #             filtered_df = filtered_df.drop(columns=['country_to_check'])

    #         else:
    #             # # TODO now that we are only filtering on country for latam we can probalby remove this if else
    #             if isinstance(col_country_name, list): # hydro more than one
    #                 # print(col_country_name)
    #                 filtered_df['country_to_check'] = [[] for _ in range(len(filtered_df))]

    #                 for col in col_country_name:
    #                     # TEST THIS
    #                     # filtered_df['country_to_check'] = filtered_df[col].str.strip()
    #                     filtered_df['country_to_check'] = filtered_df.apply(lambda row: row['country_to_check'] + [row[col].strip()], axis=1)

    #                 filtered_df = filtered_df[filtered_df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]
    #                 filtered_df = filtered_df.drop(columns=['country_to_check'])

    #             else:
    #                 filtered_df['country_to_check'] = filtered_df[col_country_name].str.strip()

    #                 # need this by country because not a GEM region, problematic since goget uses region and numbers when filtered by country in the gem region do not match 636 versus 578 for africa
    #                 filtered_df = filtered_df[filtered_df['country_to_check'].isin(needed_geo)]
                
    #                 filtered_df = filtered_df.drop(columns=['country_to_check'])
    #         print(f'len after asia w asia filter {tracker} {len(filtered_df)}')  
    #         # input('check len after')              

    #     elif maptype == 'europe': 
    #         print(f'len after gas only filter {tracker} {len(filtered_df)}') 
    #         # input('check that gas pipes get in here')
    #         # use the actual list of countries from the sheets so no western asia
    #         needed_geo = europe_countries
    #         if tracker in tracker_mult_countries: # currently no lists like with regions since goit and ggit created countries a list from start and end countries
    #             # if any of the countries in the country column list is in the needed geo list then keep it if none then filter out
    #             for sep in ',;-':
    #                 # I want to break up any multiple countries into a list of countries
    #                 # then check if any of those are in the needed_geo list
    #                 filtered_df['country_to_check'] = filtered_df[col_country_name].str.strip().str.split(sep) 

    #             # filter the df on the country column to see if any of the countries in that list is in the needed geo
    #             filtered_df = filtered_df[filtered_df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]
    #             # print(tracker)
    #             # print(maptype)
    #             # print(filtered_df)
    #             # input(f'Check length for tracker ggit goit after filter')
    #             filtered_df = filtered_df.drop(columns=['country_to_check'])

    #         else:
    #             # # TODO now that we are only filtering on country for latam we can probalby remove this if else
    #             if isinstance(col_country_name, list): # hydro more than one
    #                 # print(col_country_name)
    #                 filtered_df['country_to_check'] = [[] for _ in range(len(filtered_df))]

    #                 for col in col_country_name:
    #                     # TEST THIS
    #                     # filtered_df['country_to_check'] = filtered_df[col].str.strip()
    #                     filtered_df['country_to_check'] = filtered_df.apply(lambda row: row['country_to_check'] + [row[col].strip()], axis=1)

    #                 filtered_df = filtered_df[filtered_df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]
    #                 filtered_df = filtered_df.drop(columns=['country_to_check'])

    #             else:
    #                 filtered_df['country_to_check'] = filtered_df[col_country_name].str.strip()

    #                 # need this by country because not a GEM region, problematic since goget uses region and numbers when filtered by country in the gem region do not match 636 versus 578 for africa
    #                 filtered_df = filtered_df[filtered_df['country_to_check'].isin(needed_geo)]
                
    #                 filtered_df = filtered_df.drop(columns=['country_to_check'])
    #         print(f'len after europe gem filter {tracker} {len(filtered_df)}')  
    #         # input('check len after')           
    
    # else:
    #     print('Filtering by region!')
    #     # input('Check that')
    #     if isinstance(col_reg_name, list):
    #         maptype_list = maptype.title().split(' ')
    #         print(maptype_list)
    #         print(type(maptype_list))
    #         print(col_reg_name)
    #         # initialize a list in that column! 
    #         filtered_df['region_to_check'] = [[] for _ in range(len(filtered_df))]

    #         for col in col_reg_name:
    #             # we want to add the row's region in that col to a new column's list of all regions 
    #             filtered_df['region_to_check'] = filtered_df.apply(lambda row: row['region_to_check'] + [row[col].strip()], axis=1)
    #             # print(filtered_df['region_to_check'])
    #         # TEST THIS so africa becomes ['africa']
    #         # print(filtered_df['region_to_check'])
    #         filtered_df = filtered_df[filtered_df['region_to_check'].apply(lambda x: check_list(x, maptype_list))]
    #         filtered_df = filtered_df.drop(columns=['region_to_check'])
    #     else:

    #         filtered_df[col_reg_name] = filtered_df[col_reg_name].str.strip()

    #         filtered_df = filtered_df[filtered_df[col_reg_name] == maptype.title()]
    # # print(len(filtered_df))
    # input('check')
    return filtered_df

def conversion_equal_area(row):
    cap = float(row['cleaned_cap'])
    factor = float(row['conversion_factor'])
    # print(f'this is factor! {factor}')
    result = math.sqrt(4 * (float(cap * factor)) / np.pi) # square root(4 * capacity / pi)
    
    return result 

def conversion_multiply(row):
    cap = float(row['cleaned_cap'])
    factor = float(row['conversion_factor'])
    # print(f'this is factor! {factor}')
    result = float(cap * factor)
    # print(f'this is result! {result}')
    return result

def format_final(df_arg): # TO DO
    df = df_arg.copy()
    # make all years non float
    # round floats to 2
    # remove helper cols official_name & country to check 
    return df

def workaround_no_sum_cap_project(gdf):
    gdf = gdf.copy()
    
    # result = int()
    
    # group by id
    # summed cleaned cap
    # that's the project cap
    # print(gdf['name'].value_counts())
    # gdf['unit-name-status'] = ''
    gdf['capacity'].fillna('')
    gdf['unit_name'].fillna('--')
    gdf['unit_name'].replace('','--')
    gdf['unit_name'].replace('nan','--')
    gdf['unit_name'].replace('nan ','--')
    for row in gdf.index:
        # try:
            # groupby on that specifci row's name
        tracker = gdf.loc[row, 'tracker-acro']
        name = gdf.loc[row, 'name']
        # pid = gdf.loc[row, 'pid'] add project id to all
        capacity = gdf.loc[row, 'capacity']

        # Convert blank string capacities to NaN
        gdf['capacity'] = gdf['capacity'].replace('', np.nan).replace('--', np.nan).replace('-', np.nan).astype(float)
        
        # Group by project name and sum the capacities
        capacity_details = gdf[gdf['name'] == name].groupby('name', as_index=False)['capacity'].sum()
        
        # If the sum is NaN, replace it with an empty string
        capacity_details['capacity'] = capacity_details['capacity'].fillna('')
        # TODO WORK IN PROGRESS to help fix the summary cap bug affecting solar and all ... 
        all_unit_names_statuses = gdf[gdf['name'] == name].apply(lambda x: f"{x['unit_name']} ({x['status']})", axis=1).to_list()
        all_unit_names_statuses_str = ', '.join(all_unit_names_statuses)
        
        # print(all_unit_names_statuses_str)
        # input('check this uni status thing')
        # if capacity != capacity_details:
        #     print(f'This is a multi-unit project: {name} in {tracker}')
        #     # input('check the above for good test!')
        # else:
        #     print(f'This is not a multi-unit proejct: {name} in {tracker}')
            
        # except:
        #     print(f'capacity details is blank for {name} in {tracker}')
        #     input('check because cap detail is empty')
        #     capacity_details = ''
        # capacity_details = ''

        gdf.loc[row, 'capacity-details'] = capacity_details
        # gdf.loc[row, 'unit-name-status'] = all_unit_names_statuses  # ValueError: Must have equal len keys and value when setting with an iterable
    # project_cap_df = gdf.groupby('name', as_index=False)['capacity'].sum()
    # print(f'this is cols of project_cap_df: {project_cap_df.columns}')
    # project_cap_df = project_cap_df.rename(columns={'capacity': 'capacity-details'})
    
    # # merge on name to gdf
    
    # gdf = pd.merge(left=gdf, right=project_cap_df, on='name', how='outer')
     
    return gdf

def workaround_display_cap(row, cap_col):
    cap = row[cap_col] 
    cap = check_and_convert_float(cap)
    if pd.isna(cap):
        cap = '' 
    units_of_m = str(row['original_units'])
    if isinstance(cap, (int, float)):
        cap = str((round(cap, 3))) # handle rounding and converting from string to float to round later 
        result = f'{cap} {units_of_m}'
    else:
        result = ''
    return result
    
def workaround_table_float_cap_units(row, cap_col):
    cap = row[cap_col] 
    cap = check_and_convert_float(cap)
    if pd.isna(cap):
        cap = '' 
    units_of_m = str(row['original_units'])
    if isinstance(cap, (int, float)):
        cap = float((round(cap, 3))) # handle rounding and converting from string to float to round later 
    else:
        result = ''
    return cap, units_of_m
    
    

# def workaround_display_cap_total(row):
#     # adds original units to the summedcapacity-details'from workaround_no_sum_cap_project
#     cap = row['capacity-details']
#     cap = check_and_convert_float(cap)

#     if pd.isna(cap):
#         cap = '' 
#     units_of_m = str(row['original_units'])
#     if isinstance(cap, (int, float)):
#         cap = str(float(round(cap, 3)))
#         result = f'{cap} ({units_of_m})'
#     else:
#         result = ''
#     return result
    
    
def fix_status_inferred(df):
    # print(f"Statuses before: {set(df['status'].to_list())}")
    inferred_statuses_cancelled = df['status'].str.contains('cancelled - inferred')
    inferred_statuses_shelved = df['status'].str.contains('shelved - inferred')
    
    # # print(inferred_statuses_cancelled['status']!=False)
    # # print(len(inferred_statuses_shelved))
    df.loc[inferred_statuses_cancelled, 'status'] = 'cancelled'
    df.loc[inferred_statuses_shelved,'status'] = 'shelved'
    # for row in df.index:
    #     if 'shelved - inferred' in df.loc[row, 'status']:
    #         df.loc[row, 'status'] = 'shelved'
    
    # print(f"Statuses after: {set(df['status'].to_list())}")

    return df

def check_countries_official(df,col_country_name, col_wiki, mapname, tracker):
    df = df.copy()
    problem_units_weird_country = []
    df_country_list = df[col_country_name].unique().tolist()
    df_country_wiki = df[[col_country_name, col_wiki]] # df wiht just these two columns
    for row in df_country_wiki.index:
        if df.loc[row,col_country_name] in full_country_list:
            pass
        else:
            problem_units_weird_country.append((df.loc[row,col_wiki], df.loc[row,col_country_name]))

    path_for_test_results = gem_path + mapname + '/test_results/'
    df = df.reset_index()
    problem_units_weird_country_df = pd.DataFrame(problem_units_weird_country, columns=['wiki', 'weird_country']).drop_duplicates()
    problem_units_weird_country_df.to_csv(f'{path_for_test_results}{tracker}_problem_units_weird_country_{iso_today_date}.csv', index=False)
    # print(f'There were {len(problem_units_weird_country_df)} found for this df {df["tracker-acro"].iloc[0]}! Look at them here: {path_for_test_results}problem_units_weird_country_{iso_today_date}.csv')
    # input('Did you check it yet?')
    return None

def check_for_lists(gdf):
    for col in gdf.columns:
        if any(isinstance(val, list) for val in gdf[col]):
            print('Column: {0}, has a list in it'.format(col))
        else:
            pass
