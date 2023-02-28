# GlobalUrbanFloodMapping
This repository contains the code and data used in our reseach.

### Data
#### Flood Maps

Flood maps for the three methods (Fixed, Otsu, NDFI) can be viewed online on the Google Earth Engine (GEE) platform:
https://2110276222.users.earthengine.app/view/gfad


#### Flood Events
1. `emdat_public_2022_10_08.xlsx`: All Flood Events available from the Emergency Events Database (EM-DAT) (2015-2022).
2. `Total_flood_event_ID.csv`: Flood events following reclassification by first level district.


#### Validation
3. `Validation\uniqueID_300.csv`: Contains the IDs of all flood events used for validation.
4. `Validation\Total_Sample_uniqueID3.csv`: Analyst samples(polygon) of all flood/non-flood markers for flood events. The first column is the marking category (flood/non-flood), the second column is the coordinates of the marking point, and the third column is the ID of the flood event plus the name of the marking person.
How to verify: Upload the above two files to GEE and run the following code to calculate the accuracy https://code.earthengine.google.com/0460d00668ce03a9576de42b16f562fb?noload=true
5. `Validation\Box Graph`: This folder contains the accuracy verified by the three methods and is also the data used to draw the boxplot
