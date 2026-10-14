import os
from pathlib import Path
import tempfile
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFileDestination,
    QgsProcessingException
)
from ..base import AccessibilityAlgorithm
from ....environment import Config, run_command

WORKER_SCRIPT = 'worker.py'

class GraphAlgorithm(AccessibilityAlgorithm):

    BLOCKS = "BLOCKS"
    MODE = "MODE"
    OUTPUT = "OUTPUT"

    def name(self):
        return "accessibility_graph"

    def displayName(self):
        return "1. Graph construction"

    def shortHelpString(self):
        return "Constructs graph using OpenStreetMap data"

    def createInstance(self):
        return GraphAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.BLOCKS,
                "Urban blocks or territory boundaries",
                types=[QgsProcessing.TypeVectorPolygon],
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.MODE,
                "Travel mode (graph type)",
                options=["intermodal", "walk", "drive"],
                defaultValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                "Accessibility matrix",
                fileFilter="Pickle files (*.pkl)",
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        blocks_layer = self.parameterAsVectorLayer(
            parameters, self.BLOCKS, context
        )
        mode_index = self.parameterAsEnum(
            parameters, self.MODE, context
        )
        output_path = self.parameterAsFileOutput(
            parameters, self.OUTPUT, context
        )

        if not blocks_layer:
            raise QgsProcessingException(
                "Could not load urban blocks layer."
            )

        modes = ["intermodal", "walk", "drive"]
        mode = modes[mode_index]

        with tempfile.TemporaryDirectory(
            prefix="blocksnet_graph_"
        ) as temp_dir:
            blocks_path = Path(temp_dir) / "blocks.gpkg"

            self._export_layer(
                blocks_layer, blocks_path, context
            )

            worker_script = Path(__file__).with_name(
                WORKER_SCRIPT
            )

            command = [
                Config.get_environment(),
                str(worker_script),
                "--blocks", str(blocks_path),
                "--mode", mode,
                "--output", str(output_path),
            ]

            feedback.pushInfo(
                "Building accessibility graph..."
            )
            run_command(command, feedback=feedback)

        if not os.path.exists(output_path):
            raise QgsProcessingException(
                f"Graph file was not created: {output_path}"
            )

        return {self.OUTPUT: output_path}