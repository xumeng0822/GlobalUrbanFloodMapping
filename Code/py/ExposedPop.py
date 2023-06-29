import ee
import geemap
import numpy as np
import pandas as pd
import os
import csv
import time
import multiprocessing

# Uncomment the following lines if you are unable to directly access Earth Engine in your region
#os.environ["http_proxy"] = "http://{proxy_ip}:{proxy_port}"
#os.environ["https_proxy"] = "https://{proxy_ip}:{proxy_port}"

Map = geemap.Map()

flood_img_coll = ee.ImageCollection("projects/ee-newemdat/assets/FloodImageCol_1")
worldpop = ee.ImageCollection("WorldPop/GP/100m/pop")
gaul_lv2 = ee.FeatureCollection("FAO/GAUL/2015/level2")

fieldnames = ['ADM2_CODE',
              'ADM2_NAME',
              'ADM1_CODE',
              'ADM1_NAME',
              'ADM0_CODE',
              'ADM0_NAME',
              '2015_flood_exposed_population',
              '2016_flood_exposed_population',
              '2017_flood_exposed_population',
              '2018_flood_exposed_population',
              '2019_flood_exposed_population',
              '2020_flood_exposed_population',
              '2021_flood_exposed_population',
              '2022_flood_exposed_population']

error_field = ['error_id', 'error_msg']

with open('pop_yearly.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

with open('error_log.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=error_field)
    writer.writeheader()

with open('g2.csv', newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    dict_list = list(reader)

dict_size = len(dict_list)

def segment_land_cover_calculation(start_pos):
    end_pos = start_pos + 1000
    for item in dict_list[start_pos:end_pos]:
        try:
            gaul_code = item["ADM2_CODE"]
            admin_lv2 = gaul_lv2.filterMetadata('ADM2_CODE', 'equals', int(gaul_code)).first().geometry()

            result = item

            for year in range(2015, 2023):
                key_name = "{}_flood_exposed_population".format(year)

                try:
                    flood_img_coll_filtered = flood_img_coll.filterBounds(admin_lv2).filterMetadata("Start_Year", "equals", year).mosaic().select("VV").clip(admin_lv2)
                    flood_img_mask = flood_img_coll_filtered.selfMask()

                    if (year == 2021) or (year == 2022):
                        worldpop_mosaic = worldpop.filterBounds(admin_lv2).filter(ee.Filter.eq('year', 2020)).mosaic()
                    else:
                        worldpop_mosaic = worldpop.filterBounds(admin_lv2).filter(ee.Filter.eq('year', year-1)).mosaic()

                    worldpop_mosaic_clipped = worldpop_mosaic.clip(admin_lv2).updateMask(flood_img_mask)

                    pop_sum = int(worldpop_mosaic_clipped.reduceRegion(
                        reducer=ee.Reducer.sum(),
                        geometry=admin_lv2,
                        scale=100,
                        bestEffort=True,
                        maxPixels=1e12).getInfo().get('population'))

                    result[key_name] = pop_sum

                except Exception as e:
                    result[key_name] = 0

            # Write it to the CSV file
            with open('pop_yearly.csv', 'a') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(result)

        # If an error occurs, record it and write it to the error.csv file
        except Exception as e:
            print(str(e))
            continue


if __name__ == '__main__':
    # Create a multiprocessing pool
    with multiprocessing.Pool(processes=35) as pool:
        for result in pool.map(segment_land_cover_calculation, [i for i in range(0, dict_size, 1000)]):
            print("Done.")
