import os
from pathlib import Path
import tempfile
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterVectorDestination,
    QgsProcessingException
)
from ..base import PreprocessingAlgorithm
from ....environment import Config, run_command

WORKER_SCRIPT = 'worker.py'

class ObjectsAggregationAlgorithm(PreprocessingAlgorithm):

    BLOCKS = "BLOCKS"
    OBJECTS = "OBJECTS"
    OUTPUT = "OUTPUT"

    def name(self):
        return "aggregate_objects"

    def displayName(self):
        return "2. Aggregate objects"

    def shortHelpString(self):
        return "Aggregates parameters of objects within blocks"

    def createInstance(self):
        return ObjectsAggregationAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.BLOCKS,
                "Urban blocks (containers)",
                types=[QgsProcessing.TypeVectorPolygon],
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.OBJECTS,
                "Objects to aggregate",
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                "Output urban blocks",
                QgsProcessing.SourceType.TypeVectorPolygon,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        blocks_layer = self.parameterAsVectorLayer(
            parameters, self.BLOCKS, context
        )
        objects_layer = self.parameterAsVectorLayer(
            parameters, self.OBJECTS, context
        )
        output_path = self.parameterAsOutputLayer(
            parameters, self.OUTPUT, context
        )

        # if not blocks_layer or not objects_layer:
        #     raise QgsProcessingException(
        #         "Could not load input layers."
        #     )

        # if blocks_layer.crs() != objects_layer.crs():
        #     raise QgsProcessingException(
        #         "Input layers must have the same CRS."
        #     )

        # if blocks_layer.crs().isGeographic():
        #     feedback.pushWarning(
        #         "Input layers use a geographic CRS. "
        #         "Metric calculations may be inaccurate."
        #     )

        with tempfile.TemporaryDirectory(
            prefix="blocksnet_aggregation_"
        ) as temp_dir:
            temp_dir = Path(temp_dir)

            blocks_path = temp_dir / "blocks.gpkg"
            objects_path = temp_dir / "objects.gpkg"

            self._export_layer(
                blocks_layer, blocks_path, context
            )
            self._export_layer(
                objects_layer, objects_path, context
            )

            worker_script = Path(__file__).with_name(
                WORKER_SCRIPT
            )

            command = [
                Config.get_environment(),
                str(worker_script),
                "--blocks", str(blocks_path),
                "--objects", str(objects_path),
                "--output", str(output_path),
            ]

            feedback.pushInfo(
                "Running BlocksNet in the external Python environment..."
            )

            run_command(command, feedback=feedback)

        if not os.path.exists(output_path):
            raise QgsProcessingException(
                f"Output file was not created: {output_path}"
            )

        return {self.OUTPUT: output_path}