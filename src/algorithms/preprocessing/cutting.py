import os
from pathlib import Path
import tempfile
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterVectorDestination,
    QgsProcessingException
)
from .base import PreprocessingAlgorithm
from ...config import Config
from ..environment import run_command

class BlocksCuttingAlgorithm(PreprocessingAlgorithm):

    BOUNDARIES = "BOUNDARIES"
    ROADS = "ROADS"
    RAILWAYS = "RAILWAYS"
    WATER = "WATER"
    OUTPUT = "OUTPUT"

    def name(self):
        return "cut_blocks"

    def displayName(self):
        return "1. Cut blocks"

    def shortHelpString(self):
        return "Cuts urban blocks using various spatial layers"

    def createInstance(self):
        return BlocksCuttingAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.BOUNDARIES,
                "City boundaries polygon",
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.ROADS,
                "City roads lines",
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.RAILWAYS,
                "Railways lines (optional)",
                types=[QgsProcessing.TypeVectorLine],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.WATER,
                "Water objects (optional)",
                types=[QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorLine],
                optional=True
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
        # 1. Получаем входные слои.
        boundaries = self.parameterAsVectorLayer(
            parameters, self.BOUNDARIES, context
        )
        roads = self.parameterAsVectorLayer(
            parameters, self.ROADS, context
        )
        railways = self.parameterAsVectorLayer(
            parameters, self.RAILWAYS, context
        )
        water = self.parameterAsVectorLayer(
            parameters, self.WATER, context
        )

        # 2. Проверяем обязательные слои.
        for name, layer in (
            ("City boundaries", boundaries),
            ("Roads", roads),
        ):
            if layer is None or not layer.isValid():
                raise QgsProcessingException(
                    f"A valid '{name}' layer is required."
                )

        # 3. Проверяем CRS, но не перепроецируем данные.
        layers = {
            "City boundaries": boundaries,
            "Roads": roads,
            "Railways": railways,
            "Water": water,
        }

        for name, layer in layers.items():
            if layer is None:
                continue

            if not layer.crs().isValid():
                raise QgsProcessingException(
                    f"Layer '{name}' has no valid CRS."
                )

        reference_crs = boundaries.crs()

        for name, layer in layers.items():
            if layer is not None and layer.crs() != reference_crs:
                raise QgsProcessingException(
                    f"Layer '{name}' uses CRS "
                    f"{layer.crs().authid()}, but boundaries use "
                    f"{reference_crs.authid()}. "
                    "Reproject the input layers to a common CRS first."
                )

        if reference_crs.isGeographic():
            feedback.pushWarning(
                "The input CRS is geographic. Make sure it is suitable "
                "for BlocksNet's spatial operations; a projected CRS "
                "is generally preferable."
            )

        # 4. Получаем Python из окружения BlocksNet.
        python_exe = Config.get_environment()

        # 5. Определяем внешний скрипт.
        worker_script = Path(__file__).with_name(
            "cutting_worker.py"
        )

        # 6. Экспортируем входы во временные GeoPackage
        # и запускаем отдельный Python.
        output_path = self.parameterAsOutputLayer(
            parameters, self.OUTPUT, context
        )

        if not output_path:
            raise QgsProcessingException(
                "Output path was not specified."
            )

        output_path = str(Path(output_path).expanduser().resolve())

        with tempfile.TemporaryDirectory(
            prefix="blocksnet_cut_"
        ) as temp_dir:
            temp_dir = Path(temp_dir)

            boundaries_path = temp_dir / "boundaries.gpkg"
            roads_path = temp_dir / "roads.gpkg"

            self._export_layer(
                boundaries, boundaries_path, context
            )
            self._export_layer(
                roads, roads_path, context
            )

            command = [
                python_exe,
                str(worker_script),
                "--boundaries", str(boundaries_path),
                "--roads", str(roads_path),
                "--output", output_path,
            ]

            if railways is not None:
                railways_path = temp_dir / "railways.gpkg"
                self._export_layer(
                    railways, railways_path, context
                )
                command.extend([
                    "--railways", str(railways_path)
                ])

            if water is not None:
                water_path = temp_dir / "water.gpkg"
                self._export_layer(
                    water, water_path, context
                )
                command.extend([
                    "--water", str(water_path)
                ])

            feedback.pushInfo(
                "Running BlocksNet in the external Python environment..."
            )

            run_command(command, feedback=feedback)

        # 7. Проверяем, что внешний скрипт действительно создал результат.
        if not os.path.isfile(output_path):
            raise QgsProcessingException(
                "BlocksNet finished, but the output GeoPackage "
                "was not created."
            )

        feedback.pushInfo(f"Output created: {output_path}")

        return {
            self.OUTPUT: output_path,
        }