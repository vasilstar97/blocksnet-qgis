from qgis.core import QgsProcessingProvider
from .algorithms import *


class BlocksNetProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        # 1. Environment
        self.addAlgorithm(InstallEnvironmentAlgorithm())
        # 2. Preprocessing
        self.addAlgorithm(BlocksCuttingAlgorithm())
        self.addAlgorithm(ObjectsAggregationAlgorithm())
        # 3. Accessibility
        self.addAlgorithm(GraphAlgorithm())
        self.addAlgorithm(MatrixAlgorithm())

    def id(self):
        return "blocksnet"

    def name(self):
        return "BlocksNet"

    def longName(self):
        return self.name()