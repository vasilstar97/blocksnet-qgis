from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
)
from blocksnet.blocks.cutting import (
    preprocess_urban_objects,
    cut_urban_blocks,
)

class BlocksCuttingAlgorithm(QgsProcessingAlgorithm):
    BOUNDARIES="BOUNDARIES"
    ROADS="ROADS"
    RAILWAYS="RAILWAYS"
    WATER="WATER"
    OUTPUT="OUTPUT"

    def name(self):
        return "blockscutting"

    def displayName(self):
        return "Blocks cutting"

    def group(self):
        return "BlocksNet"

    def groupId(self):
        return "blocksnet"

    def shortHelpString(self):
        return (
            "Cut urban blocks using spatial layers"
        )

    def createInstance(self):
        return BlocksCuttingAlgorithm()

    def initAlgorithm(self, config=None):
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BOUNDARIES,
                "Boundaries",
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ROADS,
                "Roads",
                [QgsProcessing.TypeVectorLine],
            )
        )


        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.RAILWAYS,
                "Railways (optional)",
                [QgsProcessing.TypeVectorLine],
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.WATER,
                "Water (optional)",
                [QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorLine],
                optional=True,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        boundaries_src = self.parameterAsSource(
            parameters, self.BOUNDARIES, context
        )
        roads_src = self.parameterAsSource(
            parameters, self.ROADS, context
        )
        railways_src = self.parameterAsSource(
            parameters, self.RAILWAYS, context
        )
        water_src = self.parameterAsSource(
            parameters, self.WATER, context
        )

        if not boundaries_src or not roads_src:
            raise QgsProcessingException("Boundaries and roads are required.")

        boundaries_gdf = self._to_gdf(boundaries_src)
        roads_gdf = self._to_gdf(roads_src)
        railways_src = self._to_gdf(railways_src) if railways_src else None
        water_src = self._to_gdf(water_src) if water_src else None

        feedback.pushInfo("Preparing input layers...")

        output_crs = boundaries_gdf.crs
        processing_crs = boundaries_gdf.estimate_utm_crs()

        boundaries_gdf = boundaries_gdf.to_crs(processing_crs)
        roads_gdf = roads_gdf.to_crs(processing_crs)
        water_gdf = water_gdf.to_crs(processing_crs)

        if railways_gdf is not None:
            railways_gdf = railways_gdf.to_crs(processing_crs)

        if buildings_gdf is not None:
            buildings_gdf = buildings_gdf.to_crs(processing_crs)

        feedback.pushInfo("Preprocessing urban objects...")

        lines_gdf, polygons_gdf = preprocess_urban_objects(
            roads_gdf,
            railways_gdf,
            water_gdf,
        )

        feedback.pushInfo("Cutting urban blocks...")

        blocks_gdf = cut_urban_blocks(
            boundaries_gdf,
            lines_gdf,
            polygons_gdf,
        )
        blocks_gdf = blocks_gdf.to_crs(output_crs)