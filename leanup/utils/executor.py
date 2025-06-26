import subprocess
import os
from typing import Optional, Union, Tuple, List, Dict, Any
import git
from psutil import Process, NoSuchProcess
import logging

logger = logging.getLogger(__name__)

class CommandExecutor:
    def __init__(self, cwd: Optional[str] = None, timeout: Optional[int] = None):
        """
        Initialize command executor
        
        Args:
            cwd: Default working directory
        """
        self.cwd = cwd
        self.timeout = timeout
        self.active_processes = []  # Track active processes
    
    def execute(self, command: list,
            cwd: Optional[str] = None, 
            text: bool = True,
            input: Union[str, None] = None,
            capture_output: bool = True,
            timeout: Optional[int] = None) -> Tuple[str, str, int]:
        """
        Execute command and capture output
        
        Args:
            command: Command list to execute
            cwd: Working directory for command execution
            text: Whether to use text mode
            input: Input to pass to command
            capture_output: Whether to capture command output
            timeout: Command execution timeout in seconds
            
        Returns:
            Tuple containing (stdout, stderr, return_code)
        """
        working_dir = cwd or self.cwd
        self.active_processes = []
        timeout = timeout if timeout is not None else self.timeout
        
        try:
            # Configure output pipes
            stdout_pipe = subprocess.PIPE if capture_output else None
            stderr_pipe = subprocess.PIPE if capture_output else None
            
            # Create and start process
            proc = subprocess.Popen(
                command,
                cwd=working_dir,
                stdout=stdout_pipe,
                stderr=stderr_pipe,
                text=text
            )
            
            # Track process and its children
            main_pid = proc.pid
            self.active_processes = self._get_process_children(main_pid) + [Process(main_pid)]
            
            # Wait for completion and get output
            proc_output, proc_error = proc.communicate(input=input, timeout=timeout)
            exit_code = proc.returncode
            
            # Ensure output strings are not None
            command_output = proc_output or ""
            error_output = proc_error or ""
            
        except Exception as e:
            # Handle execution errors
            command_output, error_output, exit_code = "", str(e), -1
        finally:
            # Always cleanup processes
            self._cleanup_processes()
        return command_output, error_output, exit_code
    
    def _set_limits(self):
        """Set resource limits for processes"""
        # TODO: Implement memory limit logic
        pass
    
    def _get_process_children(self, pid: int) -> List[Process]:
        """
        Get child processes for given PID
        
        Args:
            pid: Parent process ID
            
        Returns:
            List of child processes
        """
        try:
            parent_process = Process(pid)
            return parent_process.children(recursive=True)
        except NoSuchProcess:
            return []
    
    def _cleanup_processes(self):
        """
        Clean up all tracked processes
        Attempts to terminate processes gracefully
        """
        for process in self.active_processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception as e:
                if not isinstance(e, NoSuchProcess):
                    logger.debug(f"Failed to terminate process {process}: {e}")
    
    # Git operations
    def git_clone(self, repo_url: str, target_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Clone a git repository
        
        Args:
            repo_url: Repository URL to clone
            target_dir: Target directory for clone
            
        Returns:
            Tuple of (success_status, error_message)
        """
        try:
            git.Repo.clone_from(repo_url, target_dir or os.path.basename(repo_url.split('/')[-1].split('.')[0]))
            return True, ""
        except Exception as e:
            return False, str(e)

        