from qgis.core import (
    QgsProcessingParameterFile,
    QgsProcessingParameterString,
    QgsProcessingException
)
from .base import EnvironmentAlgorithm
from .utils import install_environment
from ...config import Config

class InstallEnvironmentAlgorithm(EnvironmentAlgorithm):

    VENV_PATH = "VENV_PATH"
    BLOCKSNET_REQUIREMENT = "BLOCKSNET_REQUIREMENT"

    def name(self):
        return "install_environment"

    def displayName(self):
        return "1. Install environment"

    def shortHelpString(self):
        return "Install Python environment for BlocksNet library"

    def createInstance(self):
        return InstallEnvironmentAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                self.VENV_PATH,
                "Virtual environment directory",
                behavior=QgsProcessingParameterFile.Folder
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.BLOCKSNET_REQUIREMENT,
                "BlocksNet package requirement",
                defaultValue="blocksnet[ipynb,torch]==1.0.0.a9",
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        venv_path = self.parameterAsFile(
            parameters,
            self.VENV_PATH,
            context,
        )
        blocksnet_requirement = self.parameterAsString(
            parameters,
            self.BLOCKSNET_REQUIREMENT,
            context,
        )

        feedback.pushInfo(f"Environment directory: {venv_path}")
        feedback.pushInfo("Installing BlocksNet environment...")

        try:
            python_exe = install_environment(venv_path, blocksnet_requirement, feedback=feedback)
            feedback.pushInfo("Environment installed successfully.")
            feedback.pushInfo(f"Python executable: {python_exe}")

        except Exception as e:
            raise QgsProcessingException(
                f"Failed to install environment: {e}"
            ) from e

        Config.set_environment(python_exe, feedback)

        return {
            'PYTHON_EXECUTABLE': python_exe
        }