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

    BOUNDARIES = "BOUNDARIES"
    ROADS = "ROADS"
    RAILWAYS = "RAILWAYS"
    WATER = "WATER"
    OUTPUT = "OUTPUT"

    def name(self):
        return "aggregate_objects"

    def displayName(self):
        return "1. Aggregate objects"

    def shortHelpString(self):
        return "Aggregates objects within blocks"

    def createInstance(self):
        return ObjectsAggregationAlgorithm()

    def initAlgorithm(self, config=None):
        ...

    def processAlgorithm(self, parameters, context, feedback):
        ...