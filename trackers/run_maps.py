
from single_tracker_maps_script import *
# from multi_tracker_maps_script import *
import subprocess
from tqdm import tqdm # can adapt more, special tweaking for dataframe!
# TODO make sure the dependency map makes sense, so it calls both single and multi script depending on new data, try with tests
###
# CALL ALL FUNCTIONS


for tracker in tqdm(trackers_to_update, desc='Baking'):
    # print(tracker)
    
    if tracker == 'Oil & Gas Extraction':
        test_results_folder = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/goget/test_results/'

        output_folder = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/goget/compilation_output/'

        # creates single map file
        # handle production data
        key, tabs = get_key_tabs_prep_file(tracker)

        df_tuple = create_df(key, tabs)
        main = df_tuple[0]
        prod = df_tuple[1]
        # df has df['other'] column to distinguish between main and prod/res
        # result will be data ready for map, after scott's code
        df = process_goget_reserve_prod_data(main, prod)
        df = rename_cols(df) # will need to adjust for goget's columns
        df = fix_status_space(df)   
        # df = format_values(df)
        df = fix_status_inferred(df)         
        df = filter_cols(df,final_cols=['country/area', 'wiki-name',
                                        'status', 'production-start-year',  
                                        'operator', 'owner', 'parent','lat', 'lng', 'location-accuracy', 'subnational-unit-(province,-state)',
                                        'gem-region', 'unit-id', 'url', 'country-list', 'discovery-year', 'fid-year', 'production---oil-(million-bbl/y)',
                                        'production-year---oil', 'production---gas-(million-m³/y)', 'production-year---gas', 'production---total-(oil,-gas-and-hydrocarbons)-(million-boe/y)'             
                                        ])
        
        # adjust statuses 'operating', 'in_development', 'discovered', 'shut_in', 'decommissioned', 'cancelled', 'abandoned', 'UGS', ""
        
        df = input_to_output(df, f'{output_folder}{tracker}-map-file-{iso_today_date}.csv')
        # creates multi-map files 
        print('DONE MAKING GOGET SINGLE MAP onto MULTI MAPS')
        input('continue?')
        # creates multi-tracker maps
        subprocess.run(["python", "/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/multi_tracker_maps_script.py"])                 
                  
    elif tracker == 'Bioenergy':

        test_results_folder = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/bioenergy/test_results/'

        output_folder = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/bioenergy/compilation_output/'

        # creates single map file
        key, tabs = get_key_tabs_prep_file(tracker)

        df = create_df(key, tabs)
        df = rename_cols(df)
        df = fix_status_inferred(df)
        df = filter_cols(df,final_cols=['country/area', 'project-name', 'fuel', 'unit-name', 'project-name-in-local-language-/-script',
                                        'capacity-(mw)', 'status', 'start-year', 'retired-year', 'hydrogen-capable',
                                        'operator(s)', 'owner(s)', 'lat', 'lng', 'location-accuracy', 'city', 'state/province',
                                        'region', 'gem-phase-id', 'url'          
                                        ])
        df = input_to_output(df, f'{output_folder}{tracker}-map-file-{iso_today_date}.csv')
        test_stats(df)
        # creates multi-map files 
        print('DONE MAKING GBPT SINGLE MAP onto MULTI MAPS')
        input('continue?')
        # creates multi-tracker maps
        # if tracker to update is coal terminals then look at sheet and create all regional and of course single
        subprocess.run(["python", "/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/multi_tracker_maps_script.py"])                 
          
        # if test:
        #     check_expected_number(incorporated_dict_list_gdfs_by_map) # TODO HANDLE THIS ONE for dict or use the one thats been concatenated

    elif tracker == 'Oil & Gas Plants':
        # continue for all of them that are in or not in multi tracker maps
        test_results_folder = f'{tracker_folder_path}gas-plant/test_results/'

        output_folder = f'{tracker_folder_path}gas-plant/compilation_output/'

        input_file_path = f'{tracker_folder_path}gas-plant/compilation_input/'
                
        # multi_tracker_log_sheet_key = '15l2fcUBADkNVHw-Gld_kk7EaMiFFi8ysWt6aXVW26n8'
        # multi_tracker_log_sheet_tab = ['multi_map']
        # prep_file_tab = ['prep_file']
        # key = '1WRRFRuR9mWxZpko-VMYH5xm0LzRX_qM7W73nGGi4Jmg'
        # tabs = ['Data', 'Below Threshold']
        
        # creates single map file
        key, tabs = get_key_tabs_prep_file(tracker)
        df = create_df(key, tabs)
        df = rename_cols(df)
        df = fix_status_inferred(df)
        df = filter_cols(df,final_cols=['gem-location-id','country/area', 'plant-name', 'fuel', 'unit-name', 'plant-name-in-local-language-/-script',
                                        'capacity-(mw)', 'status', 'start-year', 'retired-year', 'parent(s)', 'turbine/engine-technology',
                                        'operator(s)', 'owner(s)', 'lat', 'lng', 'location-accuracy', 'city', 'state/province',
                                        'region', 'url'          
                                        ])
        # make sure 0% and 100% is removed from owners

        df = remove_implied_owner(df)
        df = formatting_checks(df)

        
        df = input_to_output(df, f'{output_folder}{tracker}-map-file-{iso_today_date}.csv')
        # test_stats(df)
        print('DONE MAKING GOGPT SINGLE MAP onto MULTI MAPS')
        input('Continue?')
        # creates multi-tracker maps
        # if tracker to update is coal terminals then look at sheet and create all regional and of course single
        subprocess.run(["python", "/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/multi_tracker_maps_script.py"])                 

    elif tracker == 'Plumes':
        print(f'Starting GMET for release {tracker}')
        # if augmented: # these vars are all set in all_config, this helped adapt AET code to all multi maps
        #     print('Start augmented')
        #     needed_map_and_tracker_dict = what_maps_are_needed(multi_tracker_log_sheet_key, multi_tracker_log_sheet_tab)
        #     # map_country_region has the list of needed maps to be created and their countries/regions
        #     needed_tracker_geo_by_map = what_countries_or_regions_are_needed_per_map(multi_tracker_countries_sheet, needed_map_and_tracker_dict)
        #     # print(path_for_download_and_map_files)
        #     folder_setup(needed_tracker_geo_by_map)
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print(f'Ended augmented {elapsed_time}')
            
        # if data_filtering: # this creates gdfs and dfs for all filtered datasets per map, lots of repetition here
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print('Start data filtering')
        #     prep_df = create_prep_file(multi_tracker_log_sheet_key, prep_file_tab) 
        #     conversion_df = create_conversion_df(conversion_key, conversion_tab)

        #     dict_list_dfs_by_map, dict_list_gdfs_by_map = pull_gsheet_data(prep_df, needed_tracker_geo_by_map) # map_country_region
        #     incorporated_dict_list_gdfs_by_map, incorporated_dict_list_dfs_by_map = incorporate_geojson_trackers(goit_geojson, ggit_geojson, ggit_lng_geojson,dict_list_dfs_by_map, dict_list_gdfs_by_map) 
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print(f'Ended data filtering {elapsed_time}') 
                       
        # if map_create:
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print('Start map file creation')
        #     custom_dict_list_gdfs_by_map = split_goget_ggit(incorporated_dict_list_gdfs_by_map)  #incorporated_dict_list_gdfs_by_map
        #     custom_dict_list_gdfs_by_map_with_conversion = assign_conversion_factors(custom_dict_list_gdfs_by_map, conversion_df)
        #     renamed_one_gdf_by_map = rename_gdfs(custom_dict_list_gdfs_by_map_with_conversion)
        #     # cleaned_dict_map_by_one_gdf = remove_null_geo(renamed_one_gdf_by_map) # doesn't do anything
        #     cleaned_dict_map_by_one_gdf_with_conversions = capacity_conversions(renamed_one_gdf_by_map)
        #     cleaned_dict_by_map_one_gdf_with_better_statuses = map_ready_statuses(cleaned_dict_map_by_one_gdf_with_conversions)
            
        #     cleaned_dict_by_map_one_gdf_with_better_countries = map_ready_countries(cleaned_dict_by_map_one_gdf_with_better_statuses)
        #     one_gdf_by_maptype = workarounds_eg_interim_goget_gcmt(cleaned_dict_by_map_one_gdf_with_better_countries)
        #     one_gdf_by_maptype_fixed = last_min_fixes(one_gdf_by_maptype) 
        #     final_dict_gdfs = create_map_file(one_gdf_by_maptype_fixed)
        #     final_count(final_dict_gdfs)
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print('End map file creation')
                    
        
    elif tracker == 'LNG Terminals':
        print('Starting on lng terminals')
    #     # if LNG Terminals, then we need to update GGIT, and all regional trackers
    #     # GGIT is unique because as a "singular" tracker it takes two files lng and gas pipelines
    #     # they are both local files
    #     # they need to go through lots for parsing so we'll copy that from the logic we have for regional
    #     # then once that's created we'll create the regional trackers
    #     # for EGT we will include hydrogen pipeline data 
        
    #     # SHOULD I USE incorporate_geojson_trackers
    #     # we can skip finding country col because no filter on singular
    #     # do we need to convert if we can use the bcm/y I don't think so no but let's keep it like the multi
    #     # then we need to rename and concat with rename_gdfs
    #     # then it drops columms based on final_cols paramter set in config
        
        
    #     # local non gspread so 
    #     test_results_folder = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/ggit/test_results/'

    #     output_folder = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/ggit/compilation_output/'

    #     input_file_json = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/source/GEM-GGIT-LNG-Terminals-2024-09 DATA TEAM COPY.geojson'
    #     # incorporate gas pipeline data as well
    #     gas_pipeline_json = '/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/testing/source/GEM-GGIT-Gas-Pipelines-2023-12 copy.geojson'                
    #     # creates single map file
    #     ggit_lng_gdf, crs = geojson_to_gdf(input_file_json)
    #     ggit_lng_gdf['tracker-acro'] = 'GGIT-lng'
    #     ggit_gdf, crs = geojson_to_gdf(gas_pipeline_json)
    #     ggit_gdf['tracker-acro'] = 'GGIT'
    #     dict_by_map = {'ggit': [ggit_lng_gdf, ggit_gdf]}
    #     dict_by_map = split_goget_ggit(dict_by_map)
    #     conversion_df = create_conversion_df(conversion_key, conversion_tab)
    #     dict_by_map = assign_conversion_factors(dict_by_map, conversion_df) # feed in conversion_df from multi tracker maps script tho will it be called? 
    #     gdf_by_map = rename_gdfs(dict_by_map) # custom_dict_list_gdfs_by_map_with_conversion
    #     gdf_by_map = capacity_conversions(gdf_by_map)
    #     gdf_by_map = map_ready_statuses(gdf_by_map) # handles for map statuses and inferred
    #     gdf_by_map = map_ready_countries(gdf_by_map) # handles for multiple areas 
    #     gdf_by_map = workarounds_eg_interim_goget_gcmt(gdf_by_map) # mainly handles multiple country sitatuions for details card 
    #     gdf_by_map = last_min_fixes(gdf_by_map) # likely do not need this
        
    #     # can print map file here or can try what we have below with the folders set up above
    #     final_dict_gdfs = create_map_file(gdf_by_map)
    #     # final_count(final_dict_gdfs)

    #     final_dict_gdfs = input_to_output_all(final_dict_gdfs, f'{output_folder}{tracker}-map-file-{iso_today_date}')
    #     # test_stats(gdf) 
    #     # now all maps dependent on LNG
    #     # creates multi-map files 
    #     # input('Main global map done. Do you want to proceed with dependent maps?')
        
    # # if augmented: # these vars are all set in all_config, this helped adapt AET code to all multi maps
    #     print('Start augmented')
    #     map_tracker_dict = what_maps_are_needed(multi_tracker_log_sheet_key, multi_tracker_log_sheet_tab)
    #     # map_country_region has the list of needed maps to be created and their countries/regions
    #     print(map_tracker_dict)
    #     # input('inspect') # this works 
    #     map_tracker_dict = what_countries_or_regions_are_needed_per_map(multi_tracker_countries_sheet, map_tracker_dict)
    #     # print(path_for_download_and_map_files)
    #     # folder_setup(needed_tracker_geo_by_map)
    #     end_time = time.time()  # Record the end time
    #     elapsed_time = end_time - start_time  # Calculate the elapsed time
    #     print(f'Ended augmented {elapsed_time}')
        
    # # if data_filtering: # this creates gdfs and dfs for all filtered datasets per map, lots of repetition here
    #     end_time = time.time()  # Record the end time
    #     elapsed_time = end_time - start_time  # Calculate the elapsed time
    #     print('Start data filtering')
    #     prep_df = create_prep_file(multi_tracker_log_sheet_key, prep_file_tab) 
    #     conversion_df = create_conversion_df(conversion_key, conversion_tab)

    #     map_tracker_dict_dfs, map_tracker_dict_gdfs = pull_gsheet_data(prep_df, map_tracker_dict) # map_country_region
    #     print(f'will this also be empty? {map_tracker_dict_gdfs}')
    #     map_tracker_dict_gdfs, map_tracker_dict_dfs = incorporate_geojson_trackers(goit_geojson, ggit_geojson, ggit_lng_geojson, map_tracker_dict_dfs, map_tracker_dict_gdfs) 
    #     end_time = time.time()  # Record the end time
    #     elapsed_time = end_time - start_time  # Calculate the elapsed time
    #     print(f'Ended data filtering {elapsed_time}')
        
    # # if map_create:
    #     end_time = time.time()  # Record the end time
    #     elapsed_time = end_time - start_time  # Calculate the elapsed time
    #     print(f'Start map file creation {elapsed_time}')
    #     map_tracker_dict_gdfs = split_goget_ggit(map_tracker_dict_gdfs)  #incorporated_dict_list_gdfs_by_map
    #     print(f'Will this be empty too? {map_tracker_dict_gdfs}')
    #     map_tracker_dict_gdfs = assign_conversion_factors(map_tracker_dict_gdfs, conversion_df)
    #     renamed_one_gdf = rename_gdfs(map_tracker_dict_gdfs)
    #     # cleaned_dict_map_by_one_gdf = remove_null_geo(renamed_one_gdf) # doesn't do anything
    #     renamed_one_gdf = capacity_conversions(renamed_one_gdf)
    #     renamed_one_gdf = map_ready_statuses(renamed_one_gdf)
        
    #     renamed_one_gdf = map_ready_countries(renamed_one_gdf)
    #     renamed_one_gdf = workarounds_eg_interim_goget_gcmt(renamed_one_gdf)
    #     renamed_one_gdf = last_min_fixes(renamed_one_gdf) 
    #     print(f'This is final gdf keys for {tracker}: {one_gdf_by_maptype}')
    #     final_dict_gdfs = create_map_file(renamed_one_gdf)
        
    #     final_dict_gdfs = input_to_output_all(final_dict_gdfs, f'{output_folder}{tracker}-map-file-{iso_today_date}')
    #     final_count(final_dict_gdfs)

    #     end_time = time.time()  # Record the end time
    #     elapsed_time = end_time - start_time  # Calculate the elapsed time
    #     print(f'End map file creation {elapsed_time}')          
    
        ## COMMENTING OUT FOR NOW TIL WE HAVE MAP WORKING

        # if about_create: # this creates and saves a preliminary file with all about pages no adjustments made
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print('Start about creation')
        #     about_df_dict_by_map = gather_all_about_pages(prev_key_dict, prep_df, new_release_date, previous_release_date, needed_tracker_geo_by_map)
        #     create_about_page_file(about_df_dict_by_map)
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print(f'End about creation {elapsed_time}')

        # if dwlnd_create: # this creates and saves the tabular data sheets for the data download from the filtered dfs
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print(f'Start dwlnd creation {elapsed_time}')
        #     create_data_dwnld_file(incorporated_dict_list_dfs_by_map) 
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print(f'End dwlnd creation {elapsed_time}')
            
        # if refine: # this reorders the data download file
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print('Start refining')
        #     if local_copy:
        #         about_df_dict_by_map = ''
        #         incorporated_dict_list_dfs_by_map = ''
        #     reorder_dwld_file_tabs(about_df_dict_by_map, incorporated_dict_list_dfs_by_map) 
        #     end_time = time.time()  # Record the end time
        #     elapsed_time = end_time - start_time  # Calculate the elapsed time
        #     print('End refining')    

    elif tracker == 'Wind':
        # continue for all of them that are in or not in multi tracker maps
        test_results_folder = f'{tracker_folder_path}wind/test_results/'

        output_folder = f'{tracker_folder_path}wind/compilation_output/'

        # input_file_path = f'{tracker_folder_path}coal-terminals/compilation_input/'
        
        os.makedirs(test_results_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)       
             

        # creates single map file
        key, tabs = get_key_tabs_prep_file(tracker)
        df = create_df(key, tabs)
        df = rename_cols(df)
        df = fix_status_inferred(df)
        df = filter_cols(df,final_cols=['gem-location-id', 'gem-phase-id', 'country/area', 'phase-name', 'project-name', 'project-name-in-local-language-/-script',
                                        'other-name(s)', 'capacity-(mw)', 'status', 'start-year', 'retired-year', 'location-accuracy',
                                         'owner', 'lat', 'lng', 'state/province', 'operator', 'installation-type',
                                        'region', 'url', 'owner-name-in-local-language-/-script', 'operator-name-in-local-language-/-script'        
                                        ])
            
        
        df = input_to_output(df, f'{output_folder}{tracker}-map-file-{iso_today_date}.csv')
        # test_stats(df)

        print('DONE MAKING WIND SINGLE MAP onto MULTI MAPS')
        input('continue?')
        # creates multi-tracker maps
        # if tracker to update is coal terminals then look at sheet and create all regional and of course single
        # subprocess.run(["python", "/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/multi_tracker_maps_script.py"])                 


    elif tracker == 'Solar':
        # continue for all of them that are in or not in multi tracker maps
        test_results_folder = f'{tracker_folder_path}solar/test_results/'

        output_folder = f'{tracker_folder_path}solar/compilation_output/'
        
        os.makedirs(test_results_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)       
             

        # creates single map file
        key, tabs = get_key_tabs_prep_file(tracker)
        df = create_df(key, tabs)
        df = rename_cols(df)
        df = fix_status_inferred(df)
        df = filter_cols(df,final_cols=['gem-location-id', 'gem-phase-id', 'country/area', 'phase-name', 'project-name', 'project-name-in-local-language-/-script',
                                        'other-name(s)', 'capacity-(mw)', 'status', 'start-year', 'retired-year', 'location-accuracy',
                                         'owner', 'lat', 'lng', 'state/province', 'operator', 'technology-type',
                                        'region', 'url', 'owner-name-in-local-language-/-script', 'operator-name-in-local-language-/-script'         
                                        ])
                
        
        df = input_to_output(df, f'{output_folder}{tracker}-map-file-{iso_today_date}.csv')
        # test_stats(df)

        print('DONE MAKING SOLAR SINGLE MAP onto MULTI MAPS')
        input('continue?')
        # creates multi-tracker maps
        # if tracker to update is coal terminals then look at sheet and create all regional and of course single
        # subprocess.run(["python", "/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/multi_tracker_maps_script.py"])                 
    
    elif tracker == 'Coal Plants':
        # continue for all of them that are in or not in multi tracker maps
        test_results_folder = f'{tracker_folder_path}coal-plant/test_results/'

        output_folder = f'{tracker_folder_path}coal-plant/compilation_output/'
        
        os.makedirs(test_results_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)       
             

        # creates single map file
        key, tabs = get_key_tabs_prep_file(tracker)
        df = create_df(key, tabs)
        df = rename_cols(df)
        df = fix_status_inferred(df)
        df = filter_cols(df,final_cols=['gem-location-id', 'gem-unit/phase-id', 'country', 'unit-name', 'plant-name', 'plant-name-(other)',
                                        'plant-name-(local)', 'capacity-(mw)', 'status', 'start-year', 'retired-year', 'location-accuracy',
                                         'owner', 'parent','lat', 'lng', 'combustion-technology',
                                        'region', 'url', 'subnational-unit-(province,-state)'        
                                        ])
                
        
        df = input_to_output(df, f'{output_folder}{tracker}-map-file-{iso_today_date}.csv')
        # test_stats(df)

        print('DONE MAKING Coal SINGLE MAP onto MULTI MAPS')
        input('continue?')
    
    subprocess.run(["python", "/Users/gem-tah/GEM_INFO/GEM_WORK/earthrise-maps/gem-tracker-maps/trackers/multi_tracker_maps_script.py"])                 
          
# if tracker in tracker to update is part of a multi tracker map then run that script in addition
# individual script

# individual script should have if else for tracker nuances
# multi map script can be the same as I used for the AET just moved out of africa-energy folder

# so for october should be:
# - bioenergy unique map
# - africa energy
# - latam energy
# - GIPT (wait on James)

# one script for all maps
# print where fails which file which tracker
# output to test file
# output for download file 
# outpuf for map file 

# first bring in gas to africa




# inputs differences for integrated is just the GIPT file from James

# new_tracker_data = 'INSERT TRACKER ACRONYM HERE'
# new_tracker_release_date = 'INSERT RELEASE DATE HERE'
