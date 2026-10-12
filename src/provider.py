from qgis.core import QgsProcessingProvider
from .algorithms import *


class BlocksNetProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(BlocksCuttingAlgorithm())
        ...

    def id(self):
        return "blocksnet"

    def name(self):
        return "BlocksNet"

    def longName(self):
        return self.name()