import geemap
import ee
import time
import os
from tqdm import tqdm

# Uncomment the following lines if you are unable to directly access Earth Engine in your region
# Proxy server configuration
# proxy_server_ip = "proxy_ip"
# proxy_server_port = "proxy_port"
# os.environ["http_proxy"] = "http://{0}:{1}".format(proxy_server_ip, proxy_server_port)
# os.environ["https_proxy"] = "https://{0}:{1}".format(proxy_server_ip, proxy_server_port)
# print("The Python environment has been proxied to {0}:{1}".format(proxy_server_ip, proxy_server_port))

# Initialize GEE via geemap
Map = geemap.Map()

print("Successfully logged in to Earth Engine")

# Select the image dataset
flood_image_collection = ee.ImageCollection('projects/ee-newemdat/assets/FloodImageCol_1').filterMetadata("Start_Year",
                                                                                                          "greater_than",
                                                                                                          2015)
days_range = 180

sleep = 0

# Calculate land-cover changes
flood_image_list = flood_image_collection.toList(flood_image_collection.size())
flood_image_size = flood_image_collection.size().getInfo()

print(flood_image_size)

def image_area(img, region=None, scale=None, denominator=1.0):
    """Calculates the area of an image.

    Args:
        img (object): ee.Image
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        denominator (float, optional): The denominator to use for converting size from square meters to other units. Defaults to 1.0.

    Returns:
        object: ee.Dictionary
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = geemap.image_scale(img)

    pixel_area = (
        img.unmask().neq(ee.Image(0)).multiply(ee.Image.pixelArea()).divide(denominator)
    )
    img_area = pixel_area.reduceRegion(
        **{
            "geometry": region,
            "bestEffort": True,
            "reducer": ee.Reducer.sum(),
            "scale": scale,
            "maxPixels": 1e12,
        }
    )
    return img_area

for i in range(0, flood_image_size):
    while True:
        try:
            flood_ee_image = ee.Image(flood_image_list.get(i))
            flood_info = flood_ee_image.getInfo()
            print("Uploading task No.{} {}".format(i, flood_info["properties"]["Dis_No"]))

            f = open("demofile2.txt", "a")
            f.write("No.{} {}\n".format(i, flood_info["properties"]["Dis_No"]))

            f.close()
            # Mask its flood mapping result
            flood_ee_image_mask = flood_ee_image.select("VV").selfMask()

            flood_area = image_area(flood_ee_image_mask, denominator=1e6).get('VV')

            # Reconstruct date info
            flood_began_date = ee.Date.fromYMD(flood_ee_image.get("Start_Year"), flood_ee_image.get("Start_Month"),
                                               flood_ee_image.get("Start_Day"), )
            flood_ended_date = ee.Date.fromYMD(flood_ee_image.get("End_Year"), flood_ee_image.get("End_Month"),
                                               flood_ee_image.get("End_Day"), )

            landcover_before_flood = geemap.dynamic_world(flood_ee_image.geometry(),
                                                          flood_began_date.advance(-days_range, "day"),
                                                          flood_began_date,
                                                          return_type='class').updateMask(flood_ee_image_mask)

            landcover_after_flood = geemap.dynamic_world(flood_ee_image.geometry(), flood_ended_date,
                                                         flood_ended_date.advance(days_range, "day"),
                                                         return_type='class').updateMask(flood_ee_image_mask)

            water_before = image_area(landcover_before_flood.eq(float(0)), scale=10, denominator=1e6).get('label_mode')
            trees_before = image_area(landcover_before_flood.eq(float(1)), scale=10, denominator=1e6).get('label_mode')
            grass_before = image_area(landcover_before_flood.eq(float(2)), scale=10, denominator=1e6).get('label_mode')
            flooded_vegetation_before = image_area(landcover_before_flood.eq(float(3)), scale=10, denominator=1e6).get(
                'label_mode')
            crops_before = image_area(landcover_before_flood.eq(float(4)), scale=10, denominator=1e6).get('label_mode')
            shrub_and_scrub_before = image_area(landcover_before_flood.eq(float(5)), scale=10, denominator=1e6).get(
                'label_mode')
            built_before = image_area(landcover_before_flood.eq(float(6)), scale=10, denominator=1e6).get('label_mode')
            bare_before = image_area(landcover_before_flood.eq(float(7)), scale=10, denominator=1e6).get('label_mode')
            snow_and_ice_before = image_area(landcover_before_flood.eq(float(8)), scale=10, denominator=1e6).get(
                'label_mode')

            water_after = image_area(landcover_after_flood.eq((float(0))), scale=10, denominator=1e6).get('label_mode')
            trees_after = image_area(landcover_after_flood.eq((float(1))), scale=10, denominator=1e6).get('label_mode')
            grass_after = image_area(landcover_after_flood.eq((float(2))), scale=10, denominator=1e6).get('label_mode')
            flooded_vegetation_after = image_area(landcover_after_flood.eq((float(3))), scale=10, denominator=1e6).get(
                'label_mode')
            crops_after = image_area(landcover_after_flood.eq((float(4))), scale=10, denominator=1e6).get('label_mode')
            shrub_and_scrub_after = image_area(landcover_after_flood.eq((float(5))), scale=10, denominator=1e6).get(
                'label_mode')
            built_after = image_area(landcover_after_flood.eq((float(6))), scale=10, denominator=1e6).get('label_mode')
            bare_after = image_area(landcover_after_flood.eq((float(7))), scale=10, denominator=1e6).get('label_mode')
            snow_and_ice_after = image_area(landcover_after_flood.eq((float(8))), scale=10, denominator=1e6).get(
                'label_mode')

            try:
                adm2_name = flood_info["properties"]["ADM2_NAME"]
            except Exception as e:
                adm2_name = ""
            try:
                adm1_name = flood_info["properties"]["ADM1_NAME"]
            except Exception as e:
                adm1_name = ""

            geojson = {
                'type': 'FeatureCollection',
                'columns': {
                    'key': 'String',
                    'system:index': 'String'
                },
                'features': [
                    {
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [
                                0,
                                0
                            ]
                        },
                        'id': '0',
                        'properties': {
                            'Dis_No': flood_ee_image.get("Dis_No"),
                            'image_path': flood_ee_image.get("system:id"),
                            'continent': flood_ee_image.get("Continent"),
                            'region': flood_ee_image.get("Region"),
                            'country': flood_ee_image.get("Country"),
                            'Start_Year': flood_ee_image.get("Start_Year"),
                            'Start_Month': flood_ee_image.get("Start_Month"),
                            'Start_Day': flood_ee_image.get("Start_Day"),
                            'Start_Date': flood_began_date.format('YYYY-MM-dd'),
                            'End_Year': flood_ee_image.get("End_Year"),
                            'End_Month': flood_ee_image.get("End_Month"),
                            'End_Day': flood_ee_image.get("End_Day"),
                            'End_Date': flood_ended_date.format('YYYY-MM-dd'),
                            'landcover_before_began_date': flood_began_date.advance(-days_range, "day").format(
                                'YYYY-MM-dd'),
                            'landcover_before_ended_date': flood_began_date.format('YYYY-MM-dd'),
                            'landcover_after_began_date': flood_ended_date.format('YYYY-MM-dd'),
                            'landcover_after_ended_date': flood_ended_date.advance(-days_range, "day").format(
                                'YYYY-MM-dd'),
                            'flood_area': flood_area,
                            'scale': 10,
                            'ADM1_NAME': adm1_name,
                            'ADM2_NAME': adm2_name,
                            'water_area_before_flood': water_before,
                            'water_area_after_flood': water_after,
                            'trees_area_before_flood': trees_before,
                            'trees_area_after_flood': trees_after,
                            'grass_area_before_flood': grass_before,
                            'grass_area_after_flood': grass_after,
                            'flooded_vegetation_area_before_flood': flooded_vegetation_before,
                            'flooded_vegetation_area_after_flood': flooded_vegetation_after,
                            'crops_area_before_flood': crops_before,
                            'crops_area_after_flood': crops_after,
                            'shrub_and_scrub_area_before_flood': shrub_and_scrub_before,
                            'shrub_and_scrub_area_after_flood': shrub_and_scrub_after,
                            'built_area_before_flood': built_before,
                            'built_area_after_flood': built_after,
                            'bare_area_before_flood': bare_before,
                            'bare_area_after_flood': bare_after,
                            'snow_and_ice_area_before_flood': snow_and_ice_before,
                            'snow_and_ice_area_after_flood': snow_and_ice_after,
                        }
                    }
                ]
            }

            geojson_fc = ee.FeatureCollection(geojson)

            pro_header = {
                'Dis_No': flood_ee_image.get("Dis_No"),
                'image_path': flood_ee_image.get("system:id"),
                'continent': flood_ee_image.get("Continent"),
                'region': flood_ee_image.get("Region"),
                'country': flood_ee_image.get("Country"),
                'Start_Year': flood_ee_image.get("Start_Year"),
                'Start_Month': flood_ee_image.get("Start_Month"),
                'Start_Day': flood_ee_image.get("Start_Day"),
                'Start_Date': flood_began_date.format('YYYY-MM-dd'),
                'End_Year': flood_ee_image.get("End_Year"),
                'End_Month': flood_ee_image.get("End_Month"),
                'End_Day': flood_ee_image.get("End_Day"),
                'End_Date': flood_ended_date.format('YYYY-MM-dd'),
                'landcover_before_began_date': flood_began_date.advance(-days_range, "day").format('YYYY-MM-dd'),
                'landcover_before_ended_date': flood_began_date.format('YYYY-MM-dd'),
                'landcover_after_began_date': flood_ended_date.format('YYYY-MM-dd'),
                'landcover_after_ended_date': flood_ended_date.advance(-days_range, "day").format('YYYY-MM-dd'),
                'flood_area': flood_area,
                'scale': 10,
                'ADM1_NAME': adm1_name,
                'ADM2_NAME': adm2_name,
                'water_area_before_flood': water_before,
                'water_area_after_flood': water_after,
                'trees_area_before_flood': trees_before,
                'trees_area_after_flood': trees_after,
                'grass_area_before_flood': grass_before,
                'grass_area_after_flood': grass_after,
                'flooded_vegetation_area_before_flood': flooded_vegetation_before,
                'flooded_vegetation_area_after_flood': flooded_vegetation_after,
                'crops_area_before_flood': crops_before,
                'crops_area_after_flood': crops_after,
                'shrub_and_scrub_area_before_flood': shrub_and_scrub_before,
                'shrub_and_scrub_area_after_flood': shrub_and_scrub_after,
                'built_area_before_flood': built_before,
                'built_area_after_flood': built_after,
                'bare_area_before_flood': bare_before,
                'bare_area_after_flood': bare_after,
                'snow_and_ice_area_before_flood': snow_and_ice_before,
                'snow_and_ice_area_after_flood': snow_and_ice_after,
            }

            # Export the FeatureCollection to a KML file.
            task = ee.batch.Export.table.toDrive(**{
                'collection': geojson_fc,
                'folder': 'WhookWhook',
                'description': 'Task No.{} Land Cover Area of {}'.format(i, flood_info["properties"]["Dis_No"]),
                'fileFormat': 'CSV',
                'selectors': list(pro_header.keys())
            })
            task.start()
            if sleep == 400:
                print("Sleep a while...")
                time.sleep(9600)
                sleep = 0
            else:
                sleep += 1
        except:
            continue
        break
