import ee
import geemap
import numpy as np
import pandas as pd
import os
import csv
from tqdm import tqdm
import multiprocessing

# Uncomment the following lines if you are unable to directly access Earth Engine in your region
# Proxy server configuration
# proxy_server_ip = "proxy_ip"
# proxy_server_port = "proxy_port"
# os.environ["http_proxy"] = "http://{0}:{1}".format(proxy_server_ip, proxy_server_port)
# os.environ["https_proxy"] = "https://{0}:{1}".format(proxy_server_ip, proxy_server_port)
# print("The Python environment has been proxied to {0}:{1}".format(proxy_server_ip, proxy_server_port))

Map = geemap.Map()
print("Successfully logged in to Earth Engine")

fieldnames = ['before', 'after','Dis_No',
              'image_path',
              'continent',
              'region',
              'country',
              'flood_began_date',
              'flood_ended_date',]

with open('samplepoints_4000.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

gaul_lv2 = ee.FeatureCollection("FAO/GAUL/2015/level2")

error_field = ['error_img_id', 'error_msg']

with open('error.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=error_field)
    writer.writeheader()
    
flood_image_collection = ee.ImageCollection("projects/ee-newemdat/assets/FloodImageCol_1").filterMetadata('Start_Year', 'greater_than', 2015)
flood_image_list = flood_image_collection.toList(flood_image_collection.size())
flood_image_size = flood_image_collection.size().getInfo()

days_range = 180

def segmentLandCoverCalculation(start_pos):
    print("Process PID {} Created".format(os.getpid()))
     
    end_pos = start_pos + 200
    for i in tqdm(range(start_pos, end_pos)):

        flood_ee_image = ee.Image(flood_image_list.get(i))
        flood_mask = flood_ee_image.select("VV").selfMask()
        flood_info = flood_ee_image.getInfo()

        try:
            flood_began_date = ee.Date.fromYMD(flood_info["properties"]["Start_Year"], flood_info["properties"]["Start_Month"], flood_info["properties"]["Start_Day"])
            flood_ended_date = ee.Date.fromYMD(flood_info["properties"]["End_Year"], flood_info["properties"]["End_Month"], flood_info["properties"]["End_Day"])

            landcover_before = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
                .filterDate(flood_began_date.advance(-days_range, "day"), flood_began_date) \
                .filterBounds(flood_ee_image.geometry()).mode().updateMask(flood_mask).clip(flood_ee_image.geometry())

            landcover_after = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
                .filterDate(flood_ended_date, flood_ended_date.advance(days_range, "day")) \
                .filterBounds(flood_ee_image.geometry()).mode().updateMask(flood_mask).clip(flood_ee_image.geometry())

            # Load a set of classified images
            img_list = [
                landcover_before,
                landcover_after
            ]

            # Which band contains the classified data?
            band = "label"

            # What labels correspond to which pixel values?
            labels = {
                0: "Water", 1: "Trees", 2: "Grass", 3: "Flooded", 4: "Crops",
                5: "Shrub / Scrub", 6: "Build", 7: "Bare", 8: "Snow / Ice",
            }

            label_list = list(range(len(img_list)))
            label_list = [str(label) for label in label_list]

            data = sampling_modified.generate_sample_data(
                flood_mask_clip=flood_mask,
                image_list=img_list,
                image_labels=label_list,
                band=band,
                n=4000,
                scale=10,
                include=list(labels.keys()),
                region=flood_ee_image.geometry(),
            )

            with open('samplepoints_4000.csv', 'a') as csvfile:
                for element in data[0]:
                        try:
                            element['before'] = element['0']
                            element['after'] = element['1']
                            del element['0']
                            del element['1']
                            element['Dis_No'] = flood_info["properties"]["Dis_No"]
                            element["region"] = flood_info["properties"]["Region"]
                            element["country"] = flood_info["properties"]["Country"]
                            element['continent'] = flood_info["properties"]["Continent"]
                            element['flood_began_date'] = "{0}-{1}-{2}".format(flood_info["properties"]["Start_Year"],flood_info["properties"]["Start_Month"],flood_info["properties"]["Start_Day"])
                            element['flood_ended_date'] = "{0}-{1}-{2}".format(flood_info["properties"]["End_Year"],flood_info["properties"]["End_Month"],flood_info["properties"]["End_Day"])
                        except Exception as e:
                            pass

                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writerow(element)

                        print("已写入")
            
            print("Success, move to next")

        except Exception as e:
            err_msg = str(e)
            print("An error has occured", err_msg)
            with open('error.csv', 'a', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=error_field)
                writer.writerow(
                    {
                        "error_img_id": flood_info["properties"]["Dis_No"],
                        "error_msg": err_msg
                    })

                          
if __name__ == '__main__':
    # Create a multi-processing pool
    with multiprocessing.Pool(processes=22) as pool:
        for result in pool.map(segmentLandCoverCalculation, [i for i in range(0, 4146, 200)]):
            print("Process finished")


# The code here was written by aazuspan@GitHub, and we greatly appreciate his code contribution.
# https://github.com/aazuspan/sankee
def get_shared_bands(images: List[ee.Image]) -> List[str]:
    """Get the list of bands that are shared by all images in the list.

    Args:
        img_list: List of ee.Image objects.

    Returns:
        List of band names.
    """
    band_counts = Counter(itertools.chain(*[img.bandNames().getInfo() for img in images]))
    return [band for band, count in band_counts.items() if count == len(images)]

def generate_sample_data(
    *,
    flood_mask_clip: ee.Image,
    image_list: List[ee.Image],
    image_labels: List[str],
    region: ee.Geometry,
    band: str,
    n: int = 500,
    scale: Union[None, int] = None,
    seed: int = 0,
    include: Union[None, List[int]] = None,
    max_classes: Union[None, int] = None,
) -> Tuple[pd.DataFrame, ee.FeatureCollection]:
    """Take a list of images extract image values to each to random points. The image values will be
    stored in a property based on the image label. Then, the samples will be returned as a formated
    dataframe with one column for each image and one row for each sample point.
    """

    def extract_values_at_point(pt):
        for img, label in zip(image_list, image_labels):
            cover = img.reduceRegion(
                reducer=ee.Reducer.first(), geometry=pt.geometry(), scale=scale
            ).get(band)
            pt = ee.Feature(pt).set(label, cover)

        return pt

    
    def removePropertyVV(pt):
        properties = pt.propertyNames()
        selectProperties = properties.filter(ee.Filter.neq('item', "VV"))
        return pt.select(selectProperties)
    
    # Original Code
    # points = ee.FeatureCollection.randomPoints(region=region, points=n, seed=seed)

    # Modified Code
    temp_points = flood_mask_clip.stratifiedSample(numPoints=n,
                  classBand='VV',
                  region=region,
                  scale=10,
                  geometries=True)
    
    points = temp_points.map(removePropertyVV)

    samples = points.map(extract_values_at_point)

    try:
        features = [feat["properties"] for feat in samples.toList(samples.size()).getInfo()]
    except ee.EEException as e:
        if band in str(e):
            shared_bands = get_shared_bands(image_list)
            raise ValueError(
                f"The band `{band}` was not found in all images. Choose from " f"{shared_bands}"
            ) from None
        elif "'count' must be positive" in str(e):
            raise ValueError("No points were sampled. Make sure to pass a 2D `region`.") from None
        else:
            raise e

    data = features

    return data, samples