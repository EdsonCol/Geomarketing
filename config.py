# config.py

import os

# Initial configuration
WORKSPACE = r"data\Marketing_ND.gdb"
NETWORK_DATASET = os.path.join(WORKSPACE, "Vias_ANT", "Antioquia_NDC")

# Input layers paths
INPUT_LAYERS = {
    "stations": r"data\layers\stations_points_layer",
    "tourist_sites": r"data\layers\tourist_sites_points_layer",
    "educational_sites": r"data\layers\educational_sites_points_layer",
    "companies": r"data\layers\copmanies_points_layer",
    "blocks": r"data\layers\blocks_polygons_layer",
    "result_blocks": r"data\result\result_blocks_polygons_layer"
}

# Output directories
OUTPUT_DIRECTORIES = [
    "Service_Area_Stations",
    "Service_Area_Tourist_Sites",
    "Service_Area_Educational_Sites",
    "Company_Density",
    "APH_Sales_TOSH"
]