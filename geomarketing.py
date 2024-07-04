# geomarketing.py

import arcpy
from arcpy import env
from arcpy.na import *
from arcpy.sa import *
import numpy as np
import os

class GeoMarketing:
    def __init__(self, workspace, network_dataset):
        self.workspace = workspace
        self.network_dataset = network_dataset
        env.workspace = workspace
        env.overwriteOutput = True

    def calculate_service_area(self, layer_name, impedance, facilities, output_shapefile, travel_from=True):
        try:
            result_object = arcpy.na.MakeServiceAreaLayer(self.network_dataset, layer_name,
                                                          impedance, "TRAVEL_FROM" if travel_from else "TRAVEL_TO",
                                                          "300 600 900 1200 1500", "SIMPLE_POLYS", "MERGE", "RINGS")
            layer_object = result_object.getOutput(0)
            sublayer_names = arcpy.na.GetNAClassNames(layer_object)
            facilities_layer_name = sublayer_names["Facilities"]
            arcpy.na.AddLocations(layer_object, facilities_layer_name, facilities, "", "")
            arcpy.na.Solve(layer_object)

            polygons_layer_name = sublayer_names["SAPolygons"]
            arcpy.management.CopyFeatures(layer_object.listLayers(polygons_layer_name)[0], output_shapefile)

            field_names = [f.name for f in arcpy.ListFields(output_shapefile)]

            if "W_Value" not in field_names:
                arcpy.management.AddField(output_shapefile, "W_Value", "SHORT")

            if "ToBreak" not in field_names:
                raise RuntimeError("The field 'ToBreak' does not exist in the layer.")

            to_break_values = []
            with arcpy.da.SearchCursor(output_shapefile, ["ToBreak"]) as cursor:
                for row in cursor:
                    to_break_values.append(row[0])

            quantiles = np.quantile(to_break_values, [0.2, 0.4, 0.6, 0.8])

            with arcpy.da.UpdateCursor(output_shapefile, ["ToBreak", "W_Value"]) as cursor:
                for row in cursor:
                    if row[0] <= quantiles[0]:
                        row[1] = 1
                    elif row[0] <= quantiles[1]:
                        row[1] = 2
                    elif row[0] <= quantiles[2]:
                        row[1] = 3
                    elif row[0] <= quantiles[3]:
                        row[1] = 4
                    else:
                        row[1] = 5
                    cursor.updateRow(row)

            return output_shapefile
        except Exception as e:
            import traceback, sys
            tb = sys.exc_info()[2]
            print(f"Error at line {tb.tb_lineno}")
            print(str(e))
            return None

    def calculate_company_density(self, input_points, output_raster, normalized_raster, reclassified_raster):
        arcpy.CheckOutExtension("Spatial")
        desc = arcpy.Describe(input_points)
        extent = desc.extent
        arcpy.env.extent = extent
        arcpy.env.overwriteOutput = True
        cell_size = 100
        search_radius = 1000

        kernel_density_result = KernelDensity(input_points, None, cell_size, search_radius, "SQUARE_MAP_UNITS")
        kernel_density_result.save(output_raster)

        density_array = arcpy.RasterToNumPyArray(kernel_density_result, nodata_to_value=np.nan)
        density_array_nonzero = density_array[np.isfinite(density_array) & (density_array > 0)]
        min_density = np.min(density_array_nonzero)
        max_density = np.max(density_array_nonzero)

        normalized_density_array = (density_array - min_density) / (max_density - min_density)
        normalized_density_array[density_array <= 0] = np.nan
        normalized_raster_obj = arcpy.NumPyArrayToRaster(normalized_density_array,
                                                         lower_left_corner=kernel_density_result.extent.lowerLeft,
                                                         x_cell_size=cell_size, y_cell_size=cell_size,
                                                         value_to_nodata=np.nan)
        normalized_raster_obj.save(normalized_raster)

        p20 = np.nanpercentile(normalized_density_array, 20)
        p40 = np.nanpercentile(normalized_density_array, 40)
        p60 = np.nanpercentile(normalized_density_array, 60)
        p80 = np.nanpercentile(normalized_density_array, 80)

        reclass_ranges = RemapRange([
            [0, p20, 1],
            [p20, p40, 2],
            [p40, p60, 3],
            [p60, p80, 4],
            [p80, 1, 5]
        ])
        no_zero_density = SetNull(normalized_raster_obj, normalized_raster_obj, "VALUE = 0")
        reclassified_result = Reclassify(no_zero_density, "VALUE", reclass_ranges, "NODATA")
        reclassified_result.save(reclassified_raster)

    def calculate_aph_sales(self, layers, output_shapefile):
        priorities = np.array([0.062, 0.192, 0.268, 0.388, 0.091])
        normalized = priorities / priorities.sum()

        classification_fields = ["c_station", "c_touristsite", "c_educationsite", "c_company", "class_tosh"]
        base_layer = layers[4]

        temp_layer = "in_memory/temp_base"
        arcpy.management.CopyFeatures(base_layer, temp_layer)

        for field in classification_fields:
            if not arcpy.ListFields(temp_layer, field):
                arcpy.management.AddField(temp_layer, field, "FLOAT" if field == "class_tosh" else "SHORT")

        for i, (layer, field) in enumerate(zip(layers[:3], classification_fields[:3])):
            joined_layer = arcpy.analysis.SpatialJoin(
                target_features=temp_layer,
                join_features=layer,
                join_type="KEEP_COMMON",
                match_option="INTERSECT"
            )

            join_values = {}
            with arcpy.da.SearchCursor(joined_layer, ["TARGET_FID", "W_Value"]) as cursor:
                join_values = {row[0]: row[1] for row in cursor}

            with arcpy.da.UpdateCursor(temp_layer, ["FID", field]) as cursor:
                for row in cursor:
                    if row[0] in join_values and join_values[row[0]] is not None and join_values[row[0]] != 0:
                        row[1] = join_values[row[0]]
                    else:
                        row[1] = 5
                    cursor.updateRow(row)

            arcpy.management.Delete(joined_layer)

        calculation_fields = ["Class", "c_company", "c_educationsite", "c_touristsite", "c_station"]
        with arcpy.da.UpdateCursor(temp_layer, calculation_fields + ["class_tosh"]) as cursor:
            for row in cursor:
                class_tosh = sum((row[i] if row[i] is not None else 5) * normalized[i] for i in range(len(calculation_fields)))
                row[len(calculation_fields)] = class_tosh
                cursor.updateRow(row)

        if temp_layer != output_shapefile:
            arcpy.management.CopyFeatures(temp_layer, output_shapefile)

    def generate_filtered_layer(self, input_polygons, input_points, output_path, field_to_keep):
        try:
            intersect_layer = "in_memory/intersect_layer"
            arcpy.analysis.Intersect([input_polygons, input_points], intersect_layer)

            oids_to_delete = [row[0] for row in arcpy.da.SearchCursor(intersect_layer, ["OID@"])]

            temp_output = "in_memory/temp_output"
            arcpy.management.CopyFeatures(input_polygons, temp_output)

            fields_to_delete = [field.name for field in arcpy.ListFields(temp_output) if field.name != field_to_keep and field.type not in ('OID', 'Geometry')]
            if fields_to_delete:
                arcpy.management.DeleteField(temp_output, fields_to_delete)

            with arcpy.da.UpdateCursor(temp_output, ["OID@"]) as cursor:
                for row in cursor:
                    if row[0] in oids_to_delete:
                        cursor.deleteRow()

            arcpy.management.CopyFeatures(temp_output, output_path)

            arcpy.management.AddField(output_path, "Class", "SHORT")
            values = [row[0] for row in arcpy.da.SearchCursor(output_path, [field_to_keep])]
            quantiles = np.quantile(values, [0.2, 0.4, 0.6, 0.8])

            with arcpy.da.UpdateCursor(output_path, [field_to_keep, "Class"]) as cursor:
                for row in cursor:
                    if row[0] <= quantiles[0]:
                        row[1] = 1
                    elif row[0] <= quantiles[1]:
                        row[1] = 2
                    elif row[0] <= quantiles[2]:
                        row[1] = 3
                    elif row[0] <= quantiles[3]:
                        row[1] = 4
                    else:
                        row[1] = 5
                    cursor.updateRow(row)

        except Exception as e:
            import traceback, sys
            tb = sys.exc_info()[2]
            print(f"Error at line {tb.tb_lineno}")
            print(str(e))

    def invert_classes_raster(self, raster_path, output_raster_path):
        raster = Raster(raster_path)
        inv_raster = Con(raster == 1, 5, Con(raster == 2, 4, Con(raster == 3, 3, Con(raster == 4, 2, Con(raster == 5, 1)))))
        inv_raster.save(output_raster_path)

    def raster_to_polygons(self, raster_path, output_polygon_path):
        arcpy.conversion.RasterToPolygon(raster_path, output_polygon_path, "NO_SIMPLIFY", "VALUE")

    def update_inverted_company_field(self, result_blocks, raster_polygons):
        field_names = [f.name for f in arcpy.ListFields(result_blocks)]
        if "c_company" not in field_names:
            arcpy.management.AddField(result_blocks, "c_company", "SHORT", field_is_nullable="NULLABLE")

        join_output = "in_memory/join_output"
        arcpy.analysis.SpatialJoin(result_blocks, raster_polygons, join_output, "JOIN_ONE_TO_ONE", "KEEP_ALL", match_option="INTERSECT")

        c_company_values = {}
        with arcpy.da.SearchCursor(join_output, ["FID", "gridcode"]) as cursor:
            for row in cursor:
                fid = row[0]
                gridcode = row[1]
                c_company_values[fid] = gridcode

        with arcpy.da.UpdateCursor(result_blocks, ["FID", "c_company"]) as cursor:
            for row in cursor:
                fid = row[0]
                if fid in c_company_values and c_company_values[fid] is not None:
                    row[1] = c_company_values[fid]
                else:
                    row[1] = 5
                cursor.updateRow(row)

        arcpy.management.Delete(join_output)

    def change_class_order(self, layer_path, field_name):
        try:
            value_map = {1: 5, 5: 1}

            with arcpy.da.UpdateCursor(layer_path, [field_name]) as cursor:
                for row in cursor:
                    if row[0] in value_map:
                        row[0] = value_map[row[0]]
                    cursor.updateRow(row)

        except Exception as e:
            import traceback, sys
            tb = sys.exc_info()[2]
            print(f"Error at line {tb.tb_lineno}")
            print(str(e))
