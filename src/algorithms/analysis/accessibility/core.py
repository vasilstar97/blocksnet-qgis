import os
from pathlib import Path
import tempfile

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFile,
    QgsProcessingParameterVectorDestination,
    QgsProcessingException,
)

from ..base import AnalysisAlgorithm
from ....environment import Config, run_command


WORKER_SCRIPT = "worker.py"


class AccessibilityAlgorithm(AnalysisAlgorithm):

    BLOCKS = "BLOCKS"
    MATRIX = "MATRIX"
    OUTPUT = "OUTPUT"

    def name(self):
        return "median_accessibility"

    def displayName(self):
        return "1. Median accessibility"

    def shortHelpString(self):
        return "Calculates median accessibility for urban blocks"

    def createInstance(self):
        return AccessibilityAlgorithm()

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
                self.MATRIX,
                "Accessibility matrix",
                fileFilter="Pickle files (*.pkl)",
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                "Blocks with accessibility",
                QgsProcessing.SourceType.TypeVectorPolygon,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        blocks_layer = self.parameterAsVectorLayer(
            parameters,
            self.BLOCKS,
            context,
        )

        matrix_path = self.parameterAsFile(
            parameters,
            self.MATRIX,
            context,
        )

        output_path = self.parameterAsOutputLayer(
            parameters,
            self.OUTPUT,
            context,
        )

        if not blocks_layer or not blocks_layer.isValid():
            raise QgsProcessingException(
                "Could not load urban blocks layer."
            )

        if not matrix_path:
            raise QgsProcessingException(
                "Accessibility matrix was not specified."
            )

        if not output_path:
            raise QgsProcessingException(
                "Output path was not specified."
            )

        output_path = str(
            Path(output_path).expanduser().resolve()
        )

        with tempfile.TemporaryDirectory(
            prefix="blocksnet_median_"
        ) as temp_dir:

            blocks_path = Path(temp_dir) / "blocks.gpkg"

            self._export_layer(
                blocks_layer,
                blocks_path,
                context,
            )

            worker_script = Path(__file__).with_name(
                WORKER_SCRIPT
            )

            command = [
                Config.get_environment(),
                str(worker_script),
                "--blocks",
                str(blocks_path),
                "--matrix",
                str(matrix_path),
                "--output",
                output_path,
            ]

            feedback.pushInfo(
                "Calculating median accessibility..."
            )

            run_command(
                command,
                feedback=feedback,
            )

        if not os.path.exists(output_path):
            raise QgsProcessingException(
                f"Output file was not created: {output_path}"
            )

        feedback.pushInfo(
            f"Output created: {output_path}"
        )

        return {
            self.OUTPUT: output_path,
        }