import os
from pathlib import Path
import tempfile

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingException,
)

from ..base import AccessibilityAlgorithm
from ....environment import Config, run_command


WORKER_SCRIPT = "worker.py"


class MatrixAlgorithm(AccessibilityAlgorithm):

    BLOCKS = "BLOCKS"
    GRAPH = "GRAPH"
    OUTPUT = "OUTPUT"

    def name(self):
        return "accessibility_matrix"

    def displayName(self):
        return "2. Calculate accessibility matrix"

    def shortHelpString(self):
        return "Calculates the accessibility matrix for urban blocks"

    def createInstance(self):
        return MatrixAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.BLOCKS,
                "Urban blocks",
                types=[QgsProcessing.TypeVectorPolygon],
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.GRAPH,
                "Accessibility graph (.pkl)",
                extension="pkl",
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
        graph_path = self.parameterAsFile(
            parameters, self.GRAPH, context
        )
        output_path = self.parameterAsFileOutput(
            parameters, self.OUTPUT, context
        )

        if not blocks_layer:
            raise QgsProcessingException(
                "Could not load urban blocks layer."
            )

        if not graph_path or not os.path.isfile(graph_path):
            raise QgsProcessingException(
                f"Graph file does not exist: {graph_path}"
            )

        with tempfile.TemporaryDirectory(
            prefix="blocksnet_matrix_"
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
                "--graph", str(graph_path),
                "--output", str(output_path),
            ]

            feedback.pushInfo(
                "Calculating accessibility matrix..."
            )
            run_command(command, feedback=feedback)

        if not os.path.exists(output_path):
            raise QgsProcessingException(
                f"Matrix file was not created: {output_path}"
            )

        return {self.OUTPUT: output_path}