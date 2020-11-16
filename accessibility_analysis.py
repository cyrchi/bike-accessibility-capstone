"""
Author: Cyrus Chimento
Date: 11/1/2020

Purpose: I created this script to run an the analysis central to my capstone
         project for a MSc. in GIS at the University of Maryland. The script
         accepts origin points, destination points, and a property parcel
         layer, and loops through six scenarios (comprising different network
         network datasets) where it conducts an OD-Cost Matrix network
         analysis, counts the number of destinations reachable from each
         origin on the network dataset, and adds this count as an attribute on
         the parcel layer.

References:

1. https://pro.arcgis.com/en/pro-app/tool-reference/network-analyst/make-od-cost-matrix-analysis-layer.htm
2. https://desktop.arcgis.com/en/arcmap/10.3/tools/network-analyst-toolbox/add-locations.htm
3. https://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/using-tools-in-python.htm
4. https://desktop.arcgis.com/en/arcmap/10.3/tools/data-management-toolbox/select-layer-by-attribute.htm
5. https://desktop.arcgis.com/en/arcmap/10.3/tools/data-management-toolbox/copy-features.htm
6. https://desktop.arcgis.com/en/arcmap/10.3/tools/analysis-toolbox/frequency.htm
7. https://desktop.arcgis.com/en/arcmap/10.3/tools/data-management-toolbox/add-join.htm
8. https://desktop.arcgis.com/en/arcmap/10.3/tools/analysis-toolbox/spatial-join.htm
9. https://desktop.arcgis.com/en/arcmap/10.3/tools/data-management-toolbox/make-feature-layer.htm
10. https://pro.arcgis.com/en/pro-app/arcpy/get-started/error-handling-with-python.htm
11. https://www.geeksforgeeks.org/python-program-to-convert-seconds-into-hours-minutes-and-seconds/

"""

# import modules
import arcpy
import sys
import time

print("Imported modules.")

start_time = time.time() # timestamp

# set environmental variables
work = r"C:\Users\cyrus\Desktop\GIS\UMD\GEOG797_ProfessionalCapstoneProject\Data\LTS_network_clean.gdb"
arcpy.env.workspace = work
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Network")

# initialize loop variables
scenario_list = ["Inequality_Full_Road_", "Inequality_Tier_0_", "Inequality_Tier_1_", "Inequality_Tier_2_", "Inequality_Tier_3_", "Inequality_Tier_4_"]
network_list = ["MontgomeryCounty_LTS", "Tier_0_LTS","Tier_1_LTS","Tier_2_LTS","Tier_3_LTS","Tier_4_LTS"] 
counter = 0

try:

    for scenario in scenario_list: # loop through the scenario list

        # variables
        inNetworkDataset = network_list[counter] + "\\" + network_list[counter] + "_ND"
        outNALayerName = scenario + "network_matrix"
        outLayerFile = r"C:\Users\cyrus\Desktop\GIS\UMD\GEOG797_ProfessionalCapstoneProject\Data\Output" + "\\" + outNALayerName + ".lyr"
        searchTolerance = "1000 Meters" # for the Add Locations tool

        parcel_points = r"Parcel_Points_Inequality_Subset" # origins
        business_points = r"MontgomeryCounty_Business_Listings" # destinations
        RideOn_points = r"MontgomeryCounty_RideOn_Stops" # destinations
        WMATA_points = r"MontgomeryCounty_WMATA_Stops" # destinations
        school_points = r"MCPS_Facilities" # destinations

        # parcel_points = r"Residential_Parcel_Points_Subset" # origins: subset
        # business_points = r"MontgomeryCounty_BusinessListings_Subset" # destinations: subset
        # RideOn_points = r"MontgomeryCounty_RideOn_Stops_Subset" # destinations: subset

        parcel_lyr = arcpy.MakeFeatureLayer_management("Parcels_Inequality_Subset", "parcel_lyr") # residential parcels

        # parcel_lyr = arcpy.MakeFeatureLayer_management("Residential_Parcels_Subset", "parcel_lyr") # subset


        # define OD Cost Matrix analysis settings
        impedanceAttribute = "Miles" # optimize based on distance
        out_lines = "NO_LINES" # don't output line shapes (output Lines will still list travel times)
        cutoff = 2.0 # don't accept destinations farther than 2 miles

        # make OD Cost Matrix Layer
        outODResultObject = arcpy.na.MakeODCostMatrixAnalysisLayer(
            inNetworkDataset,
            outNALayerName,
            "",
            cutoff,
            "",
            "",
            "",
            out_lines,
            impedanceAttribute,
            )

        print("OD Cost Matrix Layer created: %s."%outNALayerName)

        # get the layer object from the result object. The OD layer can now be referenced using the layer object
        outNALayer = outODResultObject.getOutput(0)

        # get the names of all the sublayers within the OD cost matrix layer
        subLayerNames = arcpy.na.GetNAClassNames(outNALayer)

        # stores the layer names for use later
        originsLayerName = subLayerNames["Origins"]
        destinationsLayerName = subLayerNames["Destinations"]

        # load the parcel points as origins using a default field mappings and a search tolerance of 1000 Meters
        arcpy.na.AddLocations(outNALayer, originsLayerName, parcel_points, search_tolerance = searchTolerance)

        print("Origins added.")

        # load the destinations using a default field mappings and a search tolerance of 1000 Meters
        arcpy.na.AddLocations(outNALayer, destinationsLayerName, business_points, search_tolerance = searchTolerance) # business listings
        arcpy.na.AddLocations(outNALayer, destinationsLayerName, RideOn_points, search_tolerance = searchTolerance) # RideOn stations
        arcpy.na.AddLocations(outNALayer, destinationsLayerName, WMATA_points, search_tolerance = searchTolerance) # WMATA stations
        arcpy.na.AddLocations(outNALayer, destinationsLayerName, school_points, search_tolerance = searchTolerance) # public high schools

        print("Destinations added.")

        #Solve the OD cost matrix layer
        arcpy.na.Solve(outNALayer)

        print("OD Cost Matrix solved.")

        # get sublayers
        # listLayers returns a list of sublayer layer objects contained in the NA
        # group layer, filtered by layer name used as a wildcard. Use the sublayer
        # name from GetNAClassNames as the wildcard string in case the sublayers
        # have non-default names.
        OriginsSubLayer = outNALayer.listLayers(originsLayerName)[0]
        DestinationsSubLayer = outNALayer.listLayers(destinationsLayerName)[0]
        LinesSubLayer = outNALayer.listLayers(subLayerNames["ODLines"])[0]
        
        # select lines by attribute
        arcpy.SelectLayerByAttribute_management (LinesSubLayer, "NEW_SELECTION", '"Total_Miles" <= 2')

        # write selected line features from the NA sublayer to a new feature class
        arcpy.CopyFeatures_management(LinesSubLayer, scenario + "lines_lt2mi")
        # write origin features from the NA sublayer to a new feature class
        arcpy.CopyFeatures_management(OriginsSubLayer, scenario + "origins")

        # calculate frequency of destinations reached by each origin point
        arcpy.Frequency_analysis(scenario + "lines_lt2mi", scenario + "lt2mi_FREQUENCY", "OriginID", "DestinationID")

        print("Frequency table calculated.")

        # join the frequency field back to the origin points
        arcpy.management.JoinField(scenario + "origins", "OBJECTID", scenario + "lt2mi_FREQUENCY", "OriginID", "FREQUENCY")

##        # for the spatial join, create a new fieldmappings object and add the two input feature classes
##        fieldmappings = arcpy.FieldMappings()
##        fieldmappings.addTable(parcel_lyr)
##        fieldmappings.addTable(scenario + "origins")
##         
##        # first get the FREQUENCY fieldmap, just joined to the origins layer.
##        # setting the field's merge rule to mean will aggregate the multiple FREQUENCY values in a parcel into
##        # an average value. The field is also renamed to be more appropriate for the output
##        Frequency_FieldIndex = fieldmappings.findFieldMapIndex("FREQUENCY")
##        fieldmap = fieldmappings.getFieldMap(Frequency_FieldIndex)
##         
##        # Get the output field's properties as a field object
##        field = fieldmap.outputField
##         
##        # Rename the field and pass the updated field object back into the field map
##        field.name = "NUM_DEST"
##        field.aliasName = scenario + "dest"
##        fieldmap.outputField = field
##         
##        # Set the merge rule to mean and then replace the old fieldmap in the mappings object with the updated one
##        fieldmap.mergeRule = "mean"
##        fieldmappings.replaceFieldMap(Frequency_FieldIndex, fieldmap)

        # spatial join the frequency field on the origin points to the parcel polygons
        arcpy.SpatialJoin_analysis(
            parcel_lyr,
            scenario + "origins",
            scenario + "Accessibility",
            "JOIN_ONE_TO_ONE",
            "KEEP_ALL",
            )

        print("Spatial Join complete.")

##        if scenario == "Full_Road_":
##            pass
##        else:
##            # join the full road network accessibility field to each subsequent accessibility scenario
##            arcpy.management.JoinField(scenario + "Accessibility", "OBJECTID_1", "Full_Road_Accessibility", "OBJECTID_1", "Full_Road_dest")
##            print("Full Road Accessibility joined to feature class.")
        
        print("%s Network Analysis complete."%scenario)
        counter += 1 # iterate the counter

    
    end_time = time.time() # timestamp
    analysis_time = end_time - start_time # calculate the total analysis time

    # function to convert seconds to hours, minutes, seconds
    def convert(seconds): 
        seconds = seconds % (24 * 3600) 
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
          
        return "Duration: %d hours %02d minutes %02d seconds" % (hour, minutes, seconds)

    print(convert(analysis_time))

except Exception:
    e = sys.exc_info()[1]
    print(e.args[0])

    # If using this code within a script tool, AddError can be used to return messages 
    #   back to a script tool. If not, AddError will have no effect.
    arcpy.AddError(e.args[0])
