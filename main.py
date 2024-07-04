# main.py

from geomarketing import GeoMarketing
import os
import time
import arcpy
import config

def create_directories(directories):
    for dir_name in directories:
        os.makedirs(os.path.join("data", dir_name), exist_ok=True)

def check_existence(path):
    if not arcpy.Exists(path):
        raise FileNotFoundError(f"File not found: {path}")

# Configure ArcPy to overwrite output files
arcpy.env.overwriteOutput = True

# Create output directories
create_directories(config.OUTPUT_DIRECTORIES)

# Instantiate the GeoMarketing class
geo = GeoMarketing(config.WORKSPACE, config.NETWORK_DATASET)

# Generate and check the necessary layers
total_start_time = time.time()

start_time = time.time()
stations_layer = r"data\Service_Area_Stations\Service_Area_Stations.shp"
geo.calculate_service_area(
    layer_name="Service_Area_Stations",
    impedance="Meters",
    facilities=config.INPUT_LAYERS["stations"],
    output_shapefile=stations_layer
)
check_existence(stations_layer)
end_time = time.time()
print(f"Execution time for calculate_service_area (stations): {end_time - start_time} seconds")

start_time = time.time()
tourist_sites_layer = r"data\Service_Area_Tourist_Sites\Service_Area_Tourist_Sites.shp"
geo.calculate_service_area(
    layer_name="Service_Area_Tourist_Sites",
    impedance="Meters",
    facilities=config.INPUT_LAYERS["tourist_sites"],
    output_shapefile=tourist_sites_layer
)
check_existence(tourist_sites_layer)
end_time = time.time()
print(f"Execution time for calculate_service_area (tourist_sites): {end_time - start_time} seconds")

start_time = time.time()
educational_sites_layer = r"data\Service_Area_Educational_Sites\Service_Area_Educational_Sites.shp"
geo.calculate_service_area(
    layer_name="Service_Area_Educational_Sites",
    impedance="Meters",
    facilities=config.INPUT_LAYERS["educational_sites"],
    output_shapefile=educational_sites_layer,
    travel_from=False
)
check_existence(educational_sites_layer)
end_time = time.time()
print(f"Execution time for calculate_service_area (educational_sites): {end_time - start_time} seconds")

start_time = time.time()
company_density_layer = r"data\Company_Density\companies_reclassified.tif"
geo.calculate_company_density(
    input_points=config.INPUT_LAYERS["companies"],
    output_raster=r"data\Company_Density\companies_kernel.tif",
    normalized_raster=r"data\Company_Density\normalized_companies.tif",
    reclassified_raster=company_density_layer
)
check_existence(company_density_layer)
end_time = time.time()
print(f"Execution time for calculate_company_density: {end_time - start_time} seconds")

start_time = time.time()
result_blocks_layer = config.INPUT_LAYERS["result_blocks"]
geo.generate_filtered_layer(
    input_polygons=config.INPUT_LAYERS["blocks"],
    input_points=config.INPUT_LAYERS["educational_sites"],
    output_path=result_blocks_layer,
    field_to_keep="TP27_PERSO"
)
check_existence(result_blocks_layer)
end_time = time.time()
print(f"Execution time for generate_filtered_layer: {end_time - start_time} seconds")

result_blocks = r"data\APH_Sales_TOSH\result_blocks.shp"
companies_reclassified = r"data\Company_Density\companies_reclassified.tif"
inverted_raster = r"data\Company_Density\companies_reclassified_inverted.tif"
raster_polygons = r"data\Company_Density\companies_reclassified_polygons.shp"

geo.invert_classes_raster(companies_reclassified, inverted_raster)
geo.raster_to_polygons(inverted_raster, raster_polygons)
geo.update_inverted_company_field(result_blocks, raster_polygons)
geo.change_class_order(config.INPUT_LAYERS["result_blocks"], "Class")

start_time = time.time()
layers = [
    stations_layer,
    tourist_sites_layer,
    educational_sites_layer,
    config.INPUT_LAYERS["blocks"],
    result_blocks_layer
]
output_layer = r"data\APH_Sales\result_blocks.shp"
geo.calculate_aph_sales(layers, output_layer)
check_existence(output_layer)
end_time = time.time()
print(f"Execution time for calculate_aph_sales: {end_time - start_time} seconds")

total_end_time = time.time()
print(f"Complete process finished in: {total_end_time - total_start_time} seconds")
