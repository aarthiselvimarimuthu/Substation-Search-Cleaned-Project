# Automated Substation Identification Near Parcel Polygons Using QGIS and PyQGIS

## Project Overview

This project demonstrates an automated geospatial workflow for identifying electrical substations located within or near selected land parcel polygons.

The workflow combines QGIS, PyQGIS, spatial analysis, coordinate reference system transformations, geometry buffering, spatial indexing, and OpenStreetMap data retrieval to identify potential substations within a configurable proximity of parcel boundaries.

The objective is to reduce manual GIS processing and streamline the preliminary screening of land parcels for infrastructure and renewable energy development.

## Problem Statement

Identifying nearby electrical infrastructure for large sets of land parcels can involve repetitive GIS operations, including coordinate transformation, buffering, downloading infrastructure data, and spatial filtering.

Performing these steps manually for multiple parcels or study areas can be time-consuming and difficult to scale.

This project automates the process using Python and QGIS geospatial processing tools.

## Objectives

- Automate the identification of nearby electrical substations.
- Retrieve substation information from OpenStreetMap.
- Process parcel polygons using coordinate reference system transformations.
- Generate configurable parcel buffer zones.
- Perform spatial intersection analysis.
- Export identified substation locations into GIS-compatible formats.
- Reduce repetitive manual GIS processing.

## Workflow

### 1. Input Data Preparation

The workflow uses two primary spatial inputs:

- Parcel polygons representing the land areas of interest.
- Study-area boundary defining the region for the infrastructure search.

These layers are loaded into QGIS before executing the automation script.

### 2. Coordinate Reference System Transformation

Parcel geometries are transformed into EPSG:4326 (WGS 84) for geographic processing and compatibility with OpenStreetMap data.

The geometries are subsequently transformed into EPSG:3857 to perform buffer operations using a distance expressed in metres.

### 3. Parcel Buffer Generation

A configurable buffer is generated around the parcel polygons.

The default buffer distance is 150 metres, which can be modified depending on the screening requirements.

The buffer geometries are transformed back to EPSG:4326 for spatial comparison with the retrieved OpenStreetMap infrastructure.

### 4. OpenStreetMap Data Retrieval

The workflow queries the OpenStreetMap Overpass API to retrieve electrical substations tagged with:

`power=substation`

The query includes:

- OSM nodes
- OSM ways
- OSM relations

The data is retrieved within the bounding box of the selected study boundary.

### 5. Spatial Indexing and Filtering

A spatial index is created for the buffered parcel polygons to improve candidate feature searching.

The retrieved substation geometries are checked against parcel buffer geometries using spatial intersection operations.

Substations intersecting the configured parcel buffer are selected as potential nearby infrastructure locations.

### 6. Output Generation

The filtered substation features are exported to a GeoPackage file.

The output contains available OpenStreetMap attributes, including:

- OSM feature type
- OSM ID
- Substation name
- Operator
- Voltage information
- Substation classification

The final output layer can be loaded directly into QGIS for further analysis, visualization, and validation.

## Technologies Used

- Python
- QGIS
- PyQGIS
- QGIS Processing Framework
- OpenStreetMap
- Overpass API
- GeoPackage
- Spatial Indexing
- Geometry Intersection
- Coordinate Reference Systems
- Geospatial Data Automation

## Key GIS Concepts

- Vector data processing
- Coordinate transformation
- Geometry buffering
- Bounding box extraction
- Spatial indexing
- Spatial intersection
- Infrastructure mapping
- Proximity-based analysis
- Automated geospatial workflows

## Applications

This workflow can support preliminary geospatial screening for:

- Renewable energy development
- Solar project site assessment
- Land parcel evaluation
- Electrical infrastructure mapping
- Infrastructure proximity analysis
- GIS-based site screening
- Spatial planning workflows

## Limitations

This project identifies mapped substations based on OpenStreetMap data and geometric proximity.

The presence of a nearby substation does not confirm available grid capacity, connection feasibility, accessibility, ownership, voltage suitability, or technical suitability for a project.

The results should be treated as preliminary screening information and independently validated using authoritative utility data and engineering assessments.

## Future Improvements

Potential future developments include:

- Distance calculation between parcel boundaries and substations.
- Automated ranking of candidate substations.
- Support for multiple parcel input datasets.
- Improved CRS selection based on geography.
- Automated report generation.
- Map export and visualization.
- Error handling and retry logic for API requests.
- Deduplication of retrieved infrastructure.
- Interactive parameter configuration.
- Integration with QGIS Processing Toolbox.

## Conclusion

This project showcases the use of Python-based GIS automation to streamline infrastructure identification and spatial screening.

By combining QGIS, PyQGIS, OpenStreetMap, and spatial analysis techniques, repetitive geospatial processing tasks can be automated, making the workflow more reusable, efficient, and adaptable to different study areas.

**Disclaimer:** This repository is an anonymized portfolio demonstration of GIS automation techniques. The results are not intended to replace official utility information, engineering studies, or grid-connection assessments.
