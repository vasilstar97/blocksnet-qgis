import json
import os
from pathlib import Path
import tempfile

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFile,
    QgsProcessingParameterEnum,
    QgsProcessingParameterVectorDestination,
    QgsProcessingException,
)

from ..base import AnalysisAlgorithm
from ....environment import Config, run_command


WORKER_SCRIPT = "worker.py"
SERVICE_TYPES_FILE = "service_types.json"


def load_service_types():
    config_path = Path(__file__).with_name(SERVICE_TYPES_FILE)

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            service_types = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise QgsProcessingException(
            f"Could not load service types from {config_path}: {exc}"
        )

    if not isinstance(service_types, list) or not service_types:
        raise QgsProcessingException(
            f"Service types configuration is empty or invalid: {config_path}"
        )

    for item in service_types:
        if not all(
            key in item
            for key in ("name", "name_ru", "demand", "accessibility")
        ):
            raise QgsProcessingException(
                f"Invalid service type entry in {config_path}: {item}"
            )

    return service_types


class ProvisionAlgorithm(AnalysisAlgorithm):

    BLOCKS = "BLOCKS"
    MATRIX = "MATRIX"
    SERVICE_TYPE = "SERVICE_TYPE"
    OUTPUT = "OUTPUT"

    def name(self):
        return "competitive_provision"

    def displayName(self):
        return "2. Competitive provision"

    def shortHelpString(self):
        return (
            "Calculates competitive provision of services "
            "for urban blocks."
        )

    def createInstance(self):
        return ProvisionAlgorithm()

    def initAlgorithm(self, config=None):
        self.service_types = load_service_types()

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
            QgsProcessingParameterEnum(
                self.SERVICE_TYPE,
                "Service type",
                options=[
                    item["name_ru"]
                    for item in self.service_types
                ],
                defaultValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                "Blocks with competitive provision",
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

        service_type_index = self.parameterAsEnum(
            parameters,
            self.SERVICE_TYPE,
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

        if not matrix_path or not os.path.isfile(matrix_path):
            raise QgsProcessingException(
                "Accessibility matrix was not found."
            )

        if not 0 <= service_type_index < len(self.service_types):
            raise QgsProcessingException(
                "Invalid service type selected."
            )

        if not output_path:
            raise QgsProcessingException(
                "Output path was not specified."
            )

        service_type = self.service_types[service_type_index]

        service_name = service_type["name"]
        demand = service_type["demand"]
        accessibility = service_type["accessibility"]

        output_path = str(
            Path(output_path).expanduser().resolve()
        )

        feedback.pushInfo(
            f"Service type: {service_type['name_ru']} ({service_name})"
        )
        feedback.pushInfo(f"Demand: {demand}")
        feedback.pushInfo(f"Accessibility: {accessibility}")

        with tempfile.TemporaryDirectory(
            prefix="blocksnet_provision_"
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
                "--service-type",
                str(service_name),
                "--demand",
                str(demand),
                "--accessibility",
                str(accessibility),
                "--output",
                output_path,
            ]

            feedback.pushInfo(
                "Calculating competitive provision..."
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