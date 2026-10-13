from abc import ABC, abstractmethod

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
)


class BaseAlgorithm(QgsProcessingAlgorithm, ABC):

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