
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
import tarfile
from pathlib import Path


PYTHON_VERSION = "3.10"
UV_VERSION = "0.12.20"


def log(feedback, message):
    if feedback is not None:
        feedback.pushInfo(str(message))


def find_any_python():
    """Находит доступный Python-интерпретатор."""

    candidates = [[sys.executable]]

    if os.name == "nt":
        launcher = shutil.which("py")
        if launcher:
            candidates.append([launcher, "-3"])

    for name in (
        "python",
        "python3",
        "python3.14",
        "python3.13",
        "python3.12",
        "python3.11",
        "python3.10",
    ):
        executable = shutil.which(name)
        if executable:
            candidates.append([executable])

    checked = set()

    for candidate in candidates:
        try:
            result = subprocess.run(
                candidate + [
                    "-c",
                    "import sys; print(sys.executable)",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                executable = result.stdout.strip().splitlines()[-1]
                if executable not in checked:
                    checked.add(executable)
                    return executable

        except (OSError, subprocess.TimeoutExpired):
            continue

    raise RuntimeError(
        "Python was not found. Please install Python 3.10 or newer "
        "and restart QGIS."
    )


def get_uv_install_dir():
    """Возвращает пользовательскую папку для uv."""

    if sys.platform == "win32":
        base_dir = Path(
            os.environ.get(
                "LOCALAPPDATA",
                Path.home() / "AppData" / "Local",
            )
        )
    else:
        base_dir = Path.home() / ".local" / "share"

    return base_dir / "blocksnet-qgis" / "uv"


def get_uv_executable():
    """Возвращает путь к бинарному файлу uv."""

    install_dir = get_uv_install_dir()

    if sys.platform == "win32":
        return install_dir / "uv.exe"

    return install_dir / "uv"


def get_uv_asset():
    """Определяет имя официального архива uv для текущей ОС."""

    system = sys.platform
    machine = platform.machine().lower()

    if system == "win32":
        if machine in ("amd64", "x86_64"):
            return "uv-x86_64-pc-windows-msvc.zip", "zip"
        if machine in ("arm64", "aarch64"):
            return "uv-aarch64-pc-windows-msvc.zip", "zip"

    elif system == "darwin":
        if machine in ("x86_64", "amd64"):
            return "uv-x86_64-apple-darwin.tar.gz", "tar"
        if machine in ("arm64", "aarch64"):
            return "uv-aarch64-apple-darwin.tar.gz", "tar"

    elif system.startswith("linux"):
        if machine in ("x86_64", "amd64"):
            return "uv-x86_64-unknown-linux-gnu.tar.gz", "tar"
        if machine in ("aarch64", "arm64"):
            return "uv-aarch64-unknown-linux-gnu.tar.gz", "tar"

    raise RuntimeError(
        f"Unsupported operating system or architecture: "
        f"{system}, {machine}"
    )


def ensure_uv(feedback=None):
    """Скачивает официальный бинарный файл uv, если его нет."""

    uv_executable = get_uv_executable()

    if uv_executable.is_file():
        log(feedback, f"Using uv: {uv_executable}")
        return uv_executable

    install_dir = uv_executable.parent
    install_dir.mkdir(parents=True, exist_ok=True)

    asset_name, archive_type = get_uv_asset()
    url = (
        "https://github.com/astral-sh/uv/releases/download/"
        f"{UV_VERSION}/{asset_name}"
    )

    log(feedback, f"Downloading uv {UV_VERSION}: {asset_name}")

    with tempfile.TemporaryDirectory(
        prefix="blocksnet-uv-"
    ) as temp_dir:
        archive_path = Path(temp_dir) / asset_name

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "blocksnet-qgis"},
        )

        try:
            with urllib.request.urlopen(
                request, timeout=60
            ) as response:
                archive_path.write_bytes(response.read())
        except Exception as exc:
            raise RuntimeError(
                f"Failed to download uv: {exc}"
            ) from exc

        try:
            if archive_type == "zip":
                with zipfile.ZipFile(archive_path) as archive:
                    member = next(
                        (
                            name for name in archive.namelist()
                            if name == "uv.exe"
                            or name.endswith("/uv.exe")
                        ),
                        None,
                    )

                    if member is None:
                        raise RuntimeError(
                            "Downloaded uv archive does not contain uv.exe."
                        )

                    with archive.open(member) as source:
                        with open(uv_executable, "wb") as target:
                            shutil.copyfileobj(source, target)

            else:
                with tarfile.open(
                    archive_path, mode="r:gz"
                ) as archive:
                    member = next(
                        (
                            item for item in archive.getmembers()
                            if item.isfile()
                            and Path(item.name).name == "uv"
                        ),
                        None,
                    )

                    if member is None:
                        raise RuntimeError(
                            "Downloaded uv archive does not contain uv."
                        )

                    source = archive.extractfile(member)
                    if source is None:
                        raise RuntimeError(
                            "Could not extract uv executable."
                        )

                    with source, open(uv_executable, "wb") as target:
                        shutil.copyfileobj(source, target)

                uv_executable.chmod(0o755)

        except (zipfile.BadZipFile, tarfile.TarError) as exc:
            raise RuntimeError(
                f"Downloaded uv archive is invalid: {exc}"
            ) from exc
        except Exception:
            if uv_executable.exists():
                uv_executable.unlink()
            raise

    if not uv_executable.is_file():
        raise RuntimeError(
            f"uv executable was not created: {uv_executable}"
        )

    log(feedback, f"uv downloaded: {uv_executable}")
    return uv_executable


def run_command(command, feedback=None, env=None):
    """Запускает команду, передаёт вывод в журнал QGIS и поддерживает отмену."""

    command = list(map(str, command))
    log(feedback, f"Running: {' '.join(command)}")

    # Наследуем окружение QGIS либо используем переданное окружение.
    command_env = os.environ.copy()

    if env is not None:
        command_env.update(env)

    # Не позволяем дочернему Python подхватывать библиотеки QGIS/Python 3.12.
    command_env.pop("PYTHONHOME", None)
    command_env.pop("PYTHONPATH", None)

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=command_env,
        shell=False,
    )

    try:
        if process.stdout is not None:
            for line in process.stdout:
                if feedback is not None and feedback.isCanceled():
                    process.terminate()

                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()

                    raise RuntimeError("Installation was canceled.")

                line = line.rstrip()
                if line:
                    log(feedback, line)

        return_code = process.wait()

        # Дополнительно проверяем отмену после завершения процесса.
        if feedback is not None and feedback.isCanceled():
            raise RuntimeError("Installation was canceled.")

        if return_code != 0:
            raise RuntimeError(
                f"Command failed with exit code {return_code}: "
                f"{' '.join(command)}"
            )

    finally:
        if process.stdout is not None:
            process.stdout.close()


def get_environment_python(env_dir):
    """Возвращает путь к Python внутри venv."""

    if os.name == "nt":
        return env_dir / "Scripts" / "python.exe"

    return env_dir / "bin" / "python"


def check_environment_python(env_python):
    """Проверяет, что интерпретатор использует Python 3.10."""

    try:
        result = subprocess.run(
            [
                str(env_python),
                "-c",
                (
                    "import sys; "
                    "print(f'{sys.version_info.major}."
                    "{sys.version_info.minor}')"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    return (
        result.returncode == 0
        and result.stdout.strip() == PYTHON_VERSION
    )


def install_environment(
    install_dir,
    blocksnet_requirement,
    feedback=None,
):
    """Создаёт Python 3.10 venv, устанавливает BlocksNet."""

    # 1. Проверяем, что доступен хотя бы один Python.
    python_executable = find_any_python()
    log(feedback, f"Found Python: {python_executable}")

    env_dir = Path(install_dir).expanduser().resolve()
    env_dir.mkdir(parents=True, exist_ok=True)

    env_python = get_environment_python(env_dir)

    # 2. Получаем uv.
    uv = ensure_uv(feedback)

    # 3. Проверяем существующее окружение.
    if env_python.exists():
        if not check_environment_python(env_python):
            raise RuntimeError(
                f"Existing environment is not a valid Python "
                f"{PYTHON_VERSION} environment: {env_dir}. "
                "Choose an empty directory."
            )

        log(feedback, "Using existing Python 3.10 environment.")

    else:
        if any(env_dir.iterdir()):
            raise RuntimeError(
                f"The selected directory is not empty and does not "
                f"contain a valid environment: {env_dir}"
            )

        log(
            feedback,
            f"Creating environment with Python {PYTHON_VERSION}...",
        )

        # uv загрузит Python 3.10, если он ещё не установлен.
        run_command(
            [
                uv,
                "venv",
                "--python",
                PYTHON_VERSION,
                env_dir,
            ],
            feedback,
        )

        if not env_python.is_file():
            raise RuntimeError(
                f"Virtual environment was not created correctly: "
                f"{env_dir}"
            )

        if not check_environment_python(env_python):
            raise RuntimeError(
                f"The created environment does not use Python "
                f"{PYTHON_VERSION}: {env_dir}"
            )

    # 4. Устанавливаем BlocksNet и зависимости.
    log(feedback, "Installing BlocksNet and dependencies...")

    run_command(
        [
            uv,
            "pip",
            "install",
            "--python",
            env_python,
            "--upgrade",
            blocksnet_requirement,
        ],
        feedback,
    )

    # 5. Проверяем Python и импорт BlocksNet.
    run_command(
        [
            env_python,
            "-c",
            (
                "import sys, blocksnet; "
                "assert sys.version_info[:2] == (3, 10); "
                "print('BlocksNet environment is ready')"
            ),
        ],
        feedback,
    )

    log(feedback, f"Environment ready: {env_dir}")
    log(feedback, f"Python executable: {env_python}")

    return str(env_python)

__all__=[
    "log",
    "find_any_python",
    "get_uv_install_dir",
    "get_uv_executable",
    "get_uv_asset",
    "ensure_uv",
    "run_command",
    "get_environment_python",
    "check_environment_python",
    "install_environment"
]