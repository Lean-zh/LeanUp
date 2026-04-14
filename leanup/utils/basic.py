import tempfile
import subprocess
from leanup.const import OS_TYPE, TMP_DIR
import shlex
from typing import Optional, Union, Tuple, List, Generator, Dict
from contextlib import contextmanager
from pathlib import Path
import os

def execute_command(command: Union[str, List[str]],
        cwd: Optional[str] = None,
        text: bool = True,
        input: Union[str, None] = None,
        capture_output: bool = True,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None) -> Tuple[str, str, int]:
    """
    Execute command with subprocess.Popen.

    Args:
        command: Command to execute (string or list of arguments)
        cwd: Working directory path
        text: Whether to return output as text
        input: Input string to pass to command
        capture_output: Whether to capture stdout/stderr
        timeout: Maximum execution time in seconds

    Returns:
        Tuple containing stdout, stderr, and return code
    """
    process = None
    try:
        stdout_pipe = subprocess.PIPE if capture_output else None
        stderr_pipe = subprocess.PIPE if capture_output else None
        # Handle string commands
        if isinstance(command, str) and OS_TYPE != 'Windows':
            command = shlex.split(command)
        popen_kwargs = {
            "cwd": cwd,
            "stdout": stdout_pipe,
            "stderr": stderr_pipe,
            "shell": OS_TYPE == 'Windows',
            "text": text,
        }
        if env is not None:
            popen_kwargs["env"] = env
        process = subprocess.Popen(command, **popen_kwargs)
        stdout, stderr = process.communicate(input=input, timeout=timeout)
        returncode = process.returncode
        stdout = stdout or ""
        stderr = stderr or ""
    except Exception as e:
        stdout, stderr, returncode = "", str(e), -1
    return stdout, stderr, returncode

@contextmanager
def working_directory(
    path: Optional[Union[str, Path]] = None,
    chdir: bool = False,
) -> Generator[Path, None, None]:
    """
    Context manager for temporarily changing working directory.

    Args:
        path: Target directory path (uses temporary directory if None)
        chdir: Whether to actually change the working directory

    Yields:
        Path object representing the current working directory
    """
    origin = Path.cwd()
    is_temporary = False
    tmp_dir = None

    if path is None:
        tmp_dir = tempfile.TemporaryDirectory(dir=TMP_DIR)
        path = tmp_dir.__enter__()
        is_temporary = True
    else:
        path = Path(path)
        if not path.exists():
            path.mkdir(parents=True)

    if chdir:
        os.chdir(path)

    try:
        yield Path(path)
    finally:
        if chdir:
            os.chdir(origin)
        if is_temporary and tmp_dir:
            tmp_dir.__exit__(None, None, None)
