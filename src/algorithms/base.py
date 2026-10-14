from abc import abstractmethod

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsVectorFileWriter,
)


class BaseAlgorithm(QgsProcessingAlgorithm):

    @abstractmethod
    def createInstance(self):
        pass

    @abstractmethod
    def group(self):
        pass

    @abstractmethod
    def groupId(self):
        pass    

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def displayName(self):
        pass

    @abstractmethod
    def shortHelpString(self):
        pass
    
    @abstractmethod
    def initAlgorithm(self, config=None):
        pass

    @abstractmethod
    def processAlgorithm(self, parameters, context, feedback):
        pass

    def _export_layer(self, layer, path, context):
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.fileEncoding = "UTF-8"

        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            str(path),
            context.transformContext(),
            options,
        )

        error_code, error_message = result[0], result[1]

        if error_code != QgsVectorFileWriter.NoError:
            raise QgsProcessingException(
                f"Failed to export layer '{layer.name()}': {error_message}"
            )