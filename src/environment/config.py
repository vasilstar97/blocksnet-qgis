import os

from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsProcessingException


class Config:
    ENVIRONMENT_KEY = "BlocksNet/venv_python"

    @staticmethod
    def set_environment(python_exe, feedback):
        """Сохраняет путь к Python виртуального окружения."""
        if not os.path.isfile(python_exe):
            raise QgsProcessingException(
                f"Python executable not found: {python_exe}"
            )

        QSettings().setValue(
            Config.ENVIRONMENT_KEY,
            python_exe,
        )

        feedback.pushInfo(f"Python environment set: {python_exe}")

    @staticmethod
    def get_environment():
        """Возвращает путь к Python виртуального окружения."""
        python_exe = QSettings().value(
            Config.ENVIRONMENT_KEY,
            "",
            type=str,
        )

        if not python_exe or not os.path.isfile(python_exe):
            raise QgsProcessingException(
                "BlocksNet environment is not installed. "
                "Run the Install environment algorithm first."
            )

        return python_exe

    @staticmethod
    def clear_environment():
        """Удаляет сохранённый путь к окружению."""
        QSettings().remove(Config.ENVIRONMENT_KEY)