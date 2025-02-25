# previously called create_map_datadwnld_about.py froma africa-energy
# creates the files for the multi maps

from curses import OK
from pstats import Stats
import statistics
import pandas as pd
import geopandas as gpd
import numpy as np
from tqdm import tqdm
# from shapely.geometry import Point, LineString
# from shapely import wkt
# # import polyline
# import pygsheets
import gspread
# from gspread_dataframe import get_as_dataframe, set_with_dataframe
# import xlwings
import json
from gspread.exceptions import APIError
import time
from itertools import permutations
import copy
import os
from datetime import date
import openpyxl
from scipy import stats
import xlsxwriter
from all_config import *
import re
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.styles import Alignment
from helper_functions import *
import pyogrio
from collections import Counter
import time
import pickle
from stubb_about_page import stubb_file
from googleapiclient.errors import HttpError

start_time = time.time()  # Record the start time

################
# ADAPT AET FUNCTIONS FOR ALL MULTI TRACKER MAPS #
################

def what_maps_are_needed_new(multi_tracker_log_sheet_key, map_tab):
    needed_map_and_tracker_dict = {} # map: (trackers, geo, fuel)
    # TODO un comment after it passes tests
    # if local_copy:
    #     with open('local_pkl/map_tab_df.pkl', 'rb') as f:
    #         map_tab_df = pickle.load(f)
    #     print("DataFrame have been loaded from map_tab_df.pkl")
    # else: 
    map_tab_df = gspread_access_file_read_only(multi_tracker_log_sheet_key, map_tab)
    # # printf'Trackers with updates to be incorporated: {trackers_to_update}')

    with open('local_pkl/map_tab_df.pkl', 'wb') as f:
        pickle.dump(map_tab_df, f)
    print("DataFrame have been saved to map_tab_df.pkl")

    print("Now go through and create the needed tracker dict based on new data in trackers to update.")
    for tracker in trackers_to_update:
        for row in map_tab_df.index:
            # use the tracker to filter the map_tab_df df for only rows that contain the tracker in source column
            print(map_tab_df)
            print(map_tab_df.info())

            # input('This is map_tab_df df')
            sources = map_tab_df.loc[row, 'source'].split(',')
            geo = map_tab_df.loc[row, 'geo'].split(',')
            fuel = map_tab_df.loc[row, 'fuel'].split(',')
            mapname = map_tab_df.loc[row, 'mapname']
            # print(sources)
            # input('this is sources column split on comma')
            if tracker in sources:
                needed_map_and_tracker_dict[mapname] = (sources, geo, fuel)

            else:
                map_tab_df.drop(row, inplace=True)
    print(map_tab_df)
    input('This is map_tab_df_copy after dropping irrelevant rows')
    print(needed_map_and_tracker_dict)
    input('this is dict')
        # for row in map_tab_df.index:
        #     if tracker in row['source'].to_list():
            # needed_map_and_tracker_dict[row['mapname']] = (row['source'],row['geo'],row['fuel'])
                
                
        # filter out the map tracker tab df 
        # so that we only have the row that matches the tracker to be updated
        # and also find the tracker names for the map to be updated beyond the new tracker data but existing tracker data as well
        # map_log_df_sel = map_depend_df[map_depend_df['official release tab name'] == tracker]
        # for col in map_log_df_sel.columns:
        #     if 'yes' in map_log_df_sel[col].values:
        #         map_log_df_map_sel = map_log_df[map_log_df[col] == 'yes']
        #         tracker_col_index = map_log_df.columns.get_loc('official release tab name')
        #         tracker_name_col_map_sel = map_log_df.columns[tracker_col_index]
        #         list_of_trackers_relevant_to_map = map_log_df_map_sel[tracker_name_col_map_sel].to_list()
        #         needed_map_and_tracker_dict[col] = list_of_trackers_relevant_to_map
        #         print(f'Map {col} needs to be updated with the new data for {tracker}, and existing data for {list_of_trackers_relevant_to_map} minus {tracker}.')
        #         # ##(input('Check this with ggit-hy')
            
    return needed_map_and_tracker_dict

def what_maps_are_needed(multi_tracker_log_sheet_key, multi_tracker_log_sheet_tab):
    needed_map_and_tracker_dict = {} # map: [trackers]
    
    if local_copy:
        with open('local_pkl/map_log_df.pkl', 'rb') as f:
            map_log_df = pickle.load(f)
        print("DataFrame have been loaded from map_log_df.pkl")
    else: 
        map_log_df = gspread_access_file_read_only(multi_tracker_log_sheet_key, multi_tracker_log_sheet_tab)
        # # printf'Trackers with updates to be incorporated: {trackers_to_update}')

        with open('local_pkl/map_log_df.pkl', 'wb') as f:
            pickle.dump(map_log_df, f)
        print("DataFrame have been saved to map_log_df.pkl")
    
    print("Now go through and create the needed tracker dict based on new data in trackers to update.")
    for tracker in trackers_to_update:
        print(map_log_df)
        # filter out the map tracker tab df 
        # so that we only have the row that matches the tracker to be updated
        # and also find the tracker names for the map to be updated beyond the new tracker data but existing tracker data as well
        map_log_df_sel = map_log_df[map_log_df['official release tab name'] == tracker]
        print(map_log_df_sel)
        input('check that it is gogets offiical name')
        for col in map_log_df_sel.columns:
            if 'yes' in map_log_df_sel[col].values:
                map_log_df_map_sel = map_log_df[map_log_df[col] == 'yes']
                tracker_col_index = map_log_df.columns.get_loc('official release tab name')
                tracker_name_col_map_sel = map_log_df.columns[tracker_col_index]
                list_of_trackers_relevant_to_map = map_log_df_map_sel[tracker_name_col_map_sel].to_list()
                needed_map_and_tracker_dict[col] = list_of_trackers_relevant_to_map
                print(f'Map {col} needs to be updated with the new data for {tracker}, and existing data for {list_of_trackers_relevant_to_map} minus {tracker}.')
                # ##(input('Check this with ggit-hy')
            
    return needed_map_and_tracker_dict

def what_countries_or_regions_are_needed_per_map(multi_tracker_countries_sheet, needed_map_and_tracker_dict):
    needed_tracker_geo_by_map = {} # {map: [[trackers],[countries]]}
    # map_by_region = gspread_creds.open_by_key(multi_tracker_countries_sheet)

    for map, list_needed_trackers in needed_map_and_tracker_dict.items():
        print(map)
        if map in ['GIPT', 'Global']:
            list_needed_geo = '' # global
            needed_tracker_geo_by_map[map] = [list_needed_trackers, list_needed_geo]

        else: # TODO remove this using a dictionary not that drive file anymore
            map = map.lower().split(' ')[0]
            if map == 'asia':
                # country_tab = 'asia (excl western asia)'
                # spreadsheet = map_by_region.worksheet(country_tab)
                # print(spreadsheet)
                # country_df = pd.DataFrame(spreadsheet.get_all_records())
                # list_needed_geo = country_df.iloc[:, 0].to_list()
                list_needed_geo = asia_countries
                needed_tracker_geo_by_map[map] = [list_needed_trackers, list_needed_geo]
            elif map == 'europe':
                # country_tab = 'europe (regional maps)'
                # spreadsheet = map_by_region.worksheet(country_tab)
                # print(spreadsheet)
                # country_df = pd.DataFrame(spreadsheet.get_all_records())
                # list_needed_geo = country_df.iloc[:, 0].to_list()
                list_needed_geo = europe_countries

                needed_tracker_geo_by_map[map] = [list_needed_trackers, list_needed_geo]    
            elif map == 'latam':
                # country_tab = 'latam'
                # spreadsheet = map_by_region.worksheet(country_tab)
                # print(spreadsheet)
                # country_df = pd.DataFrame(spreadsheet.get_all_records())
                # list_needed_geo = country_df.iloc[:, 0].to_list()
                list_needed_geo = latam_countries

                needed_tracker_geo_by_map[map] = [list_needed_trackers, list_needed_geo]             
            else:
                # spreadsheet = map_by_region.worksheet(map)
                # print(spreadsheet)
                # country_df = pd.DataFrame(spreadsheet.get_all_records())
                # list_needed_geo = country_df.iloc[:, 0].to_list()
                list_needed_geo = africa_countries

                needed_tracker_geo_by_map[map] = [list_needed_trackers, list_needed_geo]
 
    return needed_tracker_geo_by_map

# removing for now to simplify!
# def pull_in_prev_key_map(needed_tracker_geo_by_map, multi_tracker_log_sheet_key):
#     # pull in prev key from relevant map results tab
#     map_log_gsheets = gspread_creds.open_by_key(multi_tracker_log_sheet_key)
#     sheet_names = [sheet.title for sheet in map_log_gsheets.worksheets()]


#     for mapname, list_of_geo_trackers in needed_tracker_geo_by_map.items():
#         maphint = mapname.lower().split(' ')[0]
#         # for sheet in gsheets to find results tab and pull prev map results info for about page
#         for sheet_name in sheet_names:
#             if maphint in sheet_name and 'results' in sheet_name:
#                 sheet = map_log_gsheets.worksheet(sheet_name)
#                 map_results = pd.DataFrame(sheet.get_all_records()(expected_headers=['release date','map updated','tracker-acro','key','download file link','map file link','project count','unit count','capacity total']))
#                 # filter the dataframe so we only have the first row
#                 most_recent_map_results = map_results.iloc[[0]].reset_index(drop=True)
#                 # # printmost_recent_map_results)
#                 # # # # printmost_recent_map_results['release date'])
#                 # # # ##(input('Pause to check most recent map results')
#                 # prev_date = most_recent_map_results['release date'] # only if didn't filter like above on index .iloc[0]
#                 # prev_key = sheet.acell('D2').value.to_list() # will always be this if we do most recent first
#                 prev_key = most_recent_map_results.iloc[0, most_recent_map_results.columns.get_loc('key')]
#                 needed_tracker_geo_by_map[mapname].append(most_recent_map_results) # mapname: [trackers, geo, map_log_results_first_row]
#                 # # printf'For map {mapname} we found the prev key: {prev_key}.')

#     return needed_tracker_geo_by_map


def folder_setup(needed_tracker_geo_by_map):
    
    for mapname, list_of_countries in needed_tracker_geo_by_map.items():
        path_test_results = gem_path + mapname + '/test_results/'
        path_download_and_map_files = gem_path + mapname + '/compilation_output/' # + iso_today_date_folder
        os.makedirs(path_download_and_map_files, exist_ok=True)
        os.makedirs(path_test_results, exist_ok=True)

    return None


###########################
###########################
# PULL IN ALL AET DATA #
# SAVE ALL AET DATA AS LOCAL XLSX or GEOJSON #
# FIRST, PULL IN THE DATA FROM THE GOOGLE SHEET
# CONVERT INTO GDF
# THEN, PULL IN THE DATA FROM THE LOCAL GEOJSON

# def create_prep_file(multi_tracker_log_sheet_key, prep_file_tab): # needed_map_list
#     prep_df = gspread_access_file_read_only(multi_tracker_log_sheet_key, prep_file_tab)
#     prep_df = prep_df[prep_df['official release tab name'] != ''] # skips rows at bottom
#     # Convert 'gspread_tabs' and 'sample_cols' to lists
#     prep_df['gspread_tabs'] = prep_df['gspread_tabs'].apply(lambda x: x.split(';'))
#     # df['sample_cols'] = df['sample_cols'].apply(lambda x: x.split(';'))
#     prep_df['gspread_tabs'] = prep_df['gspread_tabs'].apply(lambda lst: [s.strip() for s in lst])
#     # df['sample_cols'] = df['sample_cols'].apply(lambda lst: [s.strip() for s in lst])
#     prep_df['official name'] = prep_df['official release tab name']

#     prep_df.set_index('official release tab name', inplace=True) # sets index on offical name
#     prep_df['tracker-acro'] = prep_df['tracker-acro']

#     # # if slowmo:

#         # printf'this is prep df: {prep_df}')

#         # # ##(input('Check prep df')
    
#     return prep_df


def pull_gsheet_data(prep_df, needed_tracker_geo_by_map):

    dict_list_dfs_by_map = {} 
    dict_list_gdfs_by_map = {} 
    prep_dict = prep_df.to_dict(orient='index')
    
    for mapname, value in needed_tracker_geo_by_map.items():

        path_for_test_results = gem_path + mapname + '/test_results/'
        os.makedirs(path_for_test_results, exist_ok=True)
        list_dfs_by_map = [] # still use this list to create a list of dfs as we go through all needed trackers
        list_gdfs_by_map = [] # still use this list to create a list of gdfs as we go through all needed trackers
        needed_trackers = value[0] # list of tracker names to include in list of dfs
        needed_geo = value[1] # list of countries or global for gipt to filter each df in the list by
        if local_copy:
            
            print('use pickle format')
            for tracker in needed_trackers:
                # print(f'We are on {tracker}')
                
                if tracker in non_gsheet_data:
                    # # printf'{tracker} is not in gsheet data so skipping this tracker.')
                    continue
                # Load the list of GeoDataFrames from the pickle file
                else:
                    with open(f'local_pkl/{mapname}_{tracker}_df_{iso_today_date}.pkl', 'rb') as f:
                        df = pickle.load(f)
                        list_dfs_by_map.append(df)
                
                    # input('Check correct countries in df for corresponding mapname')  

                    print(f"GeoDataFrames have been loaded from {path_for_test_results}{mapname}_{tracker}_gdf_{iso_today_date}.pkl")

                    
                    with open(f'local_pkl/{mapname}_{tracker}_gdf_{iso_today_date}.pkl', 'rb') as f:
                        gdf = pickle.load(f)
                        list_gdfs_by_map.append(gdf)
                
                    # input('Check correct countries in df for corresponding mapname')  

                    print(f"GeoDataFrames have been loaded from {path_for_test_results}{mapname}_{tracker}_gdf_{iso_today_date}.pkl")

        else:
            for tracker in needed_trackers:
                print(f'We are on {tracker}')
                # input('pause because this is where we have issues with df')
                
                if tracker in non_gsheet_data:
                    # skips all geojson data because already perfect geometry col
                    # # printf'{tracker} is not in gsheet data so skipping this tracker.')
                    continue
                
                else:
                    try:
                        df = gspread_access_file_read_only(prep_dict[tracker]['gspread_key'], prep_dict[tracker]['gspread_tabs'])
                        
                        print(f'Shape of df: {df.shape}')
                        # ##(input('check shape!')
                    
                        
                        # df.to_excel(f'{path_for_test_results}{mapname}_{tracker}_df_{iso_today_date}.xlsx', index=False)
                        # save df as pickle file

                        # Save the list of GeoDataFrames to a pickle file
                        df['tracker-acro'] = prep_dict[tracker]['tracker-acro']
                        df['official_name'] = tracker
                   
                        # df['tracker-acro'] = prep_dict[tracker]['tracker-acro']
                        # df['official_name'] = tracker
                        df = df.replace('*', pd.NA).replace('Unknown', pd.NA).replace('--', pd.NA)
                        df = df.fillna('')
                        col_reg_name, col_country_name = find_region_country_colname(df)
                        # check countries in df against list of official map countries and report issues]

                        # check_countries_official(df, col_country_name, mapname, tracker) # TODO troubleshoot
                        
                        # after this, GGIT-hy will have been filtered just by europe, how do we filter for gas / europe
                        df = create_filtered_df_list_by_map(df,col_country_name, col_reg_name, mapname, needed_geo)
                        # with open(f'local_pkl/{mapname}_{tracker}_df_{iso_today_date}.pkl', 'wb') as f:
                        #     pickle.dump(df, f)

                        # print(f"DataFrames have been saved to {path_for_test_results}{mapname}_{tracker}_df_{iso_today_date}.pkl") 
                        
                        print(f'len of df after filter geo {len(df)}')
                        list_dfs_by_map.append(df)
                        print(list_dfs_by_map)
                        # input('check above was just latam for geojson')
                        # df.to_excel(f'{path_for_test_results}{mapname}_{tracker}_df_{iso_today_date}.xlsx', index=False)
                        with open(f'local_pkl/{mapname}_{tracker}_df_{iso_today_date}.pkl', 'wb') as f:
                            pickle.dump(df, f)

                        print(f"DataFrames have been saved to {path_for_test_results}{mapname}_{tracker}_df_{iso_today_date}.pkl")         
                        # df_dd has all units even with missing coords
                        # df_map only has units with coords
                        df_map, issues_coords = coordinate_qc(df, col_country_name) 
                        print(f'len of df after coordinate qc: {len(df_map)}') 
                        # df.to_excel(f'{path_for_test_results}{mapname}_{tracker}_df-altered-coords_{iso_today_date}.xlsx', index=False)
                        # if len(issues_coords) > 0:
                            
                        #     print(f'These are coordinate issues FIX THEM: {issues_coords}')
                        #     ##(input('please')
                        
                        if 'Latitude' in df_map.columns:
                            print('Latitude in cols')
                            gdf = convert_coords_to_point(df_map) 
                            print(f'len of gdf after convert coords: {len(gdf)}')
                            # append gdf to list of gdfs for map - though now we can have it as a csv for faster AET non tile load
                            list_gdfs_by_map.append(gdf)
                            gdf_to_geojson(gdf, f'{path_for_test_results}{mapname}_{tracker}_gdf_{iso_today_date}.geojson')
                            with open(f'local_pkl/{mapname}_{tracker}_gdf_{iso_today_date}.pkl', 'wb') as f:
                                pickle.dump(gdf, f)


                            print(f"GeoDataFrames have been saved to {path_for_test_results}{mapname}_{tracker}_gdf_{iso_today_date}.pkl")         
                            # if gdf['tracker-acro'].iloc[0] == 'GCTT':
                            #     print(gdf)
                            #     input('This is gctt gdf ... ')
                        else:
                            # print('Latitude not in cols')
                            # print(tracker)
                            # input('check if eu pipelines eventually come up here - if so check the next inputs that they are not empty until "GeoDataFrames have been saved to"')
     
                            df_map = insert_incomplete_WKTformat_ggit_eu(df_map)
                            gdf = convert_google_to_gdf(df_map) # this drops all empty WKTformat cols
                            
                            print(f'len of gdf after convert_google_to_gdf: {len(gdf)}')

                            list_gdfs_by_map.append(gdf)
                            print(list_gdfs_by_map)
                            gdf_to_geojson(gdf, f'{path_for_test_results}{mapname}_{tracker}_gdf_{iso_today_date}.geojson')        
                        
                            # # printf'Added gdf {tracker} for map {mapname} to list of gdfs for map and saved to {path_for_test_results}{mapname}_{tracker}_gdf_{iso_today_date}.geojson.')
                            with open(f'local_pkl/{mapname}_{tracker}_gdf_{iso_today_date}.pkl', 'wb') as f:
                                pickle.dump(gdf, f)

                            print(f"GeoDataFrames have been saved to {path_for_test_results}{mapname}_{tracker}_gdf_{iso_today_date}.pkl")         
                                                
                    except HttpError as e:
                        # Handle rate limit error (HTTP status 429)
                        if e.resp.status == 429:
                            print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                            time.sleep(delay)
                            delay *= 2  # Exponential backoff
                        else:
                            raise e  # Re-raise other errors

                    except Exception as e:
                        print(f"An error occurred: {e}")
                        input('Check why error occurred in pull_gsheet_data function')
                        break
                    
        dict_list_gdfs_by_map[mapname] = list_gdfs_by_map
        dict_list_dfs_by_map[mapname] = list_dfs_by_map

        print(f'This is dict list gdfs by map: {dict_list_gdfs_by_map}')
        print(f'This is dict list dfs by map: {dict_list_dfs_by_map}') #empty for latam
        print(dict_list_gdfs_by_map.keys())
        print(dict_list_dfs_by_map.keys())
        # #(input('check the above')
        # issues_coords_df = pd.DataFrame(issues_coords).to_csv(path_for_test_results + mapname + 'issue_coords_dropped.csv')
            
    return dict_list_dfs_by_map,dict_list_gdfs_by_map

def incorporate_geojson_trackers(goit_geojson, ggit_geojson, ggit_lng_geojson, dict_list_dfs_by_map, dict_list_gdfs_by_map):
    print(f'We are in incorporate geojson functions')
    # test that we don't lose existing gdfs

    pipes_gdf = gpd.read_file(goit_geojson)
    pipes_gdf['tracker-acro'] = 'GOIT'
    pipes_gdf['official_name'] = 'Oil Pipelines'
    # pipes_gdf = find_missing_geo(pipes_gdf) 
    print(len(pipes_gdf))
    pipes_gdf = add_goit_boedcap_from_baird(pipes_gdf)
    print(len(pipes_gdf))
    # input('check that after baird merge function goit')
   
    ggit_gdf = gpd.read_file(ggit_geojson)
    ggit_gdf['tracker-acro'] = 'GGIT'
    ggit_gdf['official_name'] = 'Gas Pipelines'
    # ggit_gdf = find_missing_geo(ggit_gdf)
    print(len(ggit_gdf))
    # ggit_gdf = add_ggit_routes_from_baird(ggit_gdf)
    # print(len(ggit_gdf))
    # input('check that after baird merge function ggit')


    ggit_lng_gdf = gpd.read_file(ggit_lng_geojson)
    ggit_lng_gdf['tracker-acro'] = 'GGIT-lng'
    ggit_lng_gdf['official_name'] = 'LNG Terminals'
    print(len(ggit_lng_gdf))
    
    # ggit_lng_gdf = find_missing_coords(ggit_lng_gdf) # TODO 
##### set up dfs
    pipes_df = pd.DataFrame(pipes_gdf).reset_index(drop=True)
    ggit_df = pd.DataFrame(ggit_gdf).reset_index(drop=True)
    ggit_lng_df = pd.DataFrame(ggit_lng_gdf).reset_index(drop=True)
    
    col_reg_name_pipes, col_country_name_pipes= find_region_country_colname(pipes_gdf)
    col_reg_name_ggit, col_country_name_ggit = find_region_country_colname(ggit_gdf)
    col_reg_name_ggit_lng, col_country_name_ggit_lng = find_region_country_colname(ggit_lng_gdf)
    print('Done with finding column for region name and country name')
    print(col_country_name_pipes)
    incorporated_dict_list_gdfs_by_map = {}
    incorporated_dict_list_dfs_by_map = {}

    # print(f'This is dict: {dict_list_gdfs_by_map}')
    # print(dict_list_gdfs_by_map.keys())

    for mapname, list_of_gdfs in tqdm(dict_list_gdfs_by_map.items(), desc="Processing incorpoate_geojson_trackers"):
        list_of_gdfs_geojson = []
 
        print(f'{mapname}')
        # input('CHECK')
        input(list_of_gdfs)  
         
        if mapname in gas_only_maps:

            if mapname == 'asia':
                needed_geo = asia_countries

                # all but GOIT or pipes since that is for oil
                ggit_gdf_new = create_filtered_df_list_by_map(ggit_gdf, col_country_name_ggit, col_reg_name_ggit, mapname, needed_geo)  
                ggit_lng_gdf_new = create_filtered_df_list_by_map(ggit_lng_gdf, col_country_name_ggit_lng, col_reg_name_ggit_lng,  mapname, needed_geo)  

                list_of_gdfs_geojson.append(ggit_gdf_new)
                list_of_gdfs_geojson.append(ggit_lng_gdf_new) 

                incorporated_dict_list_gdfs_by_map[mapname] = list_of_gdfs_geojson + list_of_gdfs
                
            # elif mapname == 'latam':
            #     needed_geo = latam_countries
            elif mapname == 'europe':
                needed_geo = europe_countries

                # all but GOIT or pipes since that is for oil
                ggit_gdf_new = create_filtered_df_list_by_map(ggit_gdf, col_country_name_ggit, col_reg_name_ggit, mapname, needed_geo)  
                ggit_lng_gdf_new = create_filtered_df_list_by_map(ggit_lng_gdf, col_country_name_ggit_lng, col_reg_name_ggit_lng,  mapname, needed_geo)  

                list_of_gdfs_geojson.append(ggit_gdf_new)
                list_of_gdfs_geojson.append(ggit_lng_gdf_new) 

                incorporated_dict_list_gdfs_by_map[mapname] = list_of_gdfs_geojson + list_of_gdfs
            # elif mapname == 'africa':
            #     needed_geo = africa_countries
            else:
                print(f'This is mapname: {mapname}')
                # input('check this should be asia or europe in gas only')
                    

        else: 
            # list_of_gdfs_geojson = []

            if mapname in ['GIPT', 'Global']: 
                incorporated_dict_list_gdfs_by_map[mapname] = list_of_gdfs 
                pipes_gdf_new = create_filtered_df_list_by_map(pipes_gdf, col_country_name_pipes, col_reg_name_pipes, mapname, needed_geo)  

            # elif mapname == 'asia':
            #     needed_geo = asia_countries
            elif mapname == 'latam':
                needed_geo = latam_countries
                pipes_gdf_new = create_filtered_df_list_by_map(pipes_gdf, col_country_name_pipes, col_reg_name_pipes, mapname, needed_geo)  
                ggit_gdf_new = create_filtered_df_list_by_map(ggit_gdf, col_country_name_ggit, col_reg_name_ggit, mapname, needed_geo)  
                ggit_lng_gdf_new = create_filtered_df_list_by_map(ggit_lng_gdf, col_country_name_ggit_lng, col_reg_name_ggit_lng,  mapname, needed_geo)  

                list_of_gdfs_geojson.append(pipes_gdf_new)
                list_of_gdfs_geojson.append(ggit_gdf_new)
                list_of_gdfs_geojson.append(ggit_lng_gdf_new)

                incorporated_dict_list_gdfs_by_map[mapname] = list_of_gdfs_geojson + list_of_gdfs
            # elif mapname == 'europe':
            #     needed_geo = europe_countries
            elif mapname == 'africa':
                needed_geo = africa_countries
                pipes_gdf_new = create_filtered_df_list_by_map(pipes_gdf, col_country_name_pipes, col_reg_name_pipes, mapname, needed_geo)  
                ggit_gdf_new = create_filtered_df_list_by_map(ggit_gdf, col_country_name_ggit, col_reg_name_ggit, mapname, needed_geo)  
                ggit_lng_gdf_new = create_filtered_df_list_by_map(ggit_lng_gdf, col_country_name_ggit_lng, col_reg_name_ggit_lng,  mapname, needed_geo)  

                list_of_gdfs_geojson.append(pipes_gdf_new)
                list_of_gdfs_geojson.append(ggit_gdf_new)
                list_of_gdfs_geojson.append(ggit_lng_gdf_new)

                incorporated_dict_list_gdfs_by_map[mapname] = list_of_gdfs_geojson + list_of_gdfs
            else:
                print(f'This is mapname: {mapname}')
                # input('check this should be latam africa or gipt')

    # NOW handle dfs    
    for mapname, list_of_dfs in dict_list_dfs_by_map.items():
        list_of_dfs_geojson = []
        print(f'{mapname}')
        # input('CHECK')
        # input(list_of_dfs) #empty latam

        # if mapname in ['GIPT', 'Global']:
        #     incorporated_dict_list_dfs_by_map[mapname] = list_of_dfs  
            
        if mapname in gas_only_maps:

            if mapname == 'asia':
                needed_geo = asia_countries        

                # all but GOIT or pipes since that is for oil
                ggit_df_new = create_filtered_df_list_by_map(ggit_df, col_country_name_ggit, col_reg_name_ggit, mapname, needed_geo)  
                ggit_lng_df_new = create_filtered_df_list_by_map(ggit_lng_df, col_country_name_ggit_lng, col_reg_name_ggit_lng, mapname, needed_geo)  

                list_of_dfs_geojson.append(ggit_df_new)
                list_of_dfs_geojson.append(ggit_lng_df_new) 
                
                incorporated_dict_list_dfs_by_map[mapname] = list_of_dfs_geojson + list_of_dfs   
            
            elif mapname == 'europe':
                needed_geo = europe_countries

                # all but GOIT or pipes since that is for oil
                ggit_df_new = create_filtered_df_list_by_map(ggit_df, col_country_name_ggit, col_reg_name_ggit, mapname, needed_geo)  
                ggit_lng_df_new = create_filtered_df_list_by_map(ggit_lng_df, col_country_name_ggit_lng, col_reg_name_ggit_lng, mapname, needed_geo)  

                list_of_dfs_geojson.append(ggit_df_new)
                list_of_dfs_geojson.append(ggit_lng_df_new) 
                
                incorporated_dict_list_dfs_by_map[mapname] = list_of_dfs_geojson + list_of_dfs 
            else:
                print(f'This is mapname: {mapname}')
                # input('check this should be asia or europe in gas only')
                      
        else:
            if mapname == 'latam':
                needed_geo = latam_countries
                # print(mapname)
                # input('Check if it is africa')
                # it must be LATAM and Africa Energy which takes them all
                pipes_df_new = create_filtered_df_list_by_map(pipes_df, col_country_name_pipes, col_reg_name_pipes,  mapname, needed_geo)  
                ggit_df_new = create_filtered_df_list_by_map(ggit_df, col_country_name_ggit,  col_reg_name_ggit,  mapname, needed_geo)  
                ggit_lng_df_new = create_filtered_df_list_by_map(ggit_lng_df, col_country_name_ggit_lng, col_reg_name_ggit_lng,  mapname, needed_geo)  

                list_of_dfs_geojson.append(pipes_df_new)
                list_of_dfs_geojson.append(ggit_df_new)
                list_of_dfs_geojson.append(ggit_lng_df_new)
                
                incorporated_dict_list_dfs_by_map[mapname] = list_of_dfs_geojson + list_of_dfs   
                
            elif mapname == 'africa':
                needed_geo = africa_countries
                pipes_df_new = create_filtered_df_list_by_map(pipes_df, col_country_name_pipes, col_reg_name_pipes,  mapname, needed_geo)  
                ggit_df_new = create_filtered_df_list_by_map(ggit_df, col_country_name_ggit,  col_reg_name_ggit,  mapname, needed_geo)  
                ggit_lng_df_new = create_filtered_df_list_by_map(ggit_lng_df, col_country_name_ggit_lng, col_reg_name_ggit_lng,  mapname, needed_geo)  

                list_of_dfs_geojson.append(pipes_df_new)
                list_of_dfs_geojson.append(ggit_df_new)
                list_of_dfs_geojson.append(ggit_lng_df_new)
                
                incorporated_dict_list_dfs_by_map[mapname] = list_of_dfs_geojson + list_of_dfs   
            else:
                print(f'This is mapname: {mapname}')
                # input('check this should be latam or africa')
      
    return incorporated_dict_list_gdfs_by_map, incorporated_dict_list_dfs_by_map
    


################
# MAKE MAP FILE #
################

def create_conversion_df(conversion_key, conversion_tab):
    if local_copy:

        # Load the list of GeoDataFrames from the pickle file
        with open('local_pkl/conversion_df.pkl', 'rb') as f:
            df = pickle.load(f)

        print("DataFrames have been loaded from conversion_df.pkl")        
                
    else:
        df = gspread_access_file_read_only(conversion_key, conversion_tab)
        # # # printf'this is conversion df: {df}')
        
        df = df[['tracker', 'type', 'original units', 'conversion factor (capacity/production to common energy equivalents, TJ/y)']]
        df = df.rename(columns={'conversion factor (capacity/production to common energy equivalents, TJ/y)': 'conversion_factor', 'original units': 'original_units'})
        df['tracker'] = df['tracker'].apply(lambda x: x.strip())
        
        with open('local_pkl/conversion_df.pkl', 'wb') as f:
            pickle.dump(df, f)
        print("DataFrames have been saved to conversion_df.pkl")

    return df  


def split_goget_ggit(dict_list_gdfs_by_map):
    custom_dict_list_gdfs_by_map = {}
    
    for mapname, list_gdfs in dict_list_gdfs_by_map.items():
        custom_list_of_gdfs = []
        # # printf'This is length before: {len(list_gdfs)} for {mapname}')
        for gdf in list_gdfs:
            # # # printdf['tracker-acro'])
            gdf = gdf.reset_index(drop=True)
            if gdf['tracker-acro'].iloc[0] == 'GOGET':
                # # # printgdf.columns)
                # oil
                gdf = gdf.copy()
                # df_goget_missing_units.to_csv('compilation_output/missing_gas_oil_unit_goget.csv')
                # gdf['tracker_custom'] = gdf.apply(lambda row: 'GOGET - gas' if row['Production - Gas (Million m³/y)'] != '' else 'GOGET-oil', axis=1)
                gdf['tracker_custom'] = 'GOGET-oil'
                custom_list_of_gdfs.append(gdf)
                
            elif gdf['tracker-acro'].iloc[0] == 'GGIT-lng':
                gdf_ggit_missing_units = gdf[gdf['FacilityType']=='']
                # # printf'GGIT LNG missing units: {gdf_ggit_missing_units}')
                # # # ##(input('Pause to check missing units for GGIT LNG important to know how to calculate capacity factor because differs import and export')
                # gdf_ggit_missing_units.to_csv('compilation_output/missing_ggit_facility.csv')
                gdf = gdf[gdf['FacilityType']!='']
                gdf['tracker_custom'] = gdf.apply(lambda row: 'GGIT-import' if row['FacilityType'] == 'Import' else 'GGIT-export', axis=1)
                # # # printgdf[['tracker_custom', 'tracker-acro', 'FacilityType']])
                custom_list_of_gdfs.append(gdf)

            else:
                gdf['tracker_custom'] = gdf['tracker-acro']
            
                custom_list_of_gdfs.append(gdf)
        custom_dict_list_gdfs_by_map[mapname] = custom_list_of_gdfs
        # # printf'This is length after: {len(custom_list_of_gdfs)} for {mapname}')
    # # printcustom_dict_list_gdfs_by_map.keys())
    # # # ##(input('check that there are enough maps')

    return custom_dict_list_gdfs_by_map



def assign_conversion_factors(custom_dict_list_gdfs_by_map, conversion_df):
    # add column for units 
    # add tracker_custom
    # TODO change these because dict not a list now! dict key is map name, value is list of filtered df of gdf
    # # printcustom_dict_list_gdfs_by_map.keys())
    # # # ##(input('check enough maps')
    # # # ##(input('STOP HERE to see if all maps or not')
    custom_dict_list_gdfs_by_map_with_conversion = {}
    for mapname, list_of_gdfs in custom_dict_list_gdfs_by_map.items():
        custom_list_of_gdfs = []
        # # printmapname)
        # # # ##(input('check mapname in assign_conversion_factors')
        for gdf in list_of_gdfs:

            gdf_initial = gdf.copy()

            # # printgdf['tracker-acro'].loc[0])
            # # printgdf['official_name'].loc[0])

            if gdf['tracker-acro'].iloc[0] == 'GOGET': 
                # # # printf'We are on tracker: {gdf["tracker"].iloc[0]} length: {len(gdf)}')

                for row in gdf.index:
                    if gdf.loc[row, 'tracker_custom'] == 'GOGET-oil':
                        gdf.loc[row, 'original_units'] = conversion_df[conversion_df['tracker']=='GOGET-oil']['original_units'].values[0]
                        gdf.loc[row, 'conversion_factor'] = conversion_df[conversion_df['tracker']=='GOGET-oil']['conversion_factor'].values[0]
                    # elif gdf.loc[row, 'tracker_custom'] == 'GOGET - gas':  
                    #     gdf.loc[row, 'original_units'] = conversion_df[conversion_df['tracker-acro']=='GOGET - gas']['original_units'].values[0]
                    #     gdf.loc[row, 'conversion_factor'] = conversion_df[conversion_df['tracker-acro']=='GOGET - gas']['conversion_factor'].values[0]
                # gdf['tracker-acro'] = 'GOGET' # commenting out not needed
                gdf = gdf.reset_index(drop=True)
                custom_list_of_gdfs.append(gdf)
                
            elif gdf['tracker-acro'].iloc[0] == 'GGIT-lng':
                # # # printf'We are on tracker: {gdf["tracker"].iloc[0]} length: {len(gdf)}')
                for row in gdf.index:
                    if gdf.loc[row, 'tracker_custom'] == 'GGIT-export':
                        gdf.loc[row, 'original_units'] = conversion_df[conversion_df['tracker']=='GGIT-export']['original_units'].values[0]
                        gdf.loc[row, 'conversion_factor'] = conversion_df[conversion_df['tracker']=='GGIT-export']['conversion_factor'].values[0]
                    elif gdf.loc[row, 'tracker_custom'] == 'GGIT-import':  
                        gdf.loc[row, 'original_units'] = conversion_df[conversion_df['tracker']=='GGIT-import']['original_units'].values[0]
                        gdf.loc[row, 'conversion_factor'] = conversion_df[conversion_df['tracker']=='GGIT-import']['conversion_factor'].values[0]
                gdf = gdf.reset_index(drop=True)

                custom_list_of_gdfs.append(gdf)
                
            elif gdf['tracker-acro'].iloc[0] == 'GGIT-eu':
                gdf.loc[row, 'tracker_custom'] = 'GGIT'
                gdf['original_units'] = conversion_df[conversion_df['tracker']=='GGIT']['original_units'].values[0]
                gdf['conversion_factor'] = conversion_df[conversion_df['tracker']=='GGIT']['conversion_factor'].values[0]
                gdf = gdf.reset_index(drop=True)

                custom_list_of_gdfs.append(gdf)  
                
            else:
                # print(f'We are on tracker: {gdf['tracker-acro'].iloc[0]} length: {len(gdf)}')
                # This should apply to all rows not just one.
                if len(gdf) > 0:
                    gdf = gdf.reset_index(drop=True)
                    conversion_df = conversion_df.reset_index(drop=True)
                    print(f'printing this out to troubleshoot no zero: {gdf}')
                    gdf['tracker_custom'] = gdf["tracker-acro"].iloc[0]
                    tracker = gdf["tracker-acro"].iloc[0]
                    print(tracker)
                    print(len(gdf))
                    print(len(conversion_df))
                    gdf['original_units'] = conversion_df[conversion_df['tracker']==tracker]['original_units'].values[0]
                    gdf['conversion_factor'] = conversion_df[conversion_df['tracker']==tracker]['conversion_factor'].values[0]
                    custom_list_of_gdfs.append(gdf)                
                else:
                    print("gdf is empty!")
                

        custom_dict_list_gdfs_by_map_with_conversion[mapname] = custom_list_of_gdfs
    # # printf'This is custom dict: {custom_dict_list_gdfs_by_map_with_conversion}')
    # # # ##(input('Check it, should have all trackers not just pipes!')
    
    # # printcustom_dict_list_gdfs_by_map_with_conversion.keys())
    # # # ##(input('check that there are enough maps')
    return custom_dict_list_gdfs_by_map_with_conversion


def rename_gdfs(custom_dict_list_gdfs_by_map_with_conversion):
    # This function takes a dictionary and renames columns for all dataframes within
    # then it concats by map type all the dataframes
    # so you're left with a dictionary by maptype that holds one concatted dataframe filterd on geo and tracker type needed
    renamed_one_gdf_by_map = {}
    # # printcustom_dict_list_gdfs_by_map_with_conversion.keys())
    # # # ##(input('STOP HERE to see if all maps or not')
    for mapname, list_of_gdfs in custom_dict_list_gdfs_by_map_with_conversion.items():
        
        renamed_gdfs = []
        path_for_test_results = gem_path + mapname + '/test_results/'
        # # printmapname)
        # # printlen(list_of_gdfs))
        # # printgdf['tracker-acro']) for gdf in list_of_gdfs]
        # # # ##(input('Check if all trackers are there')
        for gdf in list_of_gdfs:
            # for col in gdf.columns:
            #     print(col)
            # print(gdf.columns)
            # if 'Countries' in gdf.columns:
            #     print(gdf['Countries'])
            # declare which tracker we are at in the list so we can rename columns accordingly
            tracker_sel = gdf['tracker-acro'].iloc[0] # GOGPT, GGIT, GGIT-lng, GOGET
            
            # if tracker_sel == 'GCTT':
            #     print(gdf)
            #     input('GCTT gdf here')
            print(f'renaming on tracker: {tracker_sel}')
            # all_trackers.append(tracker_sel)
            # select the correct renaming dict from config.py based on tracker name
            renaming_dict_sel = renaming_cols_dict[tracker_sel]
            # rename the columns!
            gdf = gdf.rename(columns=renaming_dict_sel) 
            
            # print(gdf['areas'].value_counts())
            # ##(input('check value counts for area after rename')
            gdf.reset_index(drop=True, inplace=True)  # Reset index in place
            # print('here are the cols newly renamed ')
            # for col in gdf.columns:
            #     print(col)
            renamed_gdfs.append(gdf)
            # print(f'This is renamed_gdfs so far {renamed_gdfs}')
            # #(input('tChek this')


        print(f'This is renamed_gdfs after the look {renamed_gdfs}')

    
        one_gdf = pd.concat(renamed_gdfs, sort=False, verify_integrity=True, ignore_index=True) 
        # one_gdf = one_gdf.drop_duplicates('id').reset_index(drop=True)
        print(one_gdf.index)

        cols_to_be_dropped = set(one_gdf.columns) - set(final_cols)
        # # if slowmo:
            # # ##(input('Pause to check cols before filtering out all cols in our gdf that are not in final cols, there will be a problem if our gdf does not have a col in final_cols.')
        final_gdf = one_gdf.drop(columns=cols_to_be_dropped)
        # instead of filtering on a preset list, drop the extra columns using cols_to_be_dropped
        # final_gdf = one_gdf[final_cols]
        
        # final_gdf.to_csv(f'{path_for_test_results}renamed_one_df_{iso_today_date}.csv',  encoding="utf-8")
        renamed_one_gdf_by_map[mapname] = final_gdf 
        # # print'Going on to next mapname')
    return renamed_one_gdf_by_map


def create_search_column(dict_of_gdfs):
    # this can be one string with or without spaces 
    # this creates a new column for project and project in local language
    # in the column it'll be removed of any diacritics 
    # this allows for quick searching
    #     for mapname, one_gdf in cleaned_dict_map_by_one_gdf.items():
    dict_of_gdfs_with_search = {}
    for mapname, one_gdf in dict_of_gdfs.items():

        print('testing create_search_column with no diacritics for first time')
        col_names = ['plant-name', 'parent(s)', 'owner(s)', 'operator(s)', 'name', 'owner', 'parent']
        for col in col_names:
            if col in one_gdf.columns:
                print(one_gdf[col].head(10))
                new_col_name = f'{col}_search'
                one_gdf[new_col_name] = one_gdf[col].apply(lambda x: remove_diacritics(x))
                print(one_gdf[new_col_name].head(10))
        
        dict_of_gdfs_with_search[mapname] = one_gdf
        
        print(dict_of_gdfs_with_search.keys)
        print('above are keys in dict_of_gdfs_with_search')
    return dict_of_gdfs_with_search


def capacity_conversions(cleaned_dict_map_by_one_gdf): 

# you could multiply all the capacity/production values in each tracker by the values in column C, 
# "conversion factor (capacity/production to common energy equivalents, TJ/y)."
# For this to work, we have to be sure we're using values from each tracker that are standardized
# to the same units that are stated in this sheet (column B, "original units").

# need to get nuances for each tracker, it's just GGIT if point then do lng terminal if line then do pipeline
    cleaned_dict_map_by_one_gdf_with_conversions = {}
    for mapname, one_gdf in cleaned_dict_map_by_one_gdf.items():
        gdf_converted = one_gdf.copy()
        if mapname in gas_only_maps:
            print('no need to handle for hydro having two capacities')
            print(gdf_converted.columns)
            # continue
        else:
            # first let's get GHPT cap added 
            # # printmapname) # africa
            # # printset(gdf_converted['tracker-acro'].to_list())) # only pipeline 
            ghpt_only = gdf_converted[gdf_converted['tracker-acro']=='GHPT'] # for GGPT we need to re run it to get it 
            print(len(ghpt_only))
            print(mapname)
            # ##(input('check')
            gdf_converted = gdf_converted[gdf_converted['tracker-acro']!='GHPT']
            # # printlen(ghpt_only['capacity']))
            # # printlen(ghpt_only['capacity1']))
            # # printlen(ghpt_only['capacity2']))
            # # # ##(input('Check that they are all equal GHPT')
            ghpt_only['capacity'] = ghpt_only.apply(lambda row: row['capacity'] + row['capacity2'], axis=1)
            gdf_converted = pd.concat([gdf_converted, ghpt_only],sort=False).reset_index(drop=True)
        # # # printlen(gdf_converted))
    
        gdf_converted['cleaned_cap'] = pd.to_numeric(gdf_converted['capacity'], errors='coerce')

        total_counts_trackers = []
        avg_trackers = []
        print(gdf_converted.columns)
        # print(f"this is all trackers: {set(gdf_converted['tracker-acro'].to_list())}")
        
        # gdf_converted['tracker-acro'] = gdf_converted['tracker-acro']
        # # printf"this is all trackers: {set(gdf_converted['tracker-acro'].to_list())}")
        
        gdf_converted = gdf_converted[gdf_converted['tracker-acro']!=''] # new to filter out nan


        for tracker in set(gdf_converted['tracker-acro'].to_list()):
            # for singular map will only go through one
            total = len(gdf_converted[gdf_converted['tracker-acro'] == tracker])
            sum = gdf_converted[gdf_converted['tracker-acro'] == tracker]['cleaned_cap'].sum()
            avg = sum / total
            total_pair = (tracker, total)
            total_counts_trackers.append(total_pair)
            avg_pair = (tracker, avg)
            avg_trackers.append(avg_pair)
            
        for row in gdf_converted.index:
            cap_cleaned = gdf_converted.loc[row, 'cleaned_cap']
            tracker = gdf_converted.loc[row, 'tracker-acro']
            if pd.isna(cap_cleaned):
                for pair in avg_trackers:
                    if pair[0] == tracker:
                        gdf_converted.loc[row, 'cleaned_cap'] = pair[1]
            cap_cleaned = gdf_converted.loc[row, 'cleaned_cap']
            # if pd.isna(cap_cleaned):
                # print'still na')
                # # ##(input('still na')
    

        pd.options.display.float_format = '{:.0f}'.format
        # gdf_converted['ea_scaling_capacity'] = gdf_converted.apply(lambda row: conversion_equal_area(row), axis=1) # square root(4 * capacity / pi)

        gdf_converted['scaling_capacity'] = gdf_converted.apply(lambda row: conversion_multiply(row), axis=1)
        # must be float for table to sort
        gdf_converted['capacity-table'] = gdf_converted.apply(lambda row: pd.Series(workaround_table_float_cap(row, 'capacity')), axis=1)
        gdf_converted['units-of-m'] = gdf_converted.apply(lambda row: pd.Series(workaround_table_units(row)), axis=1)
        # gdf_converted['units-of-m'] = gdf_converted.apply(lambda row: '' if 'GOGET' in row['tracker-acro'] else row['units-of-m'], axis=1)

        # below doesn't work cap details was empty all the time
        # gdf_converted = workaround_no_sum_cap_project(gdf_converted) # adds capacity-details for singular maps we can just disregard
        # TODO nov 13 test this I think it now adds all cap for a project and applies the original units to it 
        # gdf_converted['capacity-details-unit'] = gdf_converted.apply(lambda row: workaround_display_cap(row, 'capacity-details'), axis=1)
    
        cleaned_dict_map_by_one_gdf_with_conversions[mapname] = gdf_converted
    
        
    # # printcleaned_dict_map_by_one_gdf_with_conversions.keys())
    # # # ##(input('check that there are enough maps')
    return cleaned_dict_map_by_one_gdf_with_conversions


def map_ready_statuses(cleaned_dict_map_by_one_gdf_with_conversions):
    cleaned_dict_by_map_one_gdf_with_better_statuses = {}
    for mapname, gdf in cleaned_dict_map_by_one_gdf_with_conversions.items():
        path_for_test_results = gem_path + mapname + '/test_results/'           

        # print(set(gdf['status'].to_list()))
        mask_gbpt = gdf['tracker-acro'] == 'GBPT'
        # print(gdf.loc[mask_gbpt, 'status'])
        # #(input('check statuses of bio before')
        
        gdf['status'] = gdf['status'].fillna('Not Found') # ValueError: Cannot mask with non-boolean array containing NA / NaN values
        gdf['status'] = gdf['status'].replace('', 'Not Found') # ValueError: Cannot mask with non-boolean array containing NA / NaN values
        # print(set(gdf['status'].to_list()))
        gdf_map_ready = fix_status_inferred(gdf)
        
        # Create masks for the 'tracker-acro' conditions
        mask_gcmt = gdf_map_ready['tracker-acro'] == 'GCMT'
        mask_goget = gdf_map_ready['tracker-acro'] == 'GOGET'
        mask_gbpt = gdf_map_ready['tracker-acro'] == 'GBPT'
        
        # Update 'status' to 'Retired' where both masks are True
        gdf_map_ready['status'].fillna('', inplace=True)
        mask_status_empty = gdf_map_ready['status'] == ''
        # print(mask_status_empty)
        # # #(input('check the above for empty statuses')
        # print(gdf_map_ready.loc[mask_gbpt, 'status'])
        # #(input('check statuses of bio')
        
        # Update 'status' to 'Not Found' where both masks are True
        gdf_map_ready.loc[mask_status_empty & mask_gcmt, 'status'] = 'retired'
        gdf_map_ready.loc[mask_status_empty & mask_goget, 'status'] = 'not found'
        gdf_map_ready['status_legend'] = gdf_map_ready.copy()['status'].str.lower().replace({
                    # proposed_plus
                    'proposed': 'proposed_plus',
                    'announced': 'proposed_plus',
                    'discovered': 'proposed_plus',
                    # pre-construction_plus
                    'pre-construction': 'pre-construction_plus',
                    'pre-permit': 'pre-construction_plus',
                    'permitted': 'pre-construction_plus',
                    # construction_plus
                    'construction': 'construction_plus',
                    'in development': 'construction_plus',
                    # mothballed
                    'mothballed': 'mothballed_plus',
                    'idle': 'mothballed_plus',
                    'shut in': 'mothballed_plus',
                    # retired
                    'retired': 'retired_plus',
                    'closed': 'retired_plus',
                    'decommissioned': 'retired_plus',
                    'not found': 'not-found'})


        # Create a mask for rows where 'status' is empty

        gdf_map_ready_no_status = gdf_map_ready.loc[mask_status_empty]
        # # # ##(input(f'check no status df: {gdf_map_ready_no_status}')

        gdf_map_ready_no_status.to_csv(f'issues/no-status-{mapname}_{iso_today_date}.csv')
        # make sure all statuses align with no space rule
        # gdf_map_ready['status'] = gdf_map_ready['status'].apply(lambda x: x.strip().replace(' ','-'))
        gdf_map_ready['status_legend'] = gdf_map_ready['status_legend'].apply(lambda x: x.strip().replace('_','-'))
        # # printset(gdf_map_ready['status'].to_list()))
        gdf_map_ready['status'] = gdf_map_ready['status'].apply(lambda x: x.lower())
        # # printset(gdf_map_ready['status'].to_list()))
        
        cleaned_dict_by_map_one_gdf_with_better_statuses[mapname] = gdf_map_ready
    
    # # printcleaned_dict_by_map_one_gdf_with_better_statuses.keys())
    # # # ##(input('check that there are enough maps')
    return cleaned_dict_by_map_one_gdf_with_better_statuses



def map_ready_countries(cleaned_dict_by_map_one_gdf_with_better_statuses):
    cleaned_dict_by_map_one_gdf_with_better_countries = {}
    for mapname, gdf in cleaned_dict_by_map_one_gdf_with_better_statuses.items():
        print(f'We are on mapname: {mapname}')
        
        # check that areas isn't empty
        tracker_sel = gdf['tracker-acro'].iloc[0]
        # if tracker_sel == 'GCTT':
        #     print(gdf['areas'])
        gdf['areas'] = gdf['areas'].fillna('')

        empty_areas = gdf[gdf['areas']=='']
        if len(empty_areas) > 0:
            print(f'Check out which rows are empty for countries for map: {mapname}')
            print(empty_areas)
            # #(input('Remove above')
            empty_areas.to_csv(f'issues/empty-areas-{tracker_sel}{iso_today_date}.csv')

        # this formats subnational area for detail maps
        # we would also want to overwrite the subnat and say nothing ""
        gdf['count-of-semi'] = gdf.apply(lambda row: row['areas'].strip().split(';'), axis=1) # if len of list is more than 2, then split more than once
        gdf['count-of-semi'] = gdf.apply(lambda row: row['areas'].strip().split('-'), axis=1) # for goget
        gdf['count-of-semi'] = gdf.apply(lambda row: row['areas'].strip().split(','), axis=1) # just adding in case

        gdf['multi-country'] = gdf.apply(lambda row: 't' if len(row['count-of-semi']) > 1 else 'f', axis=1)
        # # printgdf['multi-country'])
        # if t then make areas-display 
        gdf['subnat'].fillna('', inplace=True)
        # if one country and subnat exists TEST THIS
        gdf['areas-subnat-sat-display'] = gdf.apply(lambda row: f"{row['subnat'].strip().strip('')}, {row['areas'].strip().strip('')}" if row['multi-country'] == 'f' and row['subnat'] != '' else row['areas'].strip(), axis=1) # row['areas'].strip()
        # if more than one country replace the '' with mult countries
        
        # print('Printing all count of semi more than 1')
        # print(gdf[gdf['count-of-semi'].apply(len) > 1])
        # print('Printing multi-country t')
        # print(gdf[gdf['multi-country']=='t'])
        
        # print(gdf[gdf['name']== 'Mexico-Northern Central America Gas Pipeline'])
        # #(input('This should be not empty!')
        maskt = gdf['multi-country']=='t'
        # print(len(maskt))
        # #(input('check more than just hydro')
        gdf.loc[maskt, 'areas-subnat-sat-display'] = 'multiple areas/countries'
        # print(gdf[gdf['areas-subnat-sat-display']!=''])
        # print(gdf[gdf['id']=='P0539'])
        # #(input('check subnat mult countries test')
        # just need to make sure all countries are separated by a comma and have a comma after last country as well
        # GOGET has a hyphen in countries
        # GOIT has comma separated in countries
        # hydropower has two columns country1 and country2
        # GGIT has comma separated in countries
        # grouped_tracker_before = gdf.groupby('tracker-acro', as_index=False)['id'].count()
        # # # printf'In map ready before adjustment: {grouped_tracker_before}')
        # # no return

        # gdf_map_ready['area2'] = gdf_map_ready['area2'].fillna('')
            
        if mapname in gas_only_maps:
            # handle for gas only maps
            print('In not map only area of function')
            gdf['areas'] = gdf['areas'].fillna('')
            gdf['areas'] = gdf['areas'].str.replace(',', ';')
            gdf['areas'] = gdf['areas'].apply(lambda x: f"{x.strip()};")
            print(gdf['areas'])
            # input('check above has semicolon')
        
        else: 
            
            # print(gdf_map_ready[['areas', 'tracker-acro', 'name']])
            # print(set(gdf_map_ready['areas'].to_list()))
            # print(set(gdf_map_ready['area2'].to_list()))
            gdf['area2'] = gdf['area2'].fillna('')
            gdf['areas'] = gdf['areas'].fillna('')
            # print(set(gdf['areas'].to_list()))
            # print(set(gdf['area2'].to_list()))
            nan_areas = gdf[gdf['areas']=='']
            print(f'Nan areas: {len(nan_areas)}')
            # print(nan_areas)
            input('check nan areas')
            issues = []
            tracker_issues = []
            for row in gdf.index:
                if gdf.loc[row, 'areas'] == '':
                    issues.append(row)
                    tracker_issues.append(gdf.loc[row, 'tracker-acro'])
            # if len(issues) >0 :
            #     print(f'No areas here for these trackers:')
            #     print(set(tracker_issues))
            gdf = gdf.drop(issues)
            issues_df = {'missing_country': issues}
            issues_df = pd.DataFrame(issues_df)
            issues_df.to_csv(f'issues/missing_county{mapname}{iso_today_date}.csv')
            print('Printed issues_df to file and dropped themf rom the df.')
            # ##(input('All area2s in gdf check if any are numbers')
            if mapname == 'Global':
                gdf['areas'] = f"{gdf['areas']};"
                
            else:
                for row in gdf.index:

                    if gdf.loc[row, 'area2'] != '':
        
                        gdf.at[row, 'areas'] = f"{gdf.loc[row, 'areas'].strip()};{gdf.loc[row, 'area2'].strip()};"
                        # print(f"Found a area2! Hydro? {gdf.loc[row, 'areas']} {gdf.loc[row, 'tracker-acro']} {gdf.loc[row, 'name']}")
                    
                    else:
                        # make it so all areas even just one end with a semincolon 
                        gdf['areas'] = gdf['areas'].fillna('')
                        # nan_areas = gdf[gdf['areas']=='']
                        # print(f'in else: {set(gdf["areas"].to_list())}') # find the rows that are nan or float
                        ser = gdf['areas']
                        try:
                            ser_str = ser.astype(str)
                        except:
                            for row in ser.index:
                                val = ser.iloc[row]
                                try:
                                    val_str = str(val)
                                except:
                                    print("Error!" + f" val couldn't be converted to str: {val}")
                        
                        gdf.at[row, 'areas'] = f"{gdf.loc[row, 'areas'].strip()};"

        # grouped_tracker_after = gdf.groupby('tracker-acro', as_index=False)['id'].count()

        # # # printf'In map ready after adjustment: {grouped_tracker_after}')
        # print(gdf.head())
        # print(gdf.columns)
        # #(input('check if semi and multi here?')
        cleaned_dict_by_map_one_gdf_with_better_countries[mapname] = gdf  
    # # printcleaned_dict_by_map_one_gdf_with_better_countries.keys())
    # # # ##(input('check that there are enough maps')
    return cleaned_dict_by_map_one_gdf_with_better_countries


def workarounds_eg_interim_goget_gcmt(cleaned_dict_by_map_one_gdf_with_better_countries):
    # this function mostly creates a new col for correctly formatted info when there is multiple countries, especially for the details card 
    # it also handles oil and gas for goget, TODO should add removal of oil for gas only map maybe? 
    one_gdf_by_maptype = {}
    for mapname, gdf in cleaned_dict_by_map_one_gdf_with_better_countries.items():
        gdf = gdf.copy()

        list_invalid_goget = []
        list_invalid_gcmt = []
        if mapname in ['GIPT', 'Global']:
            # does not have goget
            one_gdf_by_maptype[mapname] = gdf 
            
        else:
            # # # printgdf.columns)
            # # # ##(input('Check if prod-oil is there in columns')
            for row in gdf.index:

                tracker = (gdf.loc[row, 'tracker-acro'])
                #if goget then make capacity table and capacity details empty
                

                if tracker == 'GOGET':
                    gdf.loc[row, 'capacity-table'] = np.nan
                    gdf.loc[row, 'capacity-details'] = ''
                    prod_oil = gdf.loc[row, 'prod_oil']
                    prod_gas = gdf.loc[row, 'prod_gas']
                    prod_oil = check_and_convert_float(prod_oil) # NEW TO TEST FOR ROUNDING ALL GETTING CAUGH TIN INVALID GOGET
                    prod_gas = check_and_convert_float(prod_gas)

                    # try: # NEW TO DO TEST REMOVING THIS
                    #     # round it then if either is '' we can remove it later we filter on it before adding to table or details
                    #     prod_oil = prod_oil.replace(r'[^\d.-]', '', regex=True)
                    #     prod_oil= prod_oil.replace('', np.nan)
                    #     prod_oil = prod_oil.astype(float)     
    
                    #     prod_oil = str(float(round(prod_oil, 2)))

                    #     gdf.loc[row, 'prod-oil-table'] = f'{prod_oil} million bbl/y'
                    #     gdf.loc[row, 'prod-oil-details'] = f'{prod_oil} (million bbl/y)'
                    #     gdf['prod_year_gas'] = gdf['prod_year_gas'].fillna('')
                    #     gdf['prod_year_oil'] = gdf['prod_year_oil'].fillna('')
                    #     # # prod oil year an prod gas year replace -1 with not found, this was what Scott had done to replace not stated, once incorporated his code we can see if we can adjust then remove this
                    #     # not needed in map file because js does filtering to empty stringbut to be consistent
                    #     gdf['prod_year_gas'] = gdf['prod_year_gas'].apply(lambda x: str(x).replace('-1', '[not found]'))
                    #     gdf['prod_year_oil'] = gdf['prod_year_oil'].apply(lambda x: str(x).replace('-1', '[not found]'))
                                
                    # except:
                    #     list_invalid_goget.append(prod_oil)
                    #     # # print'invalid goget')
                    #     # TODO handle these cases and then create a test to confirm it's fixed
                        
                        
                    # try:
                    #     prod_gas = prod_gas.replace(r'[^\d.-]', '', regex=True)
                    #     prod_gas  = prod_gas .replace('', np.nan)

                    #     prod_gas = str(float(round(prod_gas, 2)))
                    #     prod_gas  = prod_gas.astype(float)

                    #     gdf.loc[row, 'prod-gas-table'] = f'{prod_gas} million m³/y'
                    #     gdf.loc[row, 'prod-gas-details'] = f'{prod_gas} (million m³/y)'
                        
                    # except:
                    #     list_invalid_goget.append(prod_gas)

                    #     # # print'invalid goget')
                        # TODO handle these cases and then create a test to confirm it's fixed
                elif tracker == 'GCMT':
                    gdf.loc[row, 'capacity-table'] = np.nan
                    gdf.loc[row, 'capacity-details'] = ''
                    prod_coal = gdf.loc[row, 'prod-coal']                    
                else:
                    continue
        one_gdf_by_maptype[mapname] = gdf 
    # # printone_gdf_by_maptype.keys())
    return one_gdf_by_maptype

def add_goit_boedcap_from_baird(gdf):
    # set up fixed goit file pd
    goit_cap_boed = gpd.read_file(goit_cap_updated)
    print(goit_cap_boed.info())
    # goit_cap_boed.drop(columns=['Capacity'], inplace=True) # there is already a capacity that exists

    # goit_cap_boed = goit_cap_boed.rename(columns={'ProjectID':'id', 'CapacityBOEd': 'capacity'})

    # Merge goit_cap_boed with the main gdf on 'id'
    gdf = gdf.merge(goit_cap_boed[['ProjectID', 'CapacityBOEd']], on='ProjectID', how='left', suffixes=('', '_new'))
    
    # Update the 'capacity_boed' column in gdf with the new values where there is a match
    gdf['CapacityBOEd'] = gdf['CapacityBOEd_new'].combine_first(gdf['CapacityBOEd'])
    
    # Drop the temporary 'capacity_boed_new' column
    gdf.drop(columns=['CapacityBOEd_new'], inplace=True)
    print('AFTER')
    
    print(len(gdf))

    # for col in gdf.columns:
    #     print(col)
    print(gdf.info())
    # input('Check the above...')
    return gdf
  
    
def add_ggit_routes_from_baird(gdf):
    # pull in capacity boed from new goit file on projectID
    # pull in routes from new ggit file on projectID

    print('BEFORE')
    print(len(gdf))
    print(gdf.info())
  
    # set up fixed ggit file pd
    ggit_routes = gpd.read_file(ggit_routes_updated)
    
    # ggit_routes = ggit_routes.rename(columns={'ProjectID':'id'})

    # Merge ggit_routes with the main gdf on 'id'
    gdf = gdf.merge(ggit_routes[['ProjectID', 'geometry']], on='ProjectID', how='left', suffixes=('', '_new'))

    # Update the 'route' column in gdf with the new values where there is a match
    gdf['geometry'] = gdf['geometry_new'].combine_first(gdf['geometry'])
    
    # Drop the temporary 'route_new' column
    gdf.drop(columns=['geometry_new'], inplace=True)
    
    print('AFTER')
    
    print(len(gdf))

    # for col in gdf.columns:
    #     print(col)
    print(gdf.info())
    # input('Check the above...')
    return gdf

# TODO
def manual_lng_pci_eu_temp_fix(gdf):
    print('add in lng pci info for eu ggit with function manual_lng_pci_eu_temp_fix !')
    # Polish Baltic Sea Coast FSRU and Cyprus LNG terminal
    # pci 5 for pci-list colu
    lng_mask_1 = gdf['name'] == 'Polish Baltic Sea Coast FSRU'
    print(lng_mask_1)
    gdf.loc[lng_mask_1, 'pci-list'] = '5'
    print(gdf[gdf['name']=='Polish Baltic Sea Coast FSRU'])
    input('check it changed mask1')
    # print(lng_mask_1)
    lng_mask_2 = gdf['id'] == 'T043200'
    gdf.loc[lng_mask_2, 'pci-list'] = '5'
    print(lng_mask_2)
    print(gdf[gdf['id']=='T043200'])
    input('check it changed mask2')

    return gdf

def swap_gas_methane(gdf):
    mask1 = gdf['fuel'] == 'Gas'
    print('before')
    print(gdf[gdf['fuel']=='Gas'])

    # print(gdf.loc[mask1])
    # gdf.loc[mask1, 'fuel'] = 'methane'
    
    gdf.loc[mask1, 'fuel'] = 'Methane'
    print('after')
    print(gdf[gdf['fuel']=='Methane'])
    input('check methane change')
    return gdf

def last_min_fixes(one_gdf_by_maptype):
    one_gdf_by_maptype_fixed = {}
    # # printone_gdf_by_maptype.keys())
    # # # ##(input('check that GIPT is in the above')
    for mapname, gdf in one_gdf_by_maptype.items():            # do filter out oil
        gdf = gdf.copy()
        # # printlen(gdf))
        # gdf['name'] = gdf['name'].fillna('')
        # gdf['url'] = gdf['url'].fillna('')
        # gdf['geometry'] = gdf['geometry'].fillna('')
        # # printgdf.columns)
        # TODO for now remove drop to understand why all GOGET empty is now not being filled and also prod doesn't come through
        # gdf = gdf.drop(['original_units','conversion_factor', 'area2', 'region2', 'subnat2', 'capacity1', 'capacity2', 'Latitude', 'Longitude'], axis=1) # 'cleaned_cap'
        # handle countries/areas ? 
        # gdf['areas'] = gdf['areas'].apply(lambda x: x.replace('Guinea,Bissau','Guinea-Bissau')) # reverse this one special case back 
        # # printf'Missing areas: {gdf[gdf["areas"]==""]}') # check if missing!!   
        # # # ##(input('Handle missing countries')
        # handle situation where Guinea-Bissau IS official and ok not to be split into separate countries 
        gdf['areas'] = gdf['areas'].apply(lambda x: x.replace('Guinea,Bissau','Guinea-Bissau')) 
        
        # something is happening when we concat, we lose goget's name ... 
        # gdf_empty_name = gdf[gdf['name']=='']
        # # # printf"This is cols for gdf: {gdf.columns}")
        gdf['name'].fillna('',inplace=True)
        gdf['name'] = gdf['name'].astype(str)

        gdf['wiki-from-name'] = gdf.apply(lambda row: f"https://www.gem.wiki/{row['name'].strip().replace(' ', '_')}", axis=1)
        # row['url'] if row['url'] != '' else 
        # handles for empty url rows and also non wiki cases SHOULD QC FOR THIS BEFOREHAND!! TO QC
        # need to switch to '' not nan so can use not in
        gdf['url'].fillna('',inplace=True)
        gdf['url'] = gdf.apply(lambda row: row['wiki-from-name'] if 'gem.wiki' not in row['url'] else row['url'], axis=1)
        
        # gdf['name'] = gdf.apply(lambda row: row['name'] if row['name'] != '' else row['url'].split('www.gem.wiki/')[1].replace('_', ' '))

        # gdf_empty_url = gdf[gdf['url'] == '']

        # assign Africa to all regions
        # gdf['region'] = 'Africa'
        # list_of_needed_geo_countries = needed_geo_for_region_assignment[mapname][1]
        # # printlist_of_needed_geo_countries)
        # DO WE WANT THIS FOR SOME REASON? probalby not for the cross-continental ones...
        # # # ##(input('Check this is a list of countries, otherwise may need to adjust how we access the 2nd value of the dictionary') # if it is then we can assign a region based off of it
        # if 'Brazil' in list_of_needed_geo_countries:
        #     gdf['region'] = 'Americas'
        # elif 'China' in list_of_needed_geo_countries:
        #     gdf['region'] = 'Asia'
        # elif 'Mozambique' in list_of_needed_geo_countries:
        #     gdf['region'] = 'Africa'
        # elif 'United Kingdom' in list_of_needed_geo_countries:
        #     gdf['region'] = 'Europe'
        # else:
        #     gdf['region'] = ''
            # # printf'No region found for gdf: {gdf["tracker"].iloc[0]} for map: {mapname}')
            
        # print(gdf.columns)

        gdf.columns = [col.replace('_', '-') for col in gdf.columns] 
        gdf.columns = [col.replace('  ', ' ') for col in gdf.columns] 
        gdf.columns = [col.replace(' ', '-') for col in gdf.columns] 

        # print(gdf.columns)
        # ##(input('check cols')
        # gdf['tracker-acro'] = gdf['tracker-acro']   
        # let's also look into empty url, by tracker I can assign a filler
        
        # gdf['url'] = gdf['url'].apply(lambda row: row[filler_url] if row['url'] == '' else row['url'])
        
        # gdf['capacity'] = gdf['capacity'].apply(lambda x: x.replace('--', '')) # can't do that ... 
        
        # translate acronyms to full names 
        
        gdf['tracker-display'] = gdf['tracker-custom'].map(tracker_to_fullname)
        gdf['tracker-legend'] = gdf['tracker-custom'].map(tracker_to_legendname)
        # # # printset(gdf['tracker-display'].to_list()))
        # # # printf'Figure out capacity dtype: {gdf.dtypes}')
        gdf['capacity'] = gdf['capacity'].apply(lambda x: str(x).replace('--', ''))
        gdf['capacity'] = gdf['capacity'].apply(lambda x: str(x).replace('*', ''))

        gdf.dropna(subset=['geometry'],inplace=True)
        # gdf['capacity'] = gdf['capacity'].fillna('')
        # gdf['capacity'] = gdf['capacity'].apply(lambda x: x.replace('', pd.NA))
        # gdf['capacity'] = gdf['capacity'].astype(float) # Stuck with concatting like strings for now? ValueError: could not convert string to float: ''
        
        
        if mapname == 'europe':
            print(mapname)
            gdf = pci_eu_map_read(gdf)
            gdf = assign_eu_hydrogen_legend(gdf)
            gdf = gdf[gdf['tracker-acro']!='GGIT']
            gdf = manual_lng_pci_eu_temp_fix(gdf)
            gdf = swap_gas_methane(gdf)
        
        one_gdf_by_maptype_fixed[mapname] = gdf
    # # printone_gdf_by_maptype_fixed.keys())
    return one_gdf_by_maptype_fixed

def create_map_file(one_gdf_by_maptype_fixed):
    final_dict_gdfs = {}
    # # printone_gdf_by_maptype_fixed.keys())
    # # # ##(input('STOP HERE - why only one map being printed??')

    for mapname, gdf in one_gdf_by_maptype_fixed.items():
        print(mapname)
        print(f'Saving file for map {mapname}')
        print(f'This is len of gdf {len(gdf)}')
        path_for_download_and_map_files = gem_path + mapname + '/compilation_output/'

        # # printf'We are on map: {mapname} there are {len(one_gdf_by_maptype_fixed)} total maps')
        # # printf"This is cols for gdf: {gdf.columns}")
        # # # ##(input('STOP HERE')
        # drop columns we don't need because has a list in it and that csuses issues when printing to files
        # if 'count_of_semi' in gdf.columns.to_list(): # TODO THIS should be in all ggit trackers so odd that it didnt' get pinged
        #     gdf = gdf.drop(['count_of_semi', 'multi-country', 'original-units', 'conversion-factor', 'cleaned-cap', 'wiki-from-name', 'tracker-legend'], axis=1)
        print(gdf.columns)
        # #(input('check if prod-coal is there')
        if mapname in gas_only_maps: # will probably end up making all regional maps all energy I would think
            gdf = gdf.drop(['count-of-semi', 'multi-country', 'original-units', 'conversion-factor', 'cleaned-cap', 'wiki-from-name', 'tracker-legend'], axis=1) # 'multi-country', 'original-units', 'conversion-factor', 'cleaned-cap', 'wiki-from-name', 'tracker-legend']
        
        else:
            gdf = gdf.drop(['count-of-semi','multi-country', 'original-units', 'conversion-factor', 'area2', 'region2', 'subnat2', 'capacity2', 'cleaned-cap', 'wiki-from-name', 'tracker-legend'], axis=1) #  'multi-country', 'original-units', 'conversion-factor', 'area2', 'region2', 'subnat2', 'capacity1', 'capacity2', 'cleaned-cap', 'wiki-from-name', 'tracker-legend']

        # # # printgdf.info())
        check_for_lists(gdf)
        # # if slowmo:
            # # ##(input('Check what is a list')
        gdf.to_file(f'{path_for_download_and_map_files}{mapname}_{iso_today_date}.geojson', driver='GeoJSON', encoding='utf-8')
        gdf.to_file(f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/final/{mapname}_{iso_today_date}.geojson', driver='GeoJSON', encoding='utf-8')
        if mapname == 'africa':
            gdf.to_file(f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/africa-energy/data/{mapname}_{iso_today_date}.geojson', driver='GeoJSON', encoding='utf-8')
        # gdf_to_geojson(gdf, f'{path_for_download_and_map_files}{geojson_file_of_all_africa}')
        # # printf'Saved map geojson file to {path_for_download_and_map_files}{mapname}_{iso_today_date}.geojson')

        gdf.to_excel(f'{path_for_download_and_map_files}{mapname}_{iso_today_date}.xlsx', index=False)
        gdf.to_excel(f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/final/{mapname}_{iso_today_date}.xlsx', index=False)
        if mapname == 'africa':
            gdf.to_excel(f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/africa-energy/compilation_output/{mapname}_{iso_today_date}.xlsx', index=False)
        # # printf'Saved xlsx version just in case to {path_for_download_and_map_files}{mapname}_{iso_today_date}.xlsx')
        final_dict_gdfs[mapname] = gdf
    print(final_dict_gdfs.keys())
    return final_dict_gdfs

###############
# MAKE DOWNLOAD FILE #
###############
def create_data_dwnld_file(dict_list_dfs_by_map):

    result = {}
    for mapname, list_dfs in dict_list_dfs_by_map.items():
        # reorder list_dfs to be in final format order_datadownload
        # pull in about pages to go along side them 
        # starting first with the multi tracker about page
        # Test first
        # print('Starting test prior to loop')
        # total_dfs = len(list_dfs)
        # tracker_counter = Counter()
        # for df in list_dfs:
        #     df = df.reset_index(drop=True)
        #     print(df)
        #     print(df.columns)
        #     # input('inspect, where is tracker-acro')
        #     tracker_counter.update(df['tracker-acro']) # here
        #     result[mapname] = {
        #     'total_dfs': total_dfs,
        #     'tracker_counts': tracker_counter
        # }
        # for map_name, stats in result.items():
        #     print(f"Map: {map_name}")
        #     print(f"Total number of DataFrames: {stats['total_dfs']}")
        #     print(f"Tracker counts: {stats['tracker_counts']}")
        #     print("-" * 40)
        # input('Check test')        
                
        # # printf'Creating data download file for {mapname}')
        path_for_download_and_map_files = gem_path + mapname + '/compilation_output/'
        os.makedirs(path_for_download_and_map_files, exist_ok=True)
        
        xlsfile = f'{path_for_download_and_map_files}{mapname}-data-download {new_release_date}.xlsx'
        xlsfile_testing = f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/final/{mapname}-data-download {new_release_date} {iso_today_date}.xlsx'
        if final_formatting:
            final_folder = f'{path_for_download_and_map_files}final{new_release_date}/'
            os.makedirs(final_folder, exist_ok=True)

            xlsfile = f'{final_folder}{mapname}-data-download {new_release_date}.xlsx'
            xlsfile_testing = f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/fff/{mapname}-data-download {new_release_date} {iso_today_date}.xlsx'

        for file_name in [xlsfile, xlsfile_testing]:
            with pd.ExcelWriter(file_name, engine='openpyxl') as writer:    
                for df in list_dfs:

                    df = df.reset_index(drop=True)
                    # Apply the function to remove illegal characters
                    # TODO check illegal characters or just encoding 
                    df = df.map(remove_illegal_characters)
                    print(df.columns)
                    tracker_curr = df['official_name'].loc[0]
                    
                    # # TODO handle for goget official data download
                    # if tracker_curr == 'Oil & Gas Extraction':
                    #     # use data from other file not this one
                    #     local_file = goget_orig_file
                    #     tabs = goget_orig_tab
                    #     for tab in tabs:
                    #         df = pd.read_excel(local_file, sheet_name=tab)
                    #         # TODO test that this orig file does indeed have not found already
                    #         # gdf['prod-year-gas'] = gdf['prod-year-gas'].apply(lambda x: x.replace(-1, '[not found]'))
                    #         # gdf['prod-year-oil'] = gdf['prod-year-oil'].apply(lambda x: x.replace(-1, '[not found]'))
                
                    #         # for asia filter on asia countries and fuel gas
                    #         if mapname in gas_only_maps:
                    #             df = df[df['Fuel type']!='oil']
                            
                    #         # adjusts to standardization the two terms typically used in a goget official data release                             
                    #         print(df.columns)
                    #         ##(input('Should have not listed and not stated in here')
                    #         df = df.apply(lambda x: x.replace('[not listed]', '[not found]'))
                    #         df = df.apply(lambda x: x.replace('[not stated]', '[not found]'))

                    #         df.to_excel(writer, sheet_name=f'{tracker_curr}-{tab}', index=False)
                    # else:                        
                    # # printf'Adding this tracker to dt dwnld: {tracker_curr}')
                        # # printf'About page data pulled for {(about_df_dict_by_map.keys)} maps.')                
                        # if slowmo:
                            # # ##(input('Check cols')
                    # columns_to_drop = ['tracker-acro', 'float_col_clean_lat', 'float_col_clean_lng', 'official_name']
                    # existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]
                    
                    if 'Production Year - Oil' in df.columns.to_list():
                        df['Production Year - Oil'] = df['Production Year - Oil'].apply(lambda x: str(x).replace('-1', '[not found]'))
                        df['Production Year - Gas'] = df['Production Year - Gas'].apply(lambda x: str(x).replace('-1', '[not found]'))
                
                    # if mapname == 'europe': 
                        # make sure to use the ggit eu data from march egt release 
                        # TODO handle for this
                        
                    # Drop the existing columns
                    if final_formatting:
                        df = drop_internal_tabs(df)
                        df.to_excel(writer, sheet_name=f'{tracker_curr}', index=False)

                    else:
                        df.to_excel(writer, sheet_name=f'internal_{tracker_curr}', index=False)
                        # printf"DataFrame {tracker_curr} written to {file_name}")


    print(dict_list_dfs_by_map.keys())
    



###############
# MAKE ABOUT FILE #
###############

def gather_all_about_pages(prev_key_dict, prep_df, new_release_date, previous_release_date, needed_tracker_geo_by_map):
    # first iterate by map key in dict needed_tracker_geo_by_map
    # make it so that with mapname and dict of about is return
    # official name for sheet: {about page df}
    about_df_dict_by_map = {} # map name: list of tuples with the about page name and about page dfs for each tracker as well as overarching one

    for mapname, list_of_dfs_trackers_geo_prev_info in needed_tracker_geo_by_map.items():
        if mapname == 'Global':
            print('skip this')
        else:
            if local_copy:

                with open(f'local_pkl/about_df_dict_by_map_{iso_today_date}.pkl', 'rb') as f:
                    about_df_dict_by_map = pickle.load(f)
            
            elif pkl_file in os.listdir(path_for_pkl):
                with open(f'local_pkl/about_df_dict_by_map_{iso_today_date}.pkl', 'rb') as f:
                    about_df_dict_by_map = pickle.load(f)      
                    
            else:
                # needed_trackers = value[0] # list of tracker names to include in list of dfs
                # needed_geo = value[1] # list of countries or global for gipt to filter each df in the list by
                list_of_tuples_holding_about_page_name_df = []
                # TODO make a list in config of all previous releases to gather about page for multi tracker
                # most_recent_map_results = list_of_dfs_trackers_geo_prev_info[2] # it is the third item in the list, this may not be true anymore
                # prev_key = most_recent_map_results.iloc[0, most_recent_map_results.columns.get_loc('key')]
                prev_key = prev_key_dict[mapname]

                # # printf'Creating about page file for map: {mapname} with prev key {prev_key}') # Africa Energy, Asia Gas, Europe Gas, LATAM SKIP #  GIPT FOR NOW        
                
                # about_df_dict = {} # official name for sheet: {about page df}
                gspread_creds = gspread.oauth(
                        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
                        credentials_filename=client_secret_full_path,
                        # authorized_user_filename=json_token_name,
                    )
                wait_time = 30
                time.sleep(wait_time)
                gsheets = gspread_creds.open_by_key(prev_key) # this is the last release for this map
                    # List all sheet names
                # print(gsheets)
                sheet_names = [sheet.title for sheet in gsheets.worksheets()]
                # # printf"Sheet names previous release:", sheet_names)

                multi_tracker_about_page = sheet_names[0]
                multi_tracker_about_page = gsheets.worksheet(multi_tracker_about_page) 
                multi_tracker_data = pd.DataFrame(multi_tracker_about_page.get_all_values())

                list_of_tuples_holding_about_page_name_df.append((f'About {mapname}', multi_tracker_data))
                print(list_of_tuples_holding_about_page_name_df)
            
                needed_trackers = list_of_dfs_trackers_geo_prev_info[0] # list of tracker names to include in list of dfs
                print(needed_trackers)
                for tracker in needed_trackers:
                    # # printtracker)
                    if tracker == 'Oil & Gas Extraction':
                        # currently Scott makes a special file for releases for maps 
                        # this is the actual release file
                        tracker_key = '1fdXqNS40NZuIVJreNZKkz1qZd5LB7avQuBQfhOByvgc'
                    # these are separate from geojson data so not in prepdf, in config
                    elif tracker == 'Gas Pipelines':
                        tracker_key = about_page_ggit_goit[tracker]
                    elif tracker == 'LNG Terminals':
                        tracker_key = about_page_ggit_goit[tracker]
                    elif tracker == 'Oil Pipelines':
                        tracker_key = about_page_ggit_goit[tracker]
                    # using the same as gas pipelines because about page was identical from last release dec 2023
                    elif tracker == 'Gas Pipelines EU': 
                        tracker_key = about_page_ggit_goit['Gas Pipelines']
                        
                    else:
                        tracker_key = prep_df[prep_df['official name'] == tracker]['gspread_key'].values[0]

                    gsheets = gspread_creds.open_by_key(tracker_key)
                    sheet_names = [sheet.title for sheet in gsheets.worksheets()]
                    # # printsheet_names)
                    # # # ##(input('Check tracker, key and sheet names')
                    for sheet in sheet_names:
                        # # printsheet)

                        if 'About' in sheet:
                            try:
                                about_sheet = gsheets.worksheet(sheet)
                                about_data = pd.DataFrame(about_sheet.get_all_values())
                                list_of_tuples_holding_about_page_name_df.append((f'About {tracker}', about_data))

                                # about_df_dict_by_map[mapname] = (f'About {new_tracker}', about_data)
                                print(f'Found About page for {tracker}')

                                break
                            
                            except HttpError as e:
                                # Handle rate limit error (HTTP status 429)
                                if e.resp.status == 429:
                                    print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                                    time.sleep(delay)
                                    delay *= 10  # Exponential backoff
                                else:
                                    raise e  # Re-raise other errors

                            except Exception as e:
                                print(f"An error occurred: {e}")
                                break
                            
                        elif 'about' in sheet:
                            about_sheet = gsheets.worksheet(sheet)
                            about_data = pd.DataFrame(about_sheet.get_all_values())
                            # about_df_dict_by_map[mapname] = (f'About {new_tracker}', about_data)
                            list_of_tuples_holding_about_page_name_df.append((f'About {tracker}', about_data))
                            
                            
                            print(f'Found About page for {tracker} in Copyright.')
                            # ##(input('check about page')
                            break                    
                        elif 'Copyright' in sheet:
                            about_sheet = gsheets.worksheet(sheet)
                            about_data = pd.DataFrame(about_sheet.get_all_values())
                            # about_df_dict_by_map[mapname] = (f'About {new_tracker}', about_data)
                            
                            
                            list_of_tuples_holding_about_page_name_df.append((f'About {tracker}', about_data))

                            print(f'Found About page for {tracker} in Copyright.')
                            # ##(input('check about page')
                            break

                        else:
                            print(f'No about page for {tracker} found. Check the gsheet tabs')
                            # ##(input('check about page')
                            
                # print('test that the indents are the same as before for about_df_dict_by_map[mapname] = list_of_tuples_holding_about_page_name_df')
                about_df_dict_by_map[mapname] = list_of_tuples_holding_about_page_name_df
                
                # for tuple in list_of_tuples_holding_about_page_name_df:
                #     if tuple[0] == 'About Hydropower':
                
                #         input('about page for hydro')
                
                #mapname "main about"
                with open(f'local_pkl/about_df_dict_by_map_{iso_today_date}.pkl', 'wb') as f:
                    pickle.dump(about_df_dict_by_map, f)
        

    return about_df_dict_by_map

    
def create_about_page_file(about_df_dict_by_map):
    """
    Creates an Excel file containing multiple sheets with information about different maps.

    Args:
        about_df_dict_by_map (dict): A dictionary where the key is the map name (str) and the value is a tuple containing 
                                     the sheet name (str) and the DataFrame (pd.DataFrame) with the data for that sheet.

    Returns:
        None

    This function iterates over the provided dictionary, creates an Excel file for each map, and writes the corresponding 
    DataFrames to separate sheets within the Excel file. The output file is saved in the 'compilation_output' directory 
    within the map's directory.
    """

    for mapname, about_tab_df_tuple in about_df_dict_by_map.items():

        path_for_download_and_map_files = gem_path + mapname + '/compilation_output/' 
        final_formatting_path_for_download_and_map_files = f'{path_for_download_and_map_files}final{new_release_date}/'
        os.makedirs(final_formatting_path_for_download_and_map_files, exist_ok=True)
        final_about_output = f'{final_formatting_path_for_download_and_map_files}{mapname} about_pages {new_release_date}.xlsx'
        about_output = f'{path_for_download_and_map_files}{mapname} about_pages {new_release_date}.xlsx'  
        print(about_output)  
        for file in [final_about_output, about_output]:  
            # pull out previous overall about page - done in dict
            with pd.ExcelWriter(file, engine='xlsxwriter') as writer:
                for about_tuple in about_tab_df_tuple:
                    about_tab_name = about_tuple[0]
                    about_data = about_tuple[1]
                    
                    print(f'About page for {about_tab_name} has {len(about_data)} rows.')

                    about_data.to_excel(writer, sheet_name=f'{about_tab_name}', index=False)

                # # printf'Saved about page sheets to {about_output} for {len(list_of_tuples_holding_aboutpagetabname_aboutpagedata)} trackers including the multi-tracker one.')
            
    return 

#########################
### SUMMARY FILES ###
#########################

# TODO maybe do this once it is one_gdf so we have consistent column names
def create_summary_files(dict_list_dfs): # map name: list of filtered dfs for map
    # go through each df
    types_of_pivots = {'all': ['Country', 'Owner', 'Start year', 'Province']} # come back to this, can be {tracker name: [list of specific pivot types]}
    cols_to_organize = ['Status', 'Start year']
    cols_to_sum = ['Capacity', 'Kilometers']
    cols_to_count = ['Project Name']
    status_filter = ['operating', 'prospective']
    country_filter = ['China']
    
    dict_of_summary_dfs = {} # {mapname: [list of summary dfs]}
    list_of_summary_dfs = []
    for mapname, list_dfs in dict_list_dfs.items():
        for df in list_dfs:
            # have a list of all files needed
            # do a groupby to create the df for each file
            df = df.reset_index(drop=True)
            # # printf'this is df cols: {df.cols}') # yep it was reset issue, just needs consistnet column names no Country
            tracker = df['tracker-acro'].loc[0]
            # # printf'Creating summary files for {tracker}')
            for pivot_type in types_of_pivots['all']:
                pivot = df.groupby([pivot_type, 'Status'])['Capacity'].sum().reset_index() 
                list_of_summary_dfs.append(pivot)
    dict_of_summary_dfs[mapname] = list_of_summary_dfs
    # TODO save each df to a gsheet and or excel
    df = pd.DataFrame(dict_of_summary_dfs)
    sheet = gspread_creds.open("https://docs.google.com/spreadsheets/d/18zyOMB7S_bAnvFDOPqC1emPA_AT1OMO26CXzTjpwN7o/edit?gid=0#gid=0").sheet1  # Use .worksheet("Sheet Name") to specify a sheet
    set_with_dataframe(sheet, df)
    
    return None

def pull_existing_summary_files(prep_df):
    # in prep_df get the URL for each tracker's summary tables
    # using scrapy or bs go to the site and find each summary table by the div
    # pull the google link 
    # read the google link into df with gspread
    # pull the title
    # compare title to the needed ones for AET
    # if in their pull it and filter for Africa so we can compare to the new one
    # we can compare manually for now
    return None


#### Oil and Gas Plants https://globalenergymonitor.org/projects/global-oil-gas-plant-tracker/summary-tables/
# Oil and Gas Plants by Country/Area (MW)
# Oil and Gas Plants by Country/Area (Power Stations)
# Oil and Gas Plants by Country/Area (Units)
# Oil and Gas Plants by Region (MW)
# Ownership of Oil and Gas Plants in Africa (MW)
# Oil and Gas Plants by Technology by Country/Area (MW)
###### Coal Plants https://globalenergymonitor.org/projects/global-coal-plant-tracker/summary-tables/
# Coal Plants by Country/Area (MW)
# Coal Plants by Country/Area (Power Stations)
# Coal Plants by Country/Area (Units)
# Coal Plants by Region (MW)
###### Geothermal https://globalenergymonitor.org/projects/global-geothermal-power-tracker/summary-tables/
# Geothermal Power Capacity by Country/Area (MW)
# Geothermal Unit Count by Country/Area
# Geothermal Power Capacity by Installation Type and Region (MW)
# Geothermal Operational Capacity Installed by Country/Area and Year (MW)
# Geothermal Prospective Capacity by Country/Area and Year (MW)
###### Bioenergy https://globalenergymonitor.org/projects/global-bioenergy-power-tracker/summary-tables/
# Bioenergy Capacity by Country/Area (MW)
# Bioenergy Unit Count by Country/Area
# Bioenergy Fuel Types by Country/Area
# Bioenergy Capacity by Region (MW)
# Bioenergy Unit Count by Region
# Bioenergy Fuel Types by Region
# Bioenergy Operational Capacity Added by Country/Area and Year (MW)
###### Wind https://globalenergymonitor.org/projects/global-wind-power-tracker/summary-tables/
# Wind Farm Capacity by Country/Area (MW)
# Wind Farm Phase Count by Country/Area
# Wind Farm Capacity by Region (MW)
# Wind Farm Phase Count by Region
# Wind Farm Capacity by Installation Type and Region (MW)
# Wind Farm Operational Capacity by Country/Area and Year (MW)
# Wind Farm Prospective Capacity by Country/Area and Year (MW)
####### Solar https://globalenergymonitor.org/projects/global-solar-power-tracker/summary-tables/
# Solar Farm Capacity by Country/Area (MW)
# Solar Farm Phase Count by Country/Area
# Solar Farm Capacity by Region (MW)
# Solar Farm Phase Count by Region
# Solar Farm Operational Capacity by Country/Area and Year (MW)
# Solar Farm Prospective Capacity by Country/Area and Year (MW)
####### Hydropower https://globalenergymonitor.org/projects/global-hydropower-tracker/summary-tables/
# Hydropower Capacity by Country/Area (MW)
# Hydropower Project Count by Country/Area
# Hydropower Capacity by Region and Subregion (MW)
# Hydropower Project Count by Region and Subregion
# Hydropower Capacity by Region and Type (MW)
###### Nuclear https://globalenergymonitor.org/projects/global-nuclear-power-tracker/summary-tables/
# Nuclear Power Capacity by Country/Area (MW)
# Nuclear power Unit Count by Country/Area
# Nuclear Power Capacity by Region and Subregion (MW)
# Nuclear Power Unit Count by Region and Subregion
# Nuclear Power Capacity by Reactor Type and Region (MW)
###### Oil & Gas Pipelines https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/summary-tables/ ; https://globalenergymonitor.org/projects/global-oil-infrastructure-tracker/summary-tables/
# Gas Pipeline Length by Country/Area (km)
# Gas Pipeline Length by Region (km)
# Oil Pipeline Length by Country/Area (km)
# Oil Pipeline Length by Region (km)
####### LNG Terminals https://globalenergymonitor.org/projects/global-gas-infrastructure-tracker/summary-tables/
# LNG Export Projects by Region
# LNG Export Projects by Country/Area
# LNG Import Projects by Region
# LNG Import Projects by Country/Area
# LNG Export Capacity by Region (mtpa)
# LNG Export Capacity by Country/Area (mtpa)
# LNG Import Capacity by Region (mtpa)
# LNG Import Capacity by Country/Area (mtpa)
# LNG Terminals by Start Year
# LNG Capacity by Start Year (mtpa)
######## Coal Terminals https://globalenergymonitor.org/projects/global-coal-terminals-tracker/summary-tables/
# Number of Coal Terminals by Country/Area
# Coal Terminal Capacity by Country/Area
# Coal Terminal Capacity by Region
# Coal Terminal Capacity by Type (Import/Export)
######### Oil & Gas Extraction https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker/summary-tables/
# Oil & Gas Extraction Sites by Region
# Oil & Gas Extraction Sites by Country/Area
# Oil Production by Sub Region
# Oil Production by Country/Area
# Gas Production by Region
# Gas Production by Country/Area
########## Coal Mines https://globalenergymonitor.org/projects/global-coal-mine-tracker/summary-tables/
# Number of Coal Mines by Country/Area
# groupby count on country/area filtered for Africa
#####################

#######################
### FORMAT & EXECUTION #####
#######################

def reorder_dwld_file_tabs(incorporated_dict_list_dfs_by_map):
    # use this file as order for tabs /Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/africa-energy/compilation_output/2024-08-15/africa_energy_tracker_2024-08-15.xlsx 
    # about page dict jhold all tracker about page data
    # incorporated dict list dfs holds tabular data as well as overarching map about page
    # about_df_dict_by_map {mapname: {tab_name: tab_data_df}, mapname2: {tab_name: tab_data_df}}
    # incorporated_dict_list_dfs_by_map {mapname: [list_d,fs_filt,ered_for_ma,p], mapname2: [list_dfs,filter,ed_for,_map]}
    
    # pull from local files, per map, about and data download 
    print(final_order_datadownload) # print ones that are relevant to map
    # TODO apply format_final() on a df at some point
    if local_copy:
        if priority != ['']:
            for mapname in priority:
                path_for_download_and_map_files_reordered = gem_path + mapname + '/compilation_output/' + f'{new_release_date}_reordered/'
                os.makedirs(path_for_download_and_map_files_reordered, exist_ok=True)
                path_for_download_and_map_files = gem_path + mapname + '/compilation_output/' 
                if final_formatting:
                    path_for_download_and_map_files = f'{path_for_download_and_map_files}final{new_release_date}/'
                for file in os.listdir(path_for_download_and_map_files): # use key for map name
                    # print(path_for_download_and_map_files)
                    if file.endswith(".xlsx") and mapname in file and (new_release_date in file or previous_release_date in file) and ('download' in file): 
                        print(f'{path_for_download_and_map_files}{file}')
                        dd_df_dict = pd.read_excel(f'{path_for_download_and_map_files}{file}', sheet_name=None, engine='openpyxl') # TODO rework so it pulls all tabs
                        input('look at download file')
                        
                    elif file.endswith(".xlsx") and mapname in file and (new_release_date in file or previous_release_date in file) and ('about' in file): 
                        print(f'{path_for_download_and_map_files}{file}')
                        about_df_dict = pd.read_excel(f'{path_for_download_and_map_files}{file}', sheet_name=None , engine='openpyxl')  # TODO rework so it pulls all tabs
                        input('look at about file should be 15 tabs for africa latam')

                print(f'Length of {mapname} dd: {len(dd_df_dict)}')    
                print(f'Length of {mapname} about: {len(about_df_dict)}')

                input('check length of about dict')
                
                output = f'{path_for_download_and_map_files_reordered}{mapname}-energy-tracker-data-download-with-about {new_release_date}.xlsx'        
                testing_output = f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/final/{mapname}-energy-tracker-data-download-with-about {new_release_date}.xlsx'        
                final_order = {}
                for filename in [output, testing_output]:
                    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                        # TODO handle getting the overall tracker about page
                        # for tab, df in about_df_dict.items():
                    
                        first_about_page = next(iter(about_df_dict.items()))
                        first_about_page[1].to_excel(writer, sheet_name=f'About {mapname.title()} Energy Tracker', index=False)         


                        for tracker_official in final_order_datadownload:
                            for about_sheetname, about_df in about_df_dict.items():
                                trackername = about_sheetname.split('About ')[1].strip()
                                if trackername == tracker_official:
                                    tabular_df = dd_df_dict[trackername].reset_index(drop=True)
                                    final_order[trackername] = (about_df, tabular_df) 

                                    final_order[f'About {tracker_official}'] = about_df_dict[f'About {tracker_official}']
                                    final_order[tracker_official] = dd_df_dict[tracker_official]

                                    about_df_dict[f'About {tracker_official}'].to_excel(writer, sheet_name=f'About {tracker_official}', index=False)
                                    dd_df_dict[tracker_official].to_excel(writer, sheet_name=f'{tracker_official}', index=False)         
                            
        else:
            for mapname in ['africa', 'asia', 'europe', 'LATAM']:
                path_for_download_and_map_files_reordered = gem_path + mapname + '/compilation_output/' + f'{new_release_date}_reordered/'
                path_for_download_and_map_files = gem_path + mapname + '/compilation_output/'    
                os.makedirs(path_for_download_and_map_files_reordered, exist_ok=True)

                for file in os.listdir(path_for_download_and_map_files): # use key for map name
                    # print(path_for_download_and_map_files)
                    if file.endswith(".xlsx") and mapname in file and (new_release_date in file or previous_release_date in file) and ('download' in file): 
                        print(f'{path_for_download_and_map_files}{file}')
                        dd_df_dict = pd.read_excel(f'{path_for_download_and_map_files}{file}', sheet_name=None) # TODO rework so it pulls all tabs
                        
                    elif file.endswith(".xlsx") and mapname in file and (new_release_date in file or previous_release_date in file) and ('about' in file): 
                        print(f'{path_for_download_and_map_files}{file}')
                        about_df_dict = pd.read_excel(f'{path_for_download_and_map_files}{file}', sheet_name=None)  # TODO rework so it pulls all tabs
                            
                print(f'Length of {mapname} dd: {len(dd_df_dict)}')    
                print(f'Length of {mapname} about: {len(about_df_dict)}')
                
                print(dd_df_dict.keys()) # TODO handle this 
                print(about_df_dict.keys())  
                ##(input('check above keys should be tabs not column headers now')
                #new info
                output = f'{path_for_download_and_map_files_reordered}/{mapname}-energy-tracker-data-download-with-about {new_release_date}.xlsx'        
                testing_output = f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/final/{mapname}-energy-tracker-data-download-with-about {new_release_date}.xlsx'        
                final_order = {}
                for filename in [output, testing_output]:
                    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                        # TODO handle getting the overall tracker about page
                        # for tab, df in about_df_dict.items():
                    
                        first_about_page = next(iter(about_df_dict.items()))
                        first_about_page[1].to_excel(writer, sheet_name=f'About {mapname.title()} Energy Tracker', index=False)         


                        for tracker_official in final_order_datadownload:
                            for about_sheetname, about_df in about_df_dict.items():
                                trackername = about_sheetname.split('About ')[1].strip()
                                if trackername == tracker_official:
                                    tabular_df = dd_df_dict[trackername].reset_index(drop=True)
                                    final_order[trackername] = (about_df, tabular_df) 

                                    final_order[f'About {tracker_official}'] = about_df_dict[f'About {tracker_official}']
                                    final_order[tracker_official] = dd_df_dict[tracker_official]

                                    about_df_dict[f'About {tracker_official}'].to_excel(writer, sheet_name=f'About {tracker_official}', index=False)
                                    dd_df_dict[tracker_official].to_excel(writer, sheet_name=f'{tracker_official}', index=False)         
                    
        # else:
        #     continue
    else:  # TODO SIMPLIFY THIS WHOLE PIECE We want to go ghrough tabular df and about df and one final order use that to print to final ecel          
    
        about_df_dict_by_map = {}
        
        for mapname, map_df_dict in incorporated_dict_list_dfs_by_map.items(): # all the download data files
            # print(f'This is map_df_dict: {map_df_dict}') # map_df_dict is a list
            # input('check out map_df_dict list of dfs?')
            path_for_download_and_map_files = gem_path + mapname + '/compilation_output/' 
            path_for_download_and_map_files_reordered = gem_path + mapname + '/compilation_output/' + f'{new_release_date}_reordered/'
            os.makedirs(path_for_download_and_map_files_reordered, exist_ok=True)

            output = f'{path_for_download_and_map_files_reordered}{mapname}-energy-tracker-data-download-with-about {new_release_date}.xlsx'        
            # establish about_df_dict_by_map 
            # if about file in the mapname folder use it, even if not local:

            for file in os.listdir(path_for_download_and_map_files): # use key for map name
                # print(path_for_download_and_map_files)

                if file.endswith(".xlsx") and mapname in file and (new_release_date in file) and ('about' in file):  # or previous_release_date in file missing hydro 
                    print(f'{path_for_download_and_map_files}{file}')
                    about_df_dict = pd.read_excel(f'{path_for_download_and_map_files}{file}', sheet_name=None)  # TODO rework so it pulls all tabs
                    about_df_dict_by_map[mapname] = about_df_dict
            
            #     else, if config about_create False
            #     print(need to feed in about pages, will create stub ones for now)
                
                else: 
                    input(f'creating stubb page for {mapname}')
                    # key is sheet name value is data for about page
                    stubb_about_data = stubb_file
                    # cycle thorugh all trackers in map
                    # create stubb page as value for key which is tracker name about tab 
                    stubb_about_df_dict = {}
                    for tracker_df in map_df_dict:
                        # that goes through each df in the list associated with the mapnam
                        tracker_df = tracker_df.reset_index(drop=True)
                        tracker_name = tracker_df['official_name'].loc[0]
                        about_tab_title = f'About {tracker_name}'
                        stubb_about_df_dict[about_tab_title] = stubb_about_data
                    
                    about_df_dict_by_map[mapname] = stubb_about_df_dict

            output = f'{path_for_download_and_map_files}{mapname}-energy-tracker-data-download-with-about {new_release_date}.xlsx'        
            testing_output = f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/final/{mapname}-energy-tracker-data-download-with-about {new_release_date}.xlsx'        
            final_order = {}

            for filename in [output, testing_output]:
                with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                    # TODO handle getting the overall tracker about page
                    # for tab, df in about_df_dict.items():
                

                    # first_about_page = next(iter(about_df_dict_by_map[mapname].items()))
                    # print('first_about_page:')
                    # print(first_about_page)
                    map_about_stubb = {}
                    map_about_stubb_content = f'Placeholder about page for {mapname}'
                    map_about_stubb['placeholder'] = map_about_stubb_content
                    first_about_page = pd.DataFrame(data=map_about_stubb, index=[0], dtype=str)
                    first_about_page.to_excel(writer, sheet_name=f'About {mapname.title()} Energy Tracker', index=False)         

                    # final_order = {'Africa Energy Tracker': (first_about_page[1])} # tab name: (df of about data, df of tracker/tabular data)
                    # go through each item in the dict and list of dfs, pair up the tracker info, then put them in order based on prev key
                    # final_order = {first_about_page[0]: (first_about_page[1])} 

                    for tracker_official in final_order_datadownload:
                        print(f'This is tracker name from final order: {tracker_official}')
                        for about_sheetname, about_df in about_df_dict_by_map[mapname].items():

                            trackername = about_sheetname.split('About ')[1].strip()
                            print(f'This is tracker name from sheet name about: {trackername}')
                            if trackername == tracker_official:
                                # access appropriate df in the dict by trcaker name, key, value is df
                                for tracker_df in map_df_dict:
                                    # that goes through each df in the list associated with the mapnam
                                    tracker_df = tracker_df.reset_index(drop=True)
                                    tracker_name = tracker_df['official_name'].loc[0]
                                    if tracker_name == tracker_official:
                                        tabular_df = tracker_df
                                        final_order[trackername] = (about_df, tabular_df) 
                                        about_df_dict[f'About {tracker_official}'].to_excel(writer, sheet_name=f'About {tracker_official}', index=False)
                                        tabular_df.to_excel(writer, sheet_name=f'{tracker_official}', index=False)         
                
                                        break # break out of loop in the about df, go to next in outer loop of final order datadownlaod
                                        
                                # break
                    print(final_order)
                    (input('check final order'))

    return final_order


### email google sheet of final download file and summary pages #####


#########################
#### RUN TEST OF FILE ###
# def col_differences(df):
    # todo pull over what you have in the other script for release notes to help highlight code changes
    # needed based on column name changes 

def df_info(df, key):
    # find all col name changes 
    # if slowmo:
        # printdf.info())
        # # ##(input('Check df info')

    # numerical_cols = ['Capacity (MW)', 'Start year', 'Retired year', 'Planned retire', 'Latitude', 'Longitude']
    numerical_cols = ''
    col_info = {}
    
    for col in df.columns:                
        if 'ref' in col.lower():
            # # print'ref found pass')
            continue
        else:  
            col_values = set(df[col].to_list()) # len can be a lot, cap at 30
            col_dtype = df[col].dtype # len = 1
            if col in numerical_cols:
                col_range = [df[col].min(), df[col].max()] # len = 2
                col_mid = df[col].mean() # len = 1
                col_sum = df[col].sum()   # len = 1
            else:
                col_range = ''
                col_mid = ''
                col_sum = ''
            # cap for readability 
            if len(col_values) > 5:
                col_sample = list(col_values)[:5]
            else:
                col_sample = list(col_values)
            col_info[col] = {'col_len': len(col_values), 'col_dtype': col_dtype, 'col_sample': col_sample,'col_range': col_range, 'col_mid': col_mid, 'col_sum': col_sum}
        
    col_info_df = pd.DataFrame(col_info)
    col_info_df = col_info_df.T # transpose
    # if slowmo:

        # printcol_info_df)

        # # ##(input(f'Check col info for {key}')
    col_info_df.to_csv(f'issues/{key}_column_info_{iso_today_date}.csv',  encoding="utf-8")
    # # printf'saved col info for {key} here: "test_results/{key}_column_info_{iso_today_date}.csv"')

def final_count(final_dict_gdfs):
    # # printfinal_dict_gdfs.keys())
    # # # ##(input('check that there are enough maps')
    for mapname, gdf in final_dict_gdfs.items():
        grouped_tracker = gdf.groupby('tracker-acro', as_index=False)['id'].count()
        print(mapname)
        print(grouped_tracker)
        # ##(input('Review above')

    # no return

def prior_count(d):
    # # printfinal_dict_gdfs.keys())
    # # # ##(input('check that there are enough maps')
    for value_list in d.values():
        for df in value_list:
            print(f"Tracker: {df['tracker-acro'].iloc[0]}")

            # print(df.head()) #lng
            # print(df.columns) # non lng
            # input('check df')
            # total_len = len(df)
            df.columns = df.columns.str.strip() #.str.lower()

            total_proj = len(df.groupby('name', as_index=False)) # plant name
            # Ensure column names are stripped of any leading/trailing spaces and are in a consistent case
            count_unit_per = df.groupby('name', as_index=False)['id'].count() # have to rename first ... 
            print(f"Tracker: {df['tracker-acro'].iloc[0]}")
            print(f"Count per unit: {count_unit_per}")
            print(total_proj)
            print(count_unit_per)

    # no return


def capacity_conversion_check(dict_holding_sdfs):
    print('Starting the check for major capacity conversion mistakes! Pipelines and GOGET most susceptible.')
    issues = []
    for value_list in dict_holding_sdfs.values():
        for df in value_list:
            tracker = df['tracker-acro'].iloc[0]
            # print(f"Tracker: {tracker}")

            # print(df.head()) #lng
            total_len = len(df)
            # print(total_len)
            df.columns = df.columns.str.strip()
            # print(df.columns) # non lng

            # rename columns why did this not get caught? GNPT only one?
            # df.rename(columns={'capacity (mw)': 'capacity'}, inplace=True)
            # input(f'check df cols for {tracker}')
            # Create a dictionary to store the total capacity per country
            try:
                # Convert all values in the 'capacity' column to numeric, making non-numeric values NaN
                df['capacity'] = pd.to_numeric(df['capacity'], errors='coerce')
                
                # Create a dictionary to store the total capacity per country
                country_cap_tot_dict = df.groupby('areas')['capacity'].sum().to_dict()
                # print(f'This is coutnry cap tot for this tracker: {tracker}: {country_cap_tot_dict}')
                # Save the country_cap_tot_dict to a CSV file
                country_cap_tot_df = pd.DataFrame(list(country_cap_tot_dict.items()), columns=['Country', 'Total Capacity'])
                country_cap_tot_df.to_csv(f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/country_cap_tot {tracker} {iso_today_date}.csv', index=False)
                # input('check out the cap tot for country')
            except TypeError as e:
                print(e)
                print(df['capacity'])
                # For rows in df, if capacity is a string, add to a set and return it.
                invalid_capacity_values = set(df['capacity'].apply(lambda x: x if isinstance(x, str) else None).dropna())
                print(f"Invalid capacity values: {invalid_capacity_values}")
                input('Check this error please')
                issues.append((tracker, f'Error with capacity column turning it into a numeric to get the total country cap value. {invalid_capacity_values}'))
            # Add a new column to the dataframe to show the total capacity per country
            df['country_total'] = df['areas'].map(country_cap_tot_dict)

            for row in df.index:
                try:
                    try:
                        capacity_val = df.loc[row, 'capacity']
                        country = df.loc[row, 'areas']
                        country_total = df.loc[row, 'country_total']

                        if isinstance(capacity_val, str):
                            capacity_val = capacity_val.replace(',', '')
                            capacity_val = capacity_val.replace(' ', '')
                            capacity_val = capacity_val.replace('', '0') 
                            capacity_val = float(capacity_val)                      

                        # Print out issues if any capacity value is greater than the total capacity of the country

                        if capacity_val > country_total:
                            issues.append((row, f'Capacity value {capacity_val} exceeds total capacity {country_total} for country {df.loc[row, "areas"]}'))
                            input('YIKES CHECK THIS')


                    except KeyError:
                        print(f"Capacity column not found for tracker {tracker}")
                        print(f'Not seeing cap or cap MW here')
                        input(f'Check columns: {df.columns}')
                except ValueError as e:
                    issues.append((row, f'Error with capacity column not being a float or int: {e}'))
                    df.drop(row, inplace=True)
                except TypeError as e:
                    issues.append((row, f'Error with capacity column not being a float or int: {e}'))
                    df.drop(row, inplace=True)
     
    # input('Check this while we iterate on creating the test capacity_conversion_check')
    return dict_holding_sdfs

def check_stats_prior(d):
    for value_list in d.values():
        for df in value_list:
            
            print(df.columns)
            print(df['tracker-acro'].iloc[0])
            # print('why is capacity not in GNPT?')
            # input('check cap is in there')
                

            # df = df.rename(columns = {'capacity (mw)': 'capacity'})    
            print(df)
            print(df['capacity'])
            
            capacity_ser = pd.to_numeric(df['capacity'], errors='coerce')
            
            mean = capacity_ser.mean()
            mode = capacity_ser.mode()
            quants = capacity_ser.quantile()
            min = capacity_ser.min()
            max = capacity_ser.max()
            sum = capacity_ser.sum()
            
            stats = [(mean,'mean'), (mode,'mode'), (quants,'quants'), (min,'min'), (max,'max'), (sum,'sum')]
            
            print(df['tracker-acro'].iloc[0])
            
            for stat in stats:
                print(f'{stat[1]}:')
                print(stat[0])

def mis_cols(d):
    # result is a file if not empty sep by tabs for cols and tracker
    missing_cols_check = ['Latitude', 'Longitude', 'status', 'url', 'areas', 'capacity', 'name', 'id'] 
    misformatted = {}
    missing = {}

    filename = f'issues/pre-check-results-{iso_today_date}.xlsx'
    with pd.ExcelWriter(filename, engine='openpyxl') as writer: 
        
        for value_list in d.values():
            for df in value_list:
                tracker = df['tracker-acro'].iloc[0]
                print(df['tracker-acro'].iloc[0])
                df['error messages'] = ''
                print('numeric col check')
                for col in ['Latitude', 'Longitude', 'capacity', 'prod-coal', 'prod_oil', 'prod_gas', 'start_year']: # 'areas', 'geometry', 'route'
                    df[col] = df[col].to_numeric(df[col], errors='coerce')

                    # print(col)
                    if col in df.columns:
                        ser = df[col].replace('', np.nan)
                        try:
                            ser_float = ser.astype(float)
                        except:
                            for row in ser.index:
                                val = ser.iloc[row]
                                try:
                                    val_float = float(val)
                                except:
                                    # print("Error!" + f" val couldn't be converted to float: {val}")
                                    df.iloc[row, 'error messages'] += "Error!" + f" In col {col}, val couldn't be converted to float: '{val}'; "         
                        df['error messages'] = df['error messages'].fillna('')
                        if len(set(df['error messages'].to_list())) > 1:
                            # more than 1 because if all are emtpy strings then it'd have a value of 1
                            
                            df_misformatted = df[df['error messages']!='']
                            
                            misformatted[f'{tracker}-{col}'] = df_misformatted
                            
                            df_misformatted = df_misformatted.map(remove_illegal_characters)

                            # TODO check thisremove_illegal_charactersremove_illegal_characters
                            df_misformatted.to_excel(writer, sheet_name=f'{tracker}-{col}-misformatted', index=False)

                
            print('do we want to write misformatted to a file orjust missing?')                   
            
            for col in missing_cols_check:
                # print('check for missing crucial map data')
                # print(col)
                if col in df.columns:
                    print(f"Data type of column '{col}': {df[col].dtype}")
                    print(f"Number of missing values in column '{col}': {df[col].isna().sum()}")                
                    print(len(df))
                    df_missing_nan = df.loc[df[col].isna()]
                    print(len(df_missing_nan))
                    df_missing_blank = df[df[col]=='']
                    df_missing = pd.concat([df_missing_nan, df_missing_blank], axis=0)
                    df_missing = df_missing.drop_duplicates(subset=['id'])
                    if len(df_missing) > 0:
                        missing[f'{tracker}-{col}'] = df_missing
                        df_missing.to_excel(writer, sheet_name=f'{tracker}-{col}-missing', index=False)

def check_pipeline_capacity_conversions(d):
    # from maisie 100 million barrels of oil per day
    # from baird https://docs.google.com/spreadsheets/d/1foPLE6K-uqFlaYgLPAUxzeXfDO5wOOqE7tibNHeqTek/edit?gid=893060859#gid=893060859
    filename = f'issues/check_pipeline_capacity_conversions-{iso_today_date}.xlsx'
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        for value_list in d.values():
            for df in value_list:
                df['error messages'] = ''

                tracker = df['tracker-acro'].iloc[0]
                print(tracker)
                if tracker in ['GOIT', 'GGIT', 'GGIT-eu']:
                    print('This is a pipelines dataset! Let us check the capacity columns:')
                    if tracker == 'GOIT':
                        for row in df.index:
                            # find value of capacity col and check if more than 100m
                            capacityboed = df.loc[row, 'capacity']
                            if capacityboed > 100_000_000:
                                print(f"Capacity {capacityboed:.1e} exceeds 100 million more than overall oil production")
                                input('ISSUE on capacityboed')
                                df.at[row, 'error messages'] += "Error!" + f" Capacity {capacityboed:.1e} exceeds 100 million more than overall oil production; "         
                            
                    elif tracker in ['GGIT', 'GGIT-eu']:
                    # 549 bcm Billion cubic meters (bcm)
                        for row in df.index:
                            capacitybcmy = df.loc[row, 'capacity']
                            if capacitybcmy > 549:
                                print(f"Capacity {capacitybcmy:.1e} exceeds 549 bcm/y more than overall lng production")
                                input('ISSUE on capacitybcmy')                            
                                df.at[row, 'error messages'] += "Error!" + f" Capacity {capacitybcmy:.1e} exceeds 549 bcm/y more than overall lng production; "         
                    elif tracker == 'GGIT-lng':
                        # 474 mtpa in 2024
                        for row in df.index:
                            capacitymtpa = df.loc[row, 'capacity']
                            if capacitymtpa > 474:
                                print(f"Capacity {capacitymtpa:.1e} exceeds 474 mtpa more than overall lng terminal capacity")
                                input('ISSUE on capacitymtpa')                            
            
                                df.at[row, 'error messages'] += "Error!" + f" Capacity {capacitymtpa:.1e} exceeds 474 mtpa more than overall lng terminal capacity; "                                         
                    
            df_issues = df[df['error messages'] != '']
            df_issues.to_excel(writer, index=False)
         
    
    
    

def validate_data_version(d):
    # this will help us catch situations where we haven't updated the sheet for new data
    filename = f'issues/validate-data-version-{iso_today_date}.xlsx'
    with pd.ExcelWriter(filename, engine='openpyxl') as writer: 
        
        for value_list in d.values():
            for df in value_list:
                tracker = df['tracker-acro'].iloc[0]
                print(f"{df['tracker-acro'].iloc[0]}:")    
                print('use release date in df, and find latest date in data, rename if inconsisten')
                release = df['release-date'].iloc[0]
                print(f'last updated: {release}')
                #(input('check that that makes sense')
                print('Look into apps scripts to capture when a sheet was last modified or updated or the title of it')
                print('Also ask PMs in process asana to include iso date of release')
        
def compare_prev_current(prev_geojson, curr_geojson):
    # once can write to sheets
    # save old df for map to compare stats of new
    gdf1 = gpd.read_file(prev_geojson)
    gdf2 = gpd.read_file(curr_geojson)
    # Find all differences between gdf1 and gdf2
    symmetric_difference_gdf = gpd.GeoDataFrame(pd.concat([gdf1, gdf2]).drop_duplicates(keep=False))
    # # printsymmetric_difference_gdf)
    # # ##(input('Check symmetric difference')



################
def assign_acro_to_orig(df, t_name, acro, release):
    df['tracker-official'] = t_name
    df['tracker-acro'] = acro
    df['release-date'] = release
    
    return df

def pre_tests():
    if local_copy:
        # load pickl

        with open(f'local_pkl/source_data_dict_{iso_today_date}.pkl', 'rb') as f:
            dict_holding_sdfs = pickle.load(f)  
        
        # with open(f'local_pkl/source_data_orig_dict_{iso_today_date}.pkl', 'rb') as f:
            
        #     dict_holding_sdfs_orig = pickle.load(f)
    else:
        # get entire map log file
        key = multi_tracker_log_sheet_key
        
        gspread_creds = gspread.oauth(
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
                credentials_filename=client_secret_full_path,
                # authorized_user_filename=json_token_name,
            )
        wait_time = 30
        time.sleep(wait_time)
        gsheets = gspread_creds.open_by_key(key) # this is the last release for this map

        sheet_names = [sheet.title for sheet in gsheets.worksheets()]
        # print('These are all the sheet names in map log')
        # for i, sheet in enumerate(sheet_names):
        #     print(f'{sheet} | {i}')
        #     tab = gsheets.worksheet(sheet_names[i]) 
        #     data = pd.DataFrame(tab.get_all_values())
        #     print(f'This is len of data: {len(data)}')
        #     print(f'This is cols: {data.columns.to_list()}')
        # input('Check tab options for map log')
        
        # create source data pull 
        # print('Check if this works, may only be able to call tabs by index not name of tab in this way :/')
        source_tab = gsheets.worksheet(sheet_names[2]) 
        source_data = pd.DataFrame(source_tab.get_all_values())
        # print(source_data)
        # input('check source data')
        # cols for source data acro	key	tab	release
        dict_holding_sdfs = {}
        list_sdfs = []
        # dict_holding_sdfs_orig = {}
        # list_sdfs_orig = []
        source_data = source_data.iloc[1:]
        
        for row in source_data.index:
            t_name = source_data.loc[row, 0]
            acro = source_data.loc[row, 1]
            key = source_data.loc[row, 2]
            tab = source_data.loc[row, 3]
            release = source_data.loc[row, 4]
            
            # print(acro)
            # print(t_name)
            
            if acro == "GGIT-lng":
                df = gpd.read_file(ggit_lng_geojson)
                df = assign_acro_to_orig(df, t_name, acro, release)
                # list_sdfs_orig.append(df)                
                df_renamed = set_up_df(df, t_name, acro, release)
                list_sdfs.append(df_renamed)
                
            elif acro == "GGIT":
                df = gpd.read_file(ggit_geojson)
                df = assign_acro_to_orig(df, t_name, acro, release)
                # list_sdfs_orig.append(df)                
                df_renamed = set_up_df(df, t_name, acro, release)
                list_sdfs.append(df_renamed)
            elif acro == "GOIT":
                df = gpd.read_file(goit_geojson)
                df = assign_acro_to_orig(df, t_name, acro, release)
                # list_sdfs_orig.append(df)                
                df_renamed = set_up_df(df, t_name, acro, release)
                list_sdfs.append(df_renamed)
 
            else:

                tabs = str(tab).split(';')
                
                df = gspread_access_file_read_only(key, tabs)
                df = assign_acro_to_orig(df, t_name, acro, release)
                # list_sdfs_orig.append(df)                
                df_renamed = set_up_df(df, t_name, acro, release)
                list_sdfs.append(df_renamed)

            
        # have to append df to lists after i call new function set_up_df()
        
        # list_sdfs.append(df_renamed)
        # list_sdfs_orig.append(df)
    
                    
        dict_holding_sdfs['source-global'] = list_sdfs
        # dict_holding_sdfs_orig['source-global'] = list_sdfs_orig
                
            # add this to pickle  
        with open(f'local_pkl/source_data_dict_{iso_today_date}.pkl', 'wb') as f:
            pickle.dump(dict_holding_sdfs, f) 
        
        # with open(f'local_pkl/source_data_orig_dict_{iso_today_date}.pkl', 'wb') as f:
        #     pickle.dump(dict_holding_sdfs_orig, f) 
            
        print('now we are out of loop and have a dict of dfs')
        input(
            f'This was actually saved to pkl file. {iso_today_date}'
        )
    
    return dict_holding_sdfs # dict_holding_sdfs_orig
    

if run_pre_tests:
    dict_holding_sdfs = pre_tests() 
    # print(dict_holding_sdfs) 
    # print(dict_holding_sdfs_orig)  
    prior_count(dict_holding_sdfs)
    
    # check capacity of one project is never more than the total capacity of entire country
    # also check if more than all of USA
    capacity_conversion_check(dict_holding_sdfs)
    
    # check_stats_prior(dict_holding_sdfs)
    # mis_cols(dict_holding_sdfs)
    # validate_data_version(dict_holding_sdfs)    
    # DONE ish. see if that matches the latest research date in the data
            
            
    # DONE run tests from external notebook that checks source file for missing data
    
    # DONE create global pkl for all trackers unfiltered 
    
    # DONE get sum, max, min and mean of capacity/production (so be sure to rename)
    
    # TODO ideally pull out the tests on geography and other cleaning steps 
        # from following sections so removed and file still runs to set up preview for PM while they fix data
    
    # TODO run tests comparing old and new dataset version of source

    
if augmented: # these vars are all set in all_config, this helped adapt AET code to all multi maps
    print('Start augmented')
    # print('TESTING what_maps_are_needed_new')
    # result of new is {'Africa Energy': ['Coal Plants', 'Coal Mines', 'Coal Terminals', 'Oil & Gas Plants', 'Oil & Gas Extraction', 'Gas Pipelines', 'LNG Terminals', 'Oil Pipelines', 'Solar', 'Wind', 'Nuclear', 'Bioenergy', 'Geothermal', 'Hydropower'], 'Asia Gas': ['Oil & Gas Plants', 'Oil & Gas Extraction', 'Gas Pipelines', 'LNG Terminals'], 'Europe Gas': ['Oil & Gas Plants', 'Oil & Gas Extraction', 'Gas Pipelines EU', 'LNG Terminals'], 'LATAM': ['Coal Plants', 'Coal Mines', 'Coal Terminals', 'Oil & Gas Plants', 'Oil & Gas Extraction', 'Gas Pipelines', 'LNG Terminals', 'Oil Pipelines', 'Solar', 'Wind', 'Nuclear', 'Bioenergy', 'Geothermal', 'Hydropower']}
    # needed_map_and_tracker_dict_new = what_maps_are_needed_new(multi_tracker_log_sheet_key, map_tab) # result is {'Africa Energy': ['Coal Plants', 'Coal Mines', 'Coal Terminals', 'Oil & Gas Plants', 'Oil & Gas Extraction', 'Gas Pipelines', 'LNG Terminals', 'Oil Pipelines', 'Solar', 'Wind', 'Nuclear', 'Bioenergy', 'Geothermal', 'Hydropower'], 'Asia Gas': ['Oil & Gas Plants', 'Oil & Gas Extraction', 'Gas Pipelines', 'LNG Terminals'], 'Europe Gas': ['Oil & Gas Plants', 'Oil & Gas Extraction', 'Gas Pipelines EU', 'LNG Terminals'], 'LATAM': ['Coal Plants', 'Coal Mines', 'Coal Terminals', 'Oil & Gas Plants', 'Oil & Gas Extraction', 'Gas Pipelines', 'LNG Terminals', 'Oil Pipelines', 'Solar', 'Wind', 'Nuclear', 'Bioenergy', 'Geothermal', 'Hydropower']}
    needed_map_and_tracker_dict = what_maps_are_needed(multi_tracker_log_sheet_key, multi_tracker_log_sheet_tab) # map_tab
    # map_country_region has the list of needed maps to be created and their countries/regions
    print(needed_map_and_tracker_dict)
    # ##(input('inspect')
    needed_tracker_geo_by_map = what_countries_or_regions_are_needed_per_map(multi_tracker_countries_sheet, needed_map_and_tracker_dict)
    # print(path_for_download_and_map_files)
    folder_setup(needed_tracker_geo_by_map)
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f'Ended augmented {elapsed_time}')
    
if data_filtering: # this creates gdfs and dfs for all filtered datasets per map, lots of repetition here
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print('Start data filtering')
    prep_df = create_prep_file(multi_tracker_log_sheet_key, source_data_tab)  # so we are using source, so can delete prep file
    conversion_df = create_conversion_df(conversion_key, conversion_tab)
    
    # priority = ['latam', 'africa'] # ['africa', 'asia', 'europe', 'latam']
    to_pass = []
    if priority != ['']:
        for key, value in needed_tracker_geo_by_map.items():
            if key not in priority:
                to_pass.append(key)
            else:
                print(f'Prioritizing {key}')

        
        for key in to_pass:
            del needed_tracker_geo_by_map[key]
        
    
    dict_list_dfs_by_map, dict_list_gdfs_by_map = pull_gsheet_data(prep_df, needed_tracker_geo_by_map) # map_country_region
    incorporated_dict_list_gdfs_by_map, incorporated_dict_list_dfs_by_map = incorporate_geojson_trackers(goit_geojson, ggit_geojson, ggit_lng_geojson, dict_list_dfs_by_map, dict_list_gdfs_by_map) 
    # print(incorporated_dict_list_gdfs_by_map)
    # print(len(incorporated_dict_list_gdfs_by_map))
    # for map in incorporated_dict_list_dfs_by_map.items:
    #     df = 
    # (input(f'Check the above, should not be empty! were in filtering. that is the length of local geojson file dfs.')
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f'Ended data filtering {elapsed_time}')  

    
if map_create:
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f'Start map file creation {elapsed_time}')
    custom_dict_list_gdfs_by_map = split_goget_ggit(incorporated_dict_list_gdfs_by_map)  #incorporated_dict_list_gdfs_by_map
    custom_dict_list_gdfs_by_map_with_conversion = assign_conversion_factors(custom_dict_list_gdfs_by_map, conversion_df)
    renamed_one_gdf_by_map = rename_gdfs(custom_dict_list_gdfs_by_map_with_conversion)
    renamed_one_gdf_by_map_with_search = create_search_column(renamed_one_gdf_by_map)
    input('done with create_search_column')
    # renamed_one_gdf_by_map = add_boed_routes_from_baird(renamed_one_gdf_by_map)
    # cleaned_dict_map_by_one_gdf = remove_null_geo(renamed_one_gdf_by_map) # doesn't do anything
    
    cleaned_dict_map_by_one_gdf_with_conversions = capacity_conversions(renamed_one_gdf_by_map_with_search)
    cleaned_dict_by_map_one_gdf_with_better_statuses = map_ready_statuses(cleaned_dict_map_by_one_gdf_with_conversions)
    
    cleaned_dict_by_map_one_gdf_with_better_countries = map_ready_countries(cleaned_dict_by_map_one_gdf_with_better_statuses)
    one_gdf_by_maptype = workarounds_eg_interim_goget_gcmt(cleaned_dict_by_map_one_gdf_with_better_countries)
    one_gdf_by_maptype_fixed = last_min_fixes(one_gdf_by_maptype) 
    # print(f'This is final gdf keys for: {one_gdf_by_maptype}')
    final_dict_gdfs = create_map_file(one_gdf_by_maptype_fixed)
    
    final_count(final_dict_gdfs)

    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f'End map file creation {elapsed_time}')     

if dwlnd_create: # this creates and saves the tabular data sheets for the data download from the filtered dfs
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f'Start dwlnd creation {elapsed_time}')
    create_data_dwnld_file(incorporated_dict_list_dfs_by_map) 
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print(f'End dwlnd creation {elapsed_time}')
 

if about_create: # this creates and saves a preliminary file with all about pages no adjustments made
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time 
    print('Start about creation')
    about_df_dict_by_map = gather_all_about_pages(prev_key_dict, prep_df, new_release_date, previous_release_date, needed_tracker_geo_by_map)
    create_about_page_file(about_df_dict_by_map)
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  
    print(f'End about creation {elapsed_time}')

   
if refine: # this reorders the data download file
    end_time = time.time()  
    elapsed_time = end_time - start_time  
    print('Start refining')
    if local_copy:
        about_df_dict_by_map = ''
        incorporated_dict_list_dfs_by_map = ''
    print(incorporated_dict_list_dfs_by_map)
    # for map, gdfs in incorporated_dict_list_dfs_by_map.items():
    #     print(map)
    #     print(gdfs)
    #     if map == 'latam':
    #         input('pause for latam')
    # for map, aboutdfs in about_df_dict_by_map.items():
    #     print(map)
    #     print(aboutdfs)
    #     if map == 'latam':
    #         input('pause for latam')


    reorder_dwld_file_tabs(incorporated_dict_list_dfs_by_map) 
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate the elapsed time
    print('End refining')  

def from_orig_pkl_to_tuple_list():
    orig_tup_list_map = []

    # dict_holding_sdfs['source-global'] = list_sdfs # for map
    # dict_holding_sdfs_orig['source-global'] = list_sdfs_orig # for dd, just added tracker acro to that df
            
        # add this to pickle  


    with open(f'local_pkl/source_data_dict_{iso_today_date}.pkl', 'rb') as f:
        dict_holding_sdfs = pickle.load(f) 

    # handle for maps, we only need keys, key is a list of all dfs globally no filter
    list_of_dfs_map = dict_holding_sdfs.get('source-global')   
    print(list_of_dfs_map)
    input('check list of dfs for map in robust tests')  
    for item in list_of_dfs_map:
        tracker_curr_map = item['tracker-acro'].loc[0] # maps need just the acro, dd needs acro space and official name
        orig_tup_list_map.append((item, tracker_curr_map))    
    ###############################################       

#   with open(f'local_pkl/source_data_orig_dict_{iso_today_date}.pkl', 'rb') as f:
#       dict_holding_sdfs_orig = pickle.load(f)

    # handle for dd, we only need keys, key is a list of all dfs globally no filter
    # list_of_dfs_dd = dict_holding_sdfs_orig.get('source-global')  
    # print(list_of_dfs_dd)
    # input('check list of dfs for dd in discrepancies[f'{tracker}{mapname}']')     
    for item in list_of_dfs_map:
        # TODO look into issue
        # I think it has to do with using orig pkl not other pkl
        # input('Check above, got error saying reitred retired plus when should not have been that for tracker')
        tracker_curr_dd = item['tracker-acro'].loc[0] # maps need just the acro, dd needs acro space and official name
        official_name_curr_dd = item['tracker-official'].loc[0] # maps need just the acro, dd needs acro space and official name
        name_curr_dd = f'{tracker_curr_dd} {official_name_curr_dd}'


    # print(orig_tup_list_map)
    # # input('check tup list map in robust tests, we are returning this to be used for comparison')    
    # print(orig_tup_list_dd)
    # input('check tup list dd in robust tests, we are returning this to be used for comparison')  
    
    return orig_tup_list_map

def from_final_file_to_tuple_list():
    final_tup_list_map, final_tup_list_dd = [], []
    testing_final_path = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/final/'
    for file in os.listdir(testing_final_path): 
        if map_to_test == '':
            # print(f'Testing regional maps:')
            if priority != ['']:
                for mapname in priority:
                    if (mapname in file) & file.endswith(".geojson") and iso_today_date in file:
                        final_map = gpd.read_file(testing_final_path + file)
                        final_tup_list_map.append((final_map, mapname))
                        print(final_tup_list_map) 
                    elif (mapname in file) & file.endswith(".xlsx") & (new_release_date in file) & ('about' in file):
                        # Read all sheets into a dictionary
                        final_dd = pd.read_excel(testing_final_path + file, sheet_name=None, engine='openpyxl')
                        final_tup_list_dd.append((final_dd, mapname))
                        print(final_tup_list_dd)   
            else:     
                for mapname in ['africa', 'asia', 'europe', 'latam']:
                    if (mapname in file) & file.endswith(".geojson") and iso_today_date in file:
                        final_map = gpd.read_file(testing_final_path + file)
                        final_tup_list_map.append((final_map, mapname))
                        print(final_tup_list_map) 
                    elif (mapname in file) & file.endswith(".xlsx") & (new_release_date in file) & ('about' in file):
                        # Read all sheets into a dictionary
                        final_dd = pd.read_excel(testing_final_path + file, sheet_name=None, engine='openpyxl')
                        final_tup_list_dd.append((final_dd, mapname))
                        print(final_tup_list_dd)   
        
        else:
            print(f'Testing single map: {map_to_test}')
            if (map_to_test in file) & file.endswith(".geojson") and iso_today_date in file:
                final_map = gpd.read_file(testing_final_path + file)
                final_tup_list_map.append((final_map, map_to_test))
                print(final_tup_list_map)
            elif (map_to_test in file) & file.endswith(".xlsx") & (new_release_date in file) & ('about' in file):
                # final_data = pd.ExcelFile(testing_final_path + file)
                # Read all sheets into a dictionary
                final_dd = pd.read_excel(testing_final_path + file, sheet_name=None, engine='openpyxl')
                final_tup_list_dd.append((final_dd, map_to_test))
                print(final_tup_list_dd)        
    
    
    return final_tup_list_map, final_tup_list_dd

def robust_tests_dd():
    # TODO still need to apply better smart filtering for these dd source dfs
    # tracker = ''
    # map_to_test = '' not needed instead we'll go through all created unless a single map to be tested, set this in config
    # final_map = '' # is actually equal to map_df when single map test, when multi need map_df = final_map[final_map['tracker-acro']==tracker]

    # final_data_dict = '' this is actually equal to dd df when single map test, when multi need dd_df = final_data_dict[tracker_official].rename(columns=renaming_sel) 

    final_tup_list_map, final_tup_list_dd = from_final_file_to_tuple_list() # final map and dd files from this iteration of the script     
    orig_tup_list_map = from_orig_pkl_to_tuple_list() # source files from this iteration of the script, cols adjusted for map, and not
    # orig_tup_list should be equivalent to list_of_trackers below. with df to left, and tracker acro to right. 
    discrepancies_file_name = f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/issues/output_discrepancies_dd_{new_release_date} {iso_today_date}.xlsx'

    discrepancies = {}            
    for final_tuple_dd_to_test in final_tup_list_dd: # [(dict of sheet dfs, europe), (dict of sheet dfs, africa), (dict of sheet dfs, asia), (dict of sheet dfs, latam)]. 
        
        trackers_gas_only = ['GOGET', 'GGIT-lng', 'GGIT', 'GOGPT']
        trackers_all = ['GCTT', 'GCMT', 'GCPT', 'GOGPT', 'GHPT', 'GWPT', 'GBPT',
                        'GSPT', 'GGPT', 'GNPT', 'GOGET', 'GGIT-lng', 'GGIT', 'GOIT']
    
    
        if map_to_test == '':
            mapname = final_tuple_dd_to_test[1]
            final_dd = final_tuple_dd_to_test[0]
            print(f'This is final_dd: ')
            
            print(final_dd)
            input('inspect this, it is a dict of sheet dfs, how to filter to macth source df')
            if mapname == 'asia':
                needed_geo = asia_countries
            elif mapname == 'africa':
                needed_geo = africa_countries
            elif mapname == 'europe':
                needed_geo = europe_countries
            elif mapname == 'latam':
                needed_geo = latam_countries
            else:
                print('we misunderstood mapname')
                print(f'This is mapname {mapname}')            
        # if it is a single map test then no filter on country
        else: 
            # mapname = final_tuple_map_to_test[1]
            mapname = map_to_test
            final_dd = final_tuple_dd_to_test[0]
            needed_geo = ''

# set up country now set up filter on tracker
        if mapname not in gas_only_maps:                
            for source_tracker_tup in orig_tup_list_map:

                print("-" * 40)
                print(f'MAP: {mapname}')
                print(source_tracker_tup[1])
                input('Check what is in source_tracker_tup[1]')
                tracker_acro = source_tracker_tup[1].split(' ')[0]
                # tracker_official = source_tracker_tup[1].split(' ')[1:]
                # print(tracker_official)
                # tracker_official = ''.join(tracker_official)
                # print(tracker_official)
                print(f'ACRO: {tracker_acro}') # example GOGPT
                # print(f'LONG NAME: {tracker_official}')
                input('check this for dd so that it gets renamed correctly so can be altered')
                df = source_tracker_tup[0]
                print(f'This is df from source_tracker_tup: {df}')

                renaming_sel = renaming_cols_dict[tracker_acro]
               
                # rneame source tracker
                df = df.rename(columns=renaming_sel) 
                # print(final_dd) = {}
                final_dd_minus_about = {}
                final_dd_sel_df = pd.DataFrame()
                for key, value in final_dd.items():
                    if 'tracker-acro' in value.columns:
                        final_dd_minus_about[key] = value
                        if value['tracker-acro'].iloc[0] == tracker_acro:
                            final_dd_sel_df = value
                        
                    else:
                        print(value.columns)
                        input(f'no tracker-acro in this final_dd tab for {mapname} {key}')
                
                print(final_dd_minus_about)
                print(final_dd_sel_df)
                dd_df = final_dd_sel_df 

                # rename final dd 

                dd_df = dd_df.rename(columns=renaming_sel)                             

                # filtering source on geo and fuel
                if needed_geo == '':
                    continue
                else:
                    if tracker_acro in tracker_mult_countries:
                        for sep in ',;-':
                            # I want to break up any multiple countries into a list of countries
                            # then check if any of those are in the needed_geo list
                            df['country_to_check'] = df['areas'].str.strip().str.split(sep) 

                        # filter the df on the country column to see if any of the countries in that list is in the needed geo
                        df = df[df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]

                        df = df.drop(columns=['country_to_check'])
                        
                    else:
      
                        df['country_to_check'] = df['areas'].str.strip()

                        # need this by country because not a GEM region, problematic since goget uses region and numbers when filtered by country in the gem region do not match 636 versus 578 for africa
                        df = df[df['country_to_check'].isin(needed_geo)]
                    
                        df = df.drop(columns=['country_to_check'])
                    
                    print(f'len after geo filter {tracker_acro} {len(df)}')  

                    print(f'Source Data {tracker_acro}: {len(df)}')
                    print(f'DD Data {tracker_acro}: {len(dd_df)}')
                                            
                        
                    df = df[df['areas'].isin(needed_geo)]
                    for column in dd_df.columns:
                        print(column)
                    input('is id in there?')
                    if tracker_acro == 'GGIT-eu':
                        pass
                    else:
                        df_missing_dd = df[~df['id'].isin(dd_df['id'])]
                        df_missing_dd_reverse = dd_df[~dd_df['id'].isin(df['id'])]

                        print(f'Source Data {tracker_acro}: {len(df)}')
                        print(f'Data Download Data {tracker_acro}: {len(dd_df)}')
                        print('DD Discrepancy Count')
                        print(len(df_missing_dd))
                        if len(df_missing_dd) > 0:
                            print(f'df missing {df_missing_dd}')
                            discrepancies[f'{tracker_acro}{mapname}'] = df_missing_dd
                            print(df_missing_dd[['id', 'areas','geometry']])
                            # input('check this')
                        print(f'DD Discrepancy Count for {mapname}')
                        print(len(df_missing_dd))

                        if len(df_missing_dd_reverse) > 0:
                            print(f'df reverse missing {df_missing_dd_reverse}')
                            discrepancies[f'{tracker_acro}-dd-reverse missing {mapname}'] = df_missing_dd_reverse
                            print(df_missing_dd_reverse[['id', 'areas','geometry']])
                            # input('check this')
                        print('DD Reverse Discrepancy Count')
                        print(len(df_missing_dd_reverse))
                        input('Check results not gas only')
                

        elif mapname in gas_only_maps:

            for source_tracker_tup in orig_tup_list_map: # in gas

                print("-" * 40)
                print(f'MAP: {mapname}')

                tracker_acro = source_tracker_tup[1].split(' ')[0]
                # tracker_official = (' ').join(source_tracker_tup[1].split(' ')[1:]) 
                print(tracker_acro)
                # print(tracker_official)

                df = source_tracker_tup[0]

                renaming_sel = renaming_cols_dict[tracker_acro]
                df = df.rename(columns=renaming_sel) 
                
                # print(final_dd)
                final_dd_minus_about = {}
                final_dd_sel_df = pd.DataFrame()

                for key, value in final_dd.items():
                    if 'tracker-acro' in value.columns:
                        final_dd_minus_about[key] = value
                        if value['tracker-acro'].iloc[0] == tracker_acro:
                            final_dd_sel_df = value
                    else:
                        print(value.columns)
                        input(f'no tracker-acro in this final_dd tab for {mapname} {key}')
                
                print(final_dd_minus_about)
                print(final_dd_sel_df)
                dd_df = final_dd_sel_df 

                dd_df = dd_df.rename(columns=renaming_sel) 
                
                # df = df[df['areas'].isin(needed_geo)]
                if needed_geo == '':
                    pass    
                else:
                    if tracker_acro in tracker_mult_countries: # currently no lists like with regions since goit and ggit created countries a list from start and end countries
                        # if any of the countries in the country column list is in the needed geo list then keep it if none then filter out
                        for sep in ',;-':
                            # I want to break up any multiple countries into a list of countries
                            # then check if any of those are in the needed_geo list
                            df['country_to_check'] = df['areas'].str.strip().str.split(sep) 

                        # filter the df on the country column to see if any of the countries in that list is in the needed geo
                        df = df[df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]

                        df = df.drop(columns=['country_to_check'])

                    else:

                        df['country_to_check'] = df['areas'].str.strip()

                        # need this by country because not a GEM region, problematic since goget uses region and numbers when filtered by country in the gem region do not match 636 versus 578 for africa
                        df = df[df['country_to_check'].isin(needed_geo)]
                    
                        df = df.drop(columns=['country_to_check'])
                    # print(f'len after geo filter {tracker_acro} {len(df)}')  
        
                if tracker_acro == 'GOGPT':
                    # filter out oil only fuel # Alcúdia power station
                    drop_row = []
                    for row in df.index:
                        fuel_cat_list = df.loc[row, 'fuel'].split(',')
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
                    df.drop(drop_row, inplace=True)  
                    print(f'len after gas only filter {tracker_acro} {len(df)}')  
                elif tracker_acro == 'GOGET':
                    goget_orig_file = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/source/Global Oil and Gas Extraction Tracker - 2024-03-08_1205 DATA TEAM COPY.xlsx'

                    # filter out oil
                    list_ids = handle_goget_gas_only_workaround(goget_orig_file)
                    # print(len(ndf)) # 3095 will be less because not all trackers
                    # filter = (df['tracker-acro']=='GOGET') & (df['prod-gas']=='') #2788
                    # filter = df['id'] in list_ids #2788
                    # df = df[(df['tracker-acro']=='GOGET') & (df['id'] in list_ids)]
                    drop_row = []
                    for row in df.index:
                        # if df.loc[row, 'tracker-acro'] == 'GOGET':
                        if df.loc[row, 'id'] not in list_ids:
                            drop_row.append(row)
                    # drop all rows from df that are goget and not in the gas list ids 
                    df.drop(drop_row, inplace=True)     
                    print(f'len after gas only filter {tracker_acro} {len(df)}')  
                
                print(f'Source Data {tracker_acro}: {len(df)}')
                print(f'Data Download Data {tracker_acro}: {len(dd_df)}')
                input('is id in there?')
                if tracker_acro == 'GGIT-eu':
                    pass
                else:            
                    df_missing_dd = df[~df['id'].isin(dd_df['id'])] # TODO FEB 7th error no id ... 
                    df_missing_dd_reverse = dd_df[~dd_df['id'].isin(df['id'])]

                    print(f'DD Discrepancy Count for {mapname}')

                    print(len(df_missing_dd))
                    print('Reverse map discrepancy Count')
                    print(len(df_missing_dd_reverse)) 
                                
                    if len(df_missing_dd) > 0:
                        print(f'df missing {df_missing_dd}')

                        discrepancies[f'{tracker_acro}{mapname}'] = df_missing_dd
                        print(df_missing_dd)
                        
                    if len(df_missing_dd_reverse) > 0:
                        print(f'df reverse missing dd {df_missing_dd_reverse}')
                        discrepancies[f'{tracker_acro}-reverse missing {mapname}'] = df_missing_dd_reverse
                        print(df_missing_dd_reverse[['id', 'areas','geometry']])

            else:
                continue # do we need this?
            
    with pd.ExcelWriter(discrepancies_file_name, engine='openpyxl') as writer:    

        # print(type(discrepancies)) 
        # print(discrepancies) 
        for item in discrepancies.items():
            df = item[1]
            tracker_acro = item[0]
            tab_name = tracker_acro.replace('-', '')
            df.to_excel(writer, sheet_name = f'{tab_name} ({len(df)})', index=False)  
            # df.to_excel(writer, sheet_name = f'{tracker_acro}', index=False)  

            
            
def robust_tests_map():
    print('we are in robust')
    # input('pause')
    
    # tracker = ''
    # map_to_test = '' not needed instead we'll go through all created unless a single map to be tested, set this in config
    # final_map = '' # is actually equal to map_df when single map test, when multi need map_df = final_map[final_map['tracker-acro']==tracker]

    # final_data_dict = '' this is actually equal to dd df when single map test, when multi need dd_df = final_data_dict[tracker_official].rename(columns=renaming_sel) 


    final_tup_list_map, final_tup_list_dd = from_final_file_to_tuple_list() # final map and dd files from this iteration of the script     
    orig_tup_list_map = from_orig_pkl_to_tuple_list() # source files from this iteration of the script, cols adjusted for map, and not
    # orig_tup_list should be equivalent to list_of_trackers below. with df to left, and tracker acro to right. 
    discrepancies_file_name = f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/issues/output_discrepancies {new_release_date} {iso_today_date}.xlsx'

    discrepancies = {}

    for final_tuple_map_to_test in final_tup_list_map: # [(df, europe), (df, africa), (df, asia), (df, latam)]
        
        trackers_gas_only = ['GOGET', 'GGIT-lng', 'GGIT', 'GOGPT']
        trackers_all = ['GCTT', 'GCMT', 'GCPT', 'GOGPT', 'GHPT', 'GWPT', 'GBPT',
                        'GSPT', 'GGPT', 'GNPT', 'GOGET', 'GGIT-lng', 'GGIT', 'GOIT']
        # orig_tup_list_map = [(coal_terminals, 'GCTT'), (coal_mines, 'GCMT'), (gcpt,'GCPT'), (gogpt, 'GOGPT'), (hydro, 'GHPT'), (wind,'GWPT'), (bio,'GBPT'),
        #                     (solar, 'GSPT'), (geo, 'GGPT'), (nuclear, 'GNPT'), (goget_formatted, 'GOGET'), (ggit_lng, 'GGIT-lng'), (ggit, 'GGIT'), (goit, 'GOIT')]

        # # this one tests against actual data release for goget not the formatted map file
        # orig_tup_list_dd = [(coal_terminals, 'GCTT Coal Terminals'), (coal_mines, 'GCMT Coal Mines'), (gcpt,'GCPT Coal Plants'), (gogpt, 'GOGPT Oil & GasPlants'), (hydro, 'GHPT Hydropower'), (wind,'GWPT Wind'), (bio,'GBPT Bioenergy'),
        #                     (solar, 'GSPT Solar'), (geo, 'GGPT Geothermal'), (nuclear, 'GNPT Nuclear'), (goget, 'GOGET Oil & Gas Extraction'), (ggit_lng, 'GGIT-lng LNG Terminals'), 
        #                     (ggit, 'GGIT Gas Pipelines'), (goit, 'GOIT Oil Pipelines')]

        # file_name = f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/output_africa_discrepancies_{new_release_date}.xlsx'

        if map_to_test == '':
            mapname = final_tuple_map_to_test[1]

            final_map = final_tuple_map_to_test[0]
            print(final_map)
            input('check this final map variable')
            # needed_geo = f'{mapname}_countries' # doesn't work it s a string not the variable in all_config
            if mapname == 'asia':
                needed_geo = asia_countries
            elif mapname == 'africa':
                needed_geo = africa_countries
            elif mapname == 'europe':
                needed_geo = europe_countries
            elif mapname == 'latam':
                needed_geo = latam_countries
            else:
                print('we misunderstood mapname')
                print(f'This is mapname {mapname}')
        # if it is a single map test then no filter on country
        else: 
            # mapname = final_tuple_map_to_test[1]
            mapname = map_to_test
            map_df = final_tuple_map_to_test[0]
            needed_geo = ''

        if mapname not in gas_only_maps:

            for source_tracker_tup in orig_tup_list_map:

                print("-" * 40)
                print(f'MAP: {mapname}')
                print(source_tracker_tup[1])
                tracker = source_tracker_tup[1]
                df = source_tracker_tup[0]

                renaming_sel = renaming_cols_dict[tracker]
                df = df.rename(columns=renaming_sel) 
                # print(final_map.columns)
                map_df = final_map[final_map['tracker-acro']==tracker]
                if needed_geo == '':
                    continue
                else:
                    if tracker in tracker_mult_countries: # currently no lists like with regions since goit and ggit created countries a list from start and end countries
                        # if any of the countries in the country column list is in the needed geo list then keep it if none then filter out
                        for sep in ',;-':
                            # I want to break up any multiple countries into a list of countries
                            # then check if any of those are in the needed_geo list
                            df['country_to_check'] = df['areas'].str.strip().str.split(sep) 

                        # filter the df on the country column to see if any of the countries in that list is in the needed geo
                        df = df[df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]

                        df = df.drop(columns=['country_to_check'])

                    else:
      
                        df['country_to_check'] = df['areas'].str.strip()

                        # need this by country because not a GEM region, problematic since goget uses region and numbers when filtered by country in the gem region do not match 636 versus 578 for africa
                        df = df[df['country_to_check'].isin(needed_geo)]
                    
                        df = df.drop(columns=['country_to_check'])
                    
                    # print(mapname)
                    print(f'len after geo filter {tracker} {len(df)}')  

                    print(f'Source Data {tracker}: {len(df)}')
                    print(f'Map Data {tracker}: {len(map_df)}')

                    df_missing = df[~df['id'].isin(map_df['id'])]
                    df_missing_reverse = map_df[~map_df['id'].isin(df['id'])]
                    
                    if len(df_missing) > 0:
                        print(f'df missing {df_missing}')
                        discrepancies[f'{tracker}{mapname}'] = df_missing
                        print(df_missing[['id', 'areas','geometry']])
                        # input('check this')
                    print(f'Map Discrepancy Count for {mapname}')
                    print(len(df_missing))

                    if len(df_missing_reverse) > 0:
                        print(f'df reverse missing {df_missing_reverse}')
                        discrepancies[f'{tracker}-reverse missing {mapname}'] = df_missing_reverse
                        print(df_missing_reverse[['id', 'areas','geometry']])
                        # input('check this')
                    print('Map Reverse Discrepancy Count')
                    print(len(df_missing_reverse))
                    input('Check results not gas only')
                
        elif mapname in gas_only_maps:
            # check asia, europe
            # in it check ggit, ggitlng, goget, gogpt

            col_country_name = '' # used for hydro we're renaming so not as important we should find the country cols maybe to make this consistent for hydro
            
            for source_tracker_tup in orig_tup_list_map:
                print(source_tracker_tup[1])
                if source_tracker_tup[1] in gas_only_maps:

                    print("-" * 40)
                    print(f'MAP: {mapname}')
                    print(source_tracker_tup[1])
                    tracker = source_tracker_tup[1]
                    df = source_tracker_tup[0]

                    renaming_sel = renaming_cols_dict[tracker]
                    df = df.rename(columns=renaming_sel) 

                    print(final_map)
                    for key, value in final_map.items():
                        if 'tracker-acro' in value.columns:
                            pass
                        else:
                            print(value.columns)
                            # input(f'no tracker-acro in this final_dd tab for {mapname} {key}')
                    
                    map_df = final_map[final_map['tracker-acro']==tracker]
                    if needed_geo == '':
                        pass
                    else:
                        if tracker in tracker_mult_countries: # currently no lists like with regions since goit and ggit created countries a list from start and end countries
                            # if any of the countries in the country column list is in the needed geo list then keep it if none then filter out
                            for sep in ',;-':
                                # I want to break up any multiple countries into a list of countries
                                # then check if any of those are in the needed_geo list
                                df['country_to_check'] = df['areas'].str.strip().str.split(sep) 

                            # filter the df on the country column to see if any of the countries in that list is in the needed geo
                            df = df[df['country_to_check'].apply(lambda x: check_list(x, needed_geo))]

                            df = df.drop(columns=['country_to_check'])

                        else:

                            df['country_to_check'] = df['areas'].str.strip()

                            # need this by country because not a GEM region, problematic since goget uses region and numbers when filtered by country in the gem region do not match 636 versus 578 for africa
                            df = df[df['country_to_check'].isin(needed_geo)]
                        
                            df = df.drop(columns=['country_to_check'])
                        print(f'len after geo filter {tracker} {len(df)}')  

                        # # df = df[df['areas'].isin(needed_geo)] # TODO fix for this because it excludes when there is multiple countries and shouldn't OG0013150 for africa
                        # print(f'Source Data {tracker}: {len(df)}')
                        # print(f'Map Data {tracker}: {len(map_df)}')
                        # df_missing = df[~df['id'].isin(map_df['id'])]
                        # df_missing_reverse = map_df[~map_df['id'].isin(df['id'])]
                        
                        # print(f'Map Discrepancy Count for {mapname}')
                        # print(len(df_missing))
                        # print('Reverse map discrepancy Count')
                        # print(len(df_missing_reverse))
                        # # print(df_missing_reverse)
                        
                        # if len(df_missing) > 0:
                        #     print(f'df missing {df_missing}')
                        #     discrepancies[f'{tracker}{mapname}'] = df_missing
                        #     print(df_missing[['id', 'areas','geometry']])
                        #     if tracker == 'GGIT-eu':
                        #         print(df_missing)
                        #         input('check GGIT EU')
                                
                        # print(f'Map Discrepancy Count for {mapname}')
                        # print(len(df_missing))

                        # if len(df_missing_reverse) > 0:
                        #     print(f'df reverse missing {df_missing_reverse}')
                        #     discrepancies[f'{tracker}-reverse missing'] = df_missing_reverse
                        #     print(df_missing_reverse[['id', 'areas','geometry']])
                        #     if tracker == 'GGIT-eu':
                        #         print(df_missing_reverse)
                        #         input('check GGIT EU')
                        # print('Map Reverse Discrepancy Count')
                        # print(len(df_missing_reverse))
                    
                    if tracker == 'GOGPT':
                        # filter out oil only fuel # Alcúdia power station
                        drop_row = []
                        for row in df.index:
                            fuel_cat_list = df.loc[row, 'fuel'].split(',')
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
                        df.drop(drop_row, inplace=True)  
                        print(f'len after gas only filter {tracker} {len(df)}')  

                        # df = df[df['areas'].isin(needed_geo)] # TODO fix for this because it excludes when there is multiple countries and shouldn't OG0013150 for africa
                        # print(f'Source Data {tracker}: {len(df)}')
                        # print(f'Map Data {tracker}: {len(map_df)}')
                        # df_missing = df[~df['id'].isin(map_df['id'])]
                        # df_missing_reverse = map_df[~map_df['id'].isin(df['id'])]
                        
                        # print(f'Map Discrepancy Count for {mapname}')
                        # print(len(df_missing))
                        # print('Reverse map discrepancy Count')
                        # print(len(df_missing_reverse))
                        # # print(df_missing_reverse)
                        
                        # if len(df_missing) > 0:
                        #     print(f'df missing {df_missing}')
                        #     discrepancies[f'{tracker}{mapname}'] = df_missing
                        #     print(df_missing[['id', 'areas','geometry']])
                        #     if tracker == 'GGIT-eu':
                        #         print(df_missing)
                        #         input('check GGIT EU')
                                
                        # print(f'Map Discrepancy Count for {mapname}')
                        # print(len(df_missing))

                        # if len(df_missing_reverse) > 0:
                        #     print(f'df reverse missing {df_missing_reverse}')
                        #     discrepancies[f'{tracker}-reverse missing'] = df_missing_reverse
                        #     print(df_missing_reverse[['id', 'areas','geometry']])
                        #     if tracker == 'GGIT-eu':
                        #         print(df_missing_reverse)
                        #         input('check GGIT EU')
                        # print('Map Reverse Discrepancy Count')
                        # print(len(df_missing_reverse))
                    elif tracker == 'GOGET':
                        goget_orig_file = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/source/Global Oil and Gas Extraction Tracker - 2024-03-08_1205 DATA TEAM COPY.xlsx'

                        # filter out oil
                        list_ids = handle_goget_gas_only_workaround(goget_orig_file)
                        # print(len(ndf)) # 3095 will be less because not all trackers
                        # filter = (df['tracker-acro']=='GOGET') & (df['prod-gas']=='') #2788
                        # filter = df['id'] in list_ids #2788
                        # df = df[(df['tracker-acro']=='GOGET') & (df['id'] in list_ids)]
                        drop_row = []
                        for row in df.index:
                            # if df.loc[row, 'tracker-acro'] == 'GOGET':
                            if df.loc[row, 'id'] not in list_ids:
                                drop_row.append(row)
                        # drop all rows from df that are goget and not in the gas list ids 
                        df.drop(drop_row, inplace=True)     
                        print(f'len after gas only filter {tracker} {len(df)}')  
                        

                        # df = df[df['areas'].isin(needed_geo)] # TODO fix for this because it excludes when there is multiple countries and shouldn't OG0013150 for africa
                        # print(f'Source Data {tracker}: {len(df)}')
                        # print(f'Map Data {tracker}: {len(map_df)}')
                        # df_missing = df[~df['id'].isin(map_df['id'])]
                        # df_missing_reverse = map_df[~map_df['id'].isin(df['id'])]
                        
                        # print(f'Map Discrepancy Count for {mapname}')
                        # print(len(df_missing))
                        # print('Reverse map discrepancy Count')
                        # print(len(df_missing_reverse))
                        # # print(df_missing_reverse)
                        
                        # if len(df_missing) > 0:
                        #     print(f'df missing {df_missing}')
                        #     discrepancies[f'{tracker}{mapname}'] = df_missing
                        #     print(df_missing[['id', 'areas','geometry']])
                        #     if tracker == 'GGIT-eu':
                        #         print(df_missing)
                        #         input('check GGIT EU')
                                
                        #     print(f'Map Discrepancy Count for {mapname}')
                        #     print(len(df_missing))

                        # if len(df_missing_reverse) > 0:
                        #     print(f'df reverse missing {df_missing_reverse}')
                        #     discrepancies[f'{tracker}-reverse missing'] = df_missing_reverse
                        #     print(df_missing_reverse[['id', 'areas','geometry']])
                        #     if tracker == 'GGIT-eu':
                        #         print(df_missing_reverse)
                        #         input('check GGIT EU')
                        #     print('Map Reverse Discrepancy Count')
                        #     print(len(df_missing_reverse))
                    print(f'Source Data {tracker}: {len(df)}')
                    print(f'Map Data {tracker}: {len(map_df)}')
                    df_missing = df[~df['id'].isin(map_df['id'])]
                    df_missing_reverse = map_df[~map_df['id'].isin(df['id'])]
                    
                    print(f'Map Discrepancy Count for {mapname}')
                    print(len(df_missing))
                    print('Reverse map discrepancy Count')
                    print(len(df_missing_reverse))
                    # print(df_missing_reverse)
                    
                    if len(df_missing) > 0:
                        print(f'df missing {df_missing}')
                        discrepancies[f'{tracker}{mapname}'] = df_missing
                        print(df_missing[['id', 'areas','geometry']])
                        if tracker == 'GGIT-eu':
                            print(df_missing)
                            input('check GGIT EU')
                            
                    print(f'Map Discrepancy Count for {mapname}')
                    print(len(df_missing))

                    if len(df_missing_reverse) > 0:
                        print(f'df reverse missing {df_missing_reverse}')
                        discrepancies[f'{tracker}-reverse missing {mapname}'] = df_missing_reverse
                        print(df_missing_reverse[['id', 'areas','geometry']])
                        if tracker == 'GGIT-eu':
                            print(df_missing_reverse)
                            input('check GGIT EU')
                    print('Map Reverse Discrepancy Count')
                    print(len(df_missing_reverse))
                    input('Check results gas only')
                else:
                    continue
    with pd.ExcelWriter(discrepancies_file_name, engine='openpyxl') as writer:    

        # print(type(discrepancies)) 
        # print(discrepancies) 
        input('about to save to excel...')
        for item in discrepancies.items():
            df = item[1]
            tracker = item[0]
            df.to_excel(writer, sheet_name = f'{tracker} ({len(df)})', index=False)
            # Ensure the sheet is visible
            # workbook = writer.book
            # worksheet = workbook[sheet_name]
            # worksheet.sheet_state = 'visible'        



def post_tests(final_dict_gdfs):
    discrepancies = {}
    print('Testing Map Files')
    # compare final map files to source files
    # load un renamed dict source dfs from pickl
    # this should always exist since it happens with local_copy or not

    with open(f'/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/local_pkl/source_data_dict_{iso_today_date}.pkl', 'rb') as f:
        dict_holding_sdfs = pickle.load(f) 
    source_data = dict_holding_sdfs # from pre_test functions
    print(source_data)
    # input('Check source data')
    #(input('Check that the above is a list of all gdfs')
    # use global source data from pre-test section
    for mapname, gdf in final_dict_gdfs.items():
        # say mapname = asia gas tracker
        # then that is the final, we want to compare to source
        # mapname = source-global dict_holding_sdfs_orig
        list_of_map_trackers = list(set(gdf['tracker-acro'].to_list()))
        for map_acro in list_of_map_trackers:
            #MAP DATA
            sel_map_df = gdf[gdf['tracker-acro']==map_acro]
            for gdf in source_data.values:
                print(gdf['tracker-acro'].iloc[0])
                source_acro = gdf['tracker-acro'].iloc[0]
                if source_acro == map_acro:
                    source_df = gdf.copy()
                    # apply same filtering for each dataset
                    # filter by country
                    if mapname == 'asia':
                        needed_geo = asia_countries
                    elif mapname == 'latam':
                        needed_geo = latam_countries
                    elif mapname == 'europe':
                        needed_geo = europe_countries
                    elif mapname == 'africa':
                        needed_geo = africa_countries
                    else:
                        print(f'This is mapname: {mapname}') 
                    
                    # handle countries in creating the source... TODO

                    reg_name_to_delete, col_country_name = find_region_country_colname(source_df)
                    
                    # filter by fuel

                    source_df = create_filtered_df_list_by_map(source_df, col_country_name, reg_name_to_delete, mapname, needed_geo )
                    
                    # now rename so can do analysis easily
                    renaming_dict_sel = renaming_cols_dict[map_acro]
                    source_df = source_df.rename(columns=renaming_dict_sel) 
                    # NOW we compare map data to source data
                    print(f'Source Data {source_acro}: {len(source_df)}')
                    print(f'Map Data {map_acro}: {len(sel_map_df)}')
                    df_missing = source_df[~source_df['id'].isin(sel_map_df['id'])]
                    df_missing_reverse = sel_map_df[~sel_map_df['id'].isin(source_df['id'])]                 
                if len(df_missing) > 0:
                    discrepancies[map_acro] = df_missing
                    print(df_missing) 
                    
                if len(df_missing_reverse) > 0:
                    discrepancies[f'{map_acro}_r'] = df_missing_reverse
                    print(df_missing_reverse)           
            # if discrepancy test if it is same amount as missing/misformatted for that tracker
                # that would require tallying unique problem rows by tracker for all tabs which are on the col 
                # TODO maybe update missing to be similar to misformatted where just one error message and one tab per tracker
            
            # if still discrepant, look at what is in the source but not in the map file
            
            # go through final gdf noting mapname
            # go through source dict
            # print tracker name
            # filter based on mapname in source df
            # first handle mutliple countries in source df
            
            # use something like the below to find what rows are missing
            # print(f'Source Data {tracker}: {len(df)}')
            # print(f'Map Data {tracker}: {len(map_df)}')
            # df_missing = df[~df['id'].isin(map_df['id'])]
            # df_missing_reverse = map_df[~map_df['id'].isin(df['id'])]
            
            
            print('Testing DD Files')
            # should be the same amount unless missing crucial data like a name
            # if discrepant, look at what is in the source but not in the dd file

            
            
            print('Testing refined DD Files')
            # should be the same amount unless missing crucial data like a name
            # if discrepant, look at what is in the source but not in the dd file


            # run the tests from external notebook
            
            
            
            # run the tests any capacity scaling higher than total world energy in joules
            
            # run tests comparing old and new dataset version of final
            print('to do')
            
    
if run_post_tests:
    # post_tests(final_dict_gdfs)
    robust_tests_map()
    robust_tests_dd()
    
