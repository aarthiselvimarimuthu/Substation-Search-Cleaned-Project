"""Identify OpenStreetMap substations near parcel polygons using QGIS / PyQGIS.

Run inside the QGIS Python environment with the required input layers loaded.
"""
from qgis.core import (
    QgsProject, QgsVectorFileWriter, QgsCoordinateReferenceSystem,
    QgsVectorLayer, QgsCoordinateTransform, QgsSpatialIndex,
    QgsFeatureRequest, QgsWkbTypes, QgsFeature, QgsGeometry, QgsPointXY,
)
import processing
import os
import json
from urllib import request, parse
from datetime import datetime



# -------------------- USER CONFIGURATION --------------------
OUTPUT_ROOT = r"C:/GIS/Substation_Search"  # Change to your preferred output folder
PARCEL_LAYER_NAME = "parcels"             # Name of parcel layer loaded in QGIS
BOUNDARY_LAYER_NAME = "study_boundary"     # Name of boundary layer loaded in QGIS
BUFFER_DISTANCE_METERS = 150


# --------------------------------------------------------
TEMP_DIR = os.path.join(OUTPUT_ROOT, "temp")
OUTPUT_DIR = os.path.join(OUTPUT_ROOT, "output")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

CRS_WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")
CRS_BUFFER = QgsCoordinateReferenceSystem("EPSG:3857")



def get_layer_by_name(name):
    matches = QgsProject.instance().mapLayersByName(name)
    if not matches:
        raise RuntimeError(f"Required QGIS layer not found: {name}")
    return matches[0]



def bbox_wgs84(layer):
    extent = layer.extent()
    transform = QgsCoordinateTransform(layer.crs(), CRS_WGS84, QgsProject.instance())
    lower = transform.transform(extent.xMinimum(), extent.yMinimum())
    upper = transform.transform(extent.xMaximum(), extent.yMaximum())
    return lower.y(), lower.x(), upper.y(), upper.x()  # south, west, north, east



def query_osm_substations(south, west, north, east):
    """Query OSM Overpass for substation nodes, ways and relations in the bbox."""
    endpoint = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:60];
    (
      node[\"power\"=\"substation\"]({south},{west},{north},{east});
      way[\"power\"=\"substation\"]({south},{west},{north},{east});
      relation[\"power\"=\"substation\"]({south},{west},{north},{east});
    );
    out center tags;
    """
    payload = parse.urlencode({"data": query}).encode("utf-8")
    with request.urlopen(endpoint, data=payload, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))



def osm_json_to_point_layer(osm_data, layer_name="osm_substations"):
    layer = QgsVectorLayer(
        "Point?crs=EPSG:4326&field=osm_type:string&field=osm_id:long&field=name:string&field=operator:string&field=voltage:string&field=substation:string",
        layer_name, "memory"
    )
    provider = layer.dataProvider()
    for element in osm_data.get("elements", []):
        kind = element.get("type")
        tags = element.get("tags", {})
        if kind == "node":
            lon, lat = element["lon"], element["lat"]
        elif "center" in element:
            lon, lat = element["center"]["lon"], element["center"]["lat"]
        else:
            continue
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        feature.setAttributes([
            kind, element.get("id"), tags.get("name", ""), tags.get("operator", ""),
            tags.get("voltage", ""), tags.get("substation", "")
        ])
        provider.addFeature(feature)
    layer.updateExtents()
    return layer



def save_vector(layer, path, driver="ESRI Shapefile"):
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = driver
    options.fileEncoding = "UTF-8"
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, path, QgsProject.instance().transformContext(), options
    )
    if result[0] != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"Failed to write output: {path} | {result}")



def main():
    project = QgsProject.instance()
    parcels = get_layer_by_name(PARCEL_LAYER_NAME)
    boundary = get_layer_by_name(BOUNDARY_LAYER_NAME)


    # 1. Reproject parcel data to geographic CRS.
    parcels_wgs84_path = os.path.join(TEMP_DIR, f"parcels_wgs84_{timestamp}.gpkg")
    processing.run("native:reprojectlayer", {
        "INPUT": parcels, "TARGET_CRS": CRS_WGS84, "OUTPUT": parcels_wgs84_path
    })
    parcels_wgs84 = QgsVectorLayer(parcels_wgs84_path, "parcels_wgs84", "ogr")
    if not parcels_wgs84.isValid():
        raise RuntimeError("Could not load reprojected parcel layer")

    # 2. Reproject parcels to a meter-based CRS, create buffer, then return to WGS84.
    parcels_metric_path = os.path.join(TEMP_DIR, f"parcels_metric_{timestamp}.gpkg")
    buffer_metric_path = os.path.join(TEMP_DIR, f"parcel_buffer_metric_{timestamp}.gpkg")
    buffer_wgs84_path = os.path.join(TEMP_DIR, f"parcel_buffer_wgs84_{timestamp}.gpkg")
    processing.run("native:reprojectlayer", {
        "INPUT": parcels_wgs84, "TARGET_CRS": CRS_BUFFER, "OUTPUT": parcels_metric_path
    })
    processing.run("native:buffer", {
        "INPUT": parcels_metric_path, "DISTANCE": BUFFER_DISTANCE_METERS,
        "SEGMENTS": 10, "DISSOLVE": False, "OUTPUT": buffer_metric_path
    })
    processing.run("native:reprojectlayer", {
        "INPUT": buffer_metric_path, "TARGET_CRS": CRS_WGS84, "OUTPUT": buffer_wgs84_path
    })
    buffer_layer = QgsVectorLayer(buffer_wgs84_path, "parcel_buffer_wgs84", "ogr")
    if not buffer_layer.isValid():
        raise RuntimeError("Buffer layer creation failed")

    # 3. Fetch substation features from OpenStreetMap for the study boundary extent.
    south, west, north, east = bbox_wgs84(boundary)
    osm_data = query_osm_substations(south, west, north, east)
    osm_layer = osm_json_to_point_layer(osm_data)
    osm_path = os.path.join(TEMP_DIR, f"osm_substations_{timestamp}.gpkg")
    save_vector(osm_layer, osm_path, "GPKG")
    osm_layer = QgsVectorLayer(osm_path, "osm_substations", "ogr")
    if not osm_layer.isValid():
        raise RuntimeError("Could not load downloaded OSM substation layer")

    # 4. Spatially filter OSM substations intersecting parcel buffers.
    spatial_index = QgsSpatialIndex(buffer_layer.getFeatures())
    selected = []
    for feature in osm_layer.getFeatures():
        geom = feature.geometry()
        if not geom or geom.isEmpty():
            continue
        candidate_ids = spatial_index.intersects(geom.boundingBox())
        candidates = buffer_layer.getFeatures(QgsFeatureRequest().setFilterFids(candidate_ids))
        if any(candidate.geometry().intersects(geom) for candidate in candidates):
            selected.append(feature)

    # 5. Save filtered results and add the result to the current QGIS project.
    output_path = os.path.join(OUTPUT_DIR, f"substations_near_parcels_{timestamp}.gpkg")
    result_layer = QgsVectorLayer(
        f"Point?crs=EPSG:4326&field=osm_type:string&field=osm_id:long&field=name:string&field=operator:string&field=voltage:string&field=substation:string",
        "substations_near_parcels", "memory"
    )
    result_layer.dataProvider().addFeatures(selected)
    result_layer.updateExtents()
    save_vector(result_layer, output_path, "GPKG")
    saved_layer = QgsVectorLayer(output_path, "substations_near_parcels", "ogr")
    if saved_layer.isValid():
        project.addMapLayer(saved_layer)
        print(f"Done: {len(selected)} candidate substations saved to {output_path}")
    else:
        raise RuntimeError("Output file was saved but could not be loaded into QGIS")



if __name__ == "__main__":
    main()

