from dataclasses import dataclass
import shutil
import re
from pathlib import Path
from token import OP
from typing import Optional, Union, List, Dict, Any, Tuple
import git
import os
import toml
from leanup.const import OS_TYPE, LEANUP_CACHE_DIR
from leanup.utils.basic import execute_command
from leanup.utils.custom_logger import setup_logger

logger = setup_logger("repo_manager")


# Installation Config
class InstallConfig:
    def __init__(self, 
                 suffix: Optional[str]=None, 
                 source: Optional[str]='https://github.com', 
                 url: Optional[str]=None, 
                 branch: Optional[str]=None, 
                 dest_name: Optional[str]=None, 
                 dest_dir: Optional[Path]=None, 
                 build_packages: Optional[List[str]]=None, 
                 lake_update: bool = False, 
                 lake_build:bool = False, 
                 override: bool = False):
        self._suffix = suffix
        self._url = url
        self._dest_name = dest_name
        self._dest_dir = dest_dir
        self._build_packages = build_packages
        self.branch = branch
        self.source = source
        self.lake_update = lake_update
        self.lake_build = lake_build
        self.override = override

    @property
    def url(self):
        if self._url is None:
            if self._suffix is None:
                raise ValueError("suffix or url is required")
            return f"{self.source}/{self._suffix}"
        return self._url
    
    @property
    def suffix(self):
        if self._suffix is None:
            suffix = self._url.strip().split('/')[-1]
            if suffix.endswith('.git'):
                suffix = suffix[:-4]
            return suffix
        return self._suffix
    
    @property
    def dest_name(self):
        if self._dest_name is None:
            dest_name = self.suffix.lower()
            if self.branch:
                dest_name += f"/{self.branch}"
            return dest_name
        return self._dest_name

    @property
    def dest_dir(self):
        if self._dest_dir is None:
            return LEANUP_CACHE_DIR / "repos"
        return self._dest_dir

    @property
    def build_packages(self):
        value = self._build_packages
        if not value:
            return []
        if isinstance(value, str):
            return [pkg.strip() for pkg in value.strip('[]').split(',')]
        elif isinstance(value, list):
            return value
        else:
            return []
    
    @property
    def is_valid(self):
        return self.url is not None

    @property
    def dest_path(self)->Path:
        return self.dest_dir / self.dest_name
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value"""
        return getattr(self, key, default)
    
    def update(self, **kwargs):
        """Update config"""
        config = self.copy()
        for k, v in kwargs.items():
            if v is not None:
                if k in ("suffix", "url", "dest_name", "dest_dir", "build_packages"):
                    k = f"_{k}"
                setattr(config, k, v)
        return config
    
    def copy(self) -> 'InstallConfig':
        """Copy config"""
        return InstallConfig(
            suffix=self._suffix,
            source=self.source,
            url=self._url,
            branch=self.branch,
            dest_name=self._dest_name,
            dest_dir=self._dest_dir,
            build_packages=self._build_packages,
            lake_update=self.lake_update,
            lake_build=self.lake_build,
            override=self.override,
        )

    def install(self):
        repo = LeanRepo(self.dest_path)
        repo.install(self)

class RepoManager:
    """Class for managing directory operations and git functionality."""
    
    def __init__(self, cwd: Union[str, Path]=None):
        """Initialize with a working directory.
        
        Args:
            cwd: Working directory path
        """
        if cwd is None:
            cwd = Path.cwd().resolve()
        else:
            self.cwd = Path(cwd).resolve()
        self._git_repo = None
        self._check_git_repo()
    
    def _check_git_repo(self) -> None:
        """Check if the current directory is a git repository and initialize git.Repo if it is."""
        try:
            if (self.cwd / ".git").exists():
                self._git_repo = git.Repo(self.cwd)
                # logger.debug(f"Git repository found at {self.cwd}")
            else:
                logger.debug(f"{self.cwd} is not a git repository")
        except Exception as e:
            logger.error(f"Error checking git repository: {e}")
    
    @property
    def is_gitrepo(self) -> bool:
        """Check if the current directory is a git repository.
        
        Returns:
            bool: True if the directory is a git repository, False otherwise
        """
        return self._git_repo is not None
    
    def clone_from(self, url: str, branch: Optional[str] = None, depth: Optional[int] = None) -> bool:
        """Clone a git repository to the current directory.
        
        Args:
            url: Git repository URL
            branch: Branch to clone (optional)
            depth: Depth for shallow clone (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare command
            cmd = ["git", "clone", url, "."]
            if branch:
                cmd.extend(["--branch", branch])
            if depth:
                cmd.extend(["--depth", str(depth)])
                
            # Execute clone command
            self.cwd.mkdir(parents=True, exist_ok=True)
            stdout, stderr, returncode = execute_command(cmd, cwd=str(self.cwd))
            
            if returncode == 0:
                logger.info(f"Successfully cloned {url} to {self.cwd}")
                self._check_git_repo()  # Refresh git repo status
                return True
            else:
                logger.error(f"Failed to clone repository: {stderr}")
                return False
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            return False
    
    def clone_from_path(self, path: Union[str, Path]) -> bool:
        """Clone a git repository from a local path.
        
        Args:
            path: Local path to the git repository
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            path = Path(path).resolve()
            if path.resolve() == Path().resolve():
                logger.error("Cannot clone repository from current directory")
                return False
            # Clone repository
            git.Repo.clone_from(str(path), str(self.cwd))
            return True
        except Exception as e:
            logger.error(f"Error cloning repository from path: {e}")
            return False
    
    def execute_command(self, command: Union[str, List[str]]) -> Tuple[str, str, int]:
        """Execute a command in the current directory.
        
        Args:
            command: Command to execute (string or list of arguments)
            
        Returns:
            Tuple containing stdout, stderr, and return code
        """
        return execute_command(command, cwd=str(self.cwd))
    
    def read_file(self, file_path: Union[str, Path]) -> str:
        """Read the contents of a file.
        
        Args:
            file_path: Path to the file (relative to cwd)
            
        Returns:
            str: File contents
        
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        path = self.cwd / file_path
        return path.read_text(encoding='utf-8')
    
    def write_file(self, file_path: Union[str, Path], content: str, append: bool = False) -> bool:
        """Write content to a file.
        
        Args:
            file_path: Path to the file (relative to cwd)
            content: Content to write
            append: Whether to append to the file (default: False)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            path = self.cwd / file_path
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            mode = 'a' if append else 'w'
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {e}")
            return False
    
    def edit_file(self, file_path: Union[str, Path], 
                  find_text: str, replace_text: str, 
                  use_regex: bool = False) -> bool:
        """Edit a file by replacing text.
        
        Args:
            file_path: Path to the file (relative to cwd)
            find_text: Text to find
            replace_text: Text to replace with
            use_regex: Whether to use regex for find/replace
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            path = self.cwd / file_path
            if not path.exists():
                logger.error(f"File {file_path} does not exist")
                return False
                
            content = path.read_text(encoding='utf-8')
            
            if use_regex:
                new_content = re.sub(find_text, replace_text, content)
            else:
                new_content = content.replace(find_text, replace_text)
                
            path.write_text(new_content, encoding='utf-8')
            return True
        except Exception as e:
            logger.error(f"Error editing file {file_path}: {e}")
            return False
    
    def list_files(self, pattern: Optional[str] = None) -> List[Path]:
        """List files in the current directory, optionally filtered by pattern.
        
        Args:
            pattern: Glob pattern to filter files
            
        Returns:
            List of Path objects
        """
        if pattern:
            return list(self.cwd.glob(pattern))
        else:
            return [p for p in self.cwd.iterdir() if p.is_file()]
    
    def list_dirs(self, pattern: Optional[str] = None) -> List[Path]:
        """List subdirectories in the current directory, optionally filtered by pattern.
        
        Args:
            pattern: Glob pattern to filter directories
            
        Returns:
            List of Path objects
        """
        if pattern:
            return [p for p in self.cwd.glob(pattern) if p.is_dir()]
        else:
            return [p for p in self.cwd.iterdir() if p.is_dir()]
    
    # Git operations
    def git_status(self) -> Dict[str, Any]:
        """Get git status information.
        
        Returns:
            Dict containing status information or error message
        """
        if not self.is_gitrepo:
            return {"error": "Not a git repository"}
        try:
            return {
                "branch": self._git_repo.active_branch.name,
                "is_dirty": self._git_repo.is_dirty(),
                "untracked_files": self._git_repo.untracked_files,
                "modified_files": [item.a_path for item in self._git_repo.index.diff(None)]
            }
        except Exception as e:
            return {"error": str(e)}

    def git_init(self) -> bool:
        """Initialize git repository."""
        try:
            self._git_repo = git.Repo.init(str(self.cwd))
            return True
        except Exception as e:
            logger.error(f"Error initializing git repository: {e}")
            return False

    def git_add(self, paths: Union[str, List[str], None] = None) -> bool:
        """Add files to git staging area.
        
        Args:
            paths: File path(s) to add, or None to add all
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_gitrepo:
            logger.warning("Not a git repository")
            return False
        try:
            if paths is None:
                # Add all files
                self._git_repo.git.add(A=True)
            elif isinstance(paths, str):
                # Add single file
                self._git_repo.git.add(paths)
            else:
                # Add multiple files
                for path in paths:
                    self._git_repo.git.add(path)
            return True
        except Exception as e:
            logger.error(f"Error adding files to git: {e}")
            return False
    
    def git_commit(self, message: str) -> bool:
        """Commit changes to git repository.
        
        Args:
            message: Commit message
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_gitrepo:
            logger.warning("Not a git repository")
            return False
        
        try:
            self._git_repo.git.commit(m=message)
            return True
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            return False
    
    def git_pull(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """Pull changes from remote repository.
        
        Args:
            remote: Remote name
            branch: Branch name (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_gitrepo:
            logger.warning("Not a git repository")
            return False
        
        try:
            if branch:
                self._git_repo.git.pull(remote, branch)
            else:
                self._git_repo.git.pull()
            return True
        except Exception as e:
            logger.error(f"Error pulling changes: {e}")
            return False
    
    def git_push(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """Push changes to remote repository.
        
        Args:
            remote: Remote name
            branch: Branch name (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_gitrepo:
            logger.warning("Not a git repository")
            return False
        
        try:
            if branch:
                self._git_repo.git.push(remote, branch)
            else:
                self._git_repo.git.push()
            return True
        except Exception as e:
            logger.error(f"Error pushing changes: {e}")
            return False

class LeanRepo(RepoManager):
    """Class for managing Lean repositories with lake support."""
    
    def __init__(self, cwd: Union[str, Path]=None):
        """Initialize LeanRepo with working directory.
        
        Args:
            cwd: Working directory path
        """
        super().__init__(cwd)
        self.elan_home = Path(os.environ.get('ELAN_HOME', Path.home() / '.elan'))
        self.elan_bin_dir = self.elan_home / 'bin'
        self._lake_exe = None
        self.lean_version = self.get_lean_toolchain()
    
    @property
    def lake_exe(self):
        if self._lake_exe is None:
            self._lake_exe = self.get_lake_executable()
        return self._lake_exe
    
    def get_lake_executable(self) -> Optional[Path]:
        """Get lake executable file path"""
        lake_exe = 'lake.exe' if OS_TYPE == 'Windows' else 'lake'
        lake_path = self.elan_bin_dir / lake_exe
        
        if lake_path.exists() and lake_path.is_file():
            return lake_path
        
        # Try to find in PATH
        lake_in_path = shutil.which('lake')
        if lake_in_path:
            return Path(lake_in_path)
        
        return None

    def get_lean_toolchain(self) -> Optional[str]:
        """Read lean-toolchain file to get Lean version.
        
        Returns:
            str: Lean version if found, None otherwise
        """
        try:
            toolchain_file = self.cwd / "lean-toolchain"
            if toolchain_file.exists():
                content = toolchain_file.read_text(encoding='utf-8').strip()
                logger.debug(f"Found Lean toolchain: {content}")
                return content
            else:
                logger.debug("lean-toolchain file not found")
                return None
        except Exception as e:
            logger.error(f"Error reading lean-toolchain: {e}")
            return None
    
    def lake(self, args: List[str]) -> Tuple[str, str, int]:
        """Execute lake command with given arguments.
        
        Args:
            args: List of lake command arguments
            
        Returns:
            Tuple containing stdout, stderr, and return code
        """
        if isinstance(args, str):
            args = [args]
        command = [str(self.lake_exe)] + args
        logger.debug("Executing lake command: " + ' '.join(command))
        return self.execute_command(command)
    
    def lake_env_which(self, name: str) -> Tuple[str, str, int]:
        """Check if a lake package is installed.
        
        Args:
            name: Package name
            
        Returns:
            Tuple containing stdout, stderr, and return code
        """
        msg, err, code = self.lake(["env", "which", name])
        if code == 0:
            return msg, err, code
        else:
            logger.error(f"Error checking package {name}: {err}")
            return msg, err, code
        
    def lake_init(self,
                  name: Optional[str] = None,
                  template: Optional[str] = None,
                  language: Optional[str] = None) -> Tuple[str, str, int]:
        """Initialize lake repository.
        
        Args:
            name: Repository name
            template: Template name
            language: Language name

        The initial configuration and starter files are based on the template:

            std    library and executable; default
            exe    executable only
            lib    library only
            math   library only with a mathlib dependency
        
        Templates can be suffixed with `.lean` or `.toml` to produce a Lean or TOML
        version of the configuration file, respectively. The default is Lean.

        Returns:
            Tuple containing stdout, stderr, and return code
        """
        if not self.cwd.exists():
            self.cwd.mkdir(parents=True)
        cmds = ["init"]
        if name:
            cmds.append(name)
        if template:
            assert name is not None, "Repository name is required when template is specified"
            assert template in ["std", "exe", "lib", "math"], "Invalid template name"
            cmds.append(template)
        if language:
            assert language in ["lean", "toml", '.lean', '.toml'], "Invalid language name"
            if not language.startswith('.'):
                language = '.' + language
            if template is not None:
                cmds[-1] += f".{language}"
        return self.lake(cmds)
    
    def lake_build(self, target: Optional[str] = None) -> Tuple[str, str, int]:
        """Build the Lean project using lake.
        
        Args:
            target: Optional build target
            
        Returns:
            Tuple containing stdout, stderr, and return code
        """
        args = ["build"]
        if target:
            args.append(target)
        return self.lake(args)
    
    def lake_update(self) -> Tuple[str, str, int]:
        """Update dependencies using lake.
        
        Returns:
            Tuple containing stdout, stderr, and return code
        """
        return self.lake(["update"])
    
    def lake_env_lean(
        self, 
        filepath: Union[str, Path], 
        json: bool = True, 
        options: Optional[Dict[str, Any]] = None,
        nproc: Optional[int] = None) -> Tuple[str, str, int]:
        """Run lean file with lake environment.
        
        Args:
            filepath: Path to the Lean file
            json: Whether to return JSON output, default is True
            
        Returns:
            Tuple containing stdout, stderr, and return code
        """
        args = ["env", "lean"]
        if json:
            args.append("--json")
        if options is not None:
            opts = ["-D {}={}".format(k,v) for k,v in options.items()]
            args += opts
        if isinstance(nproc, int) and nproc > 0:
            # nproc += 1
            args += ["-j", str(nproc)]
        args.append(str(filepath))
        return self.lake(args)
    
    def lake_clean(self) -> Tuple[str, str, int]:
        """Clean build artifacts using lake.
        
        Returns:
            Tuple containing stdout, stderr, and return code
        """
        return self.lake(["clean"])
    
    def lake_test(self) -> Tuple[str, str, int]:
        """Run tests using lake.
        
        Returns:
            Tuple containing stdout, stderr, and return code
        """
        return self.lake(["test"])
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get comprehensive project information.
        
        Returns:
            Dict containing project information
        """
        info = {
            'lean_version': self.get_lean_toolchain(),
            'has_lakefile_toml': (self.cwd / "lakefile.toml").exists(),
            'has_lakefile_lean': (self.cwd / "lakefile.lean").exists(),
            'has_lake_manifest': (self.cwd / "lake-manifest.json").exists(),
            'build_dir_exists': (self.cwd / ".lake").exists(),
        }
        return info
    
    def install(self, config: InstallConfig, **kwargs):
        """Install Lean repository.
        
        Args:
            config: InstallConfig object
            kwargs: Additional keyword arguments for lake_init
        """
        config = config.update(**kwargs)
        assert config.url, "Repository URL is required"
        repo_dir = config.dest_dir / config.dest_name
        if repo_dir.exists():
            if config.override:
                shutil.rmtree(repo_dir)
                logger.info(f"{repo_dir} removed successfully.")
            else:
                logger.info(f"Repository already exists at {repo_dir}")
                return True
        repo = LeanRepo(repo_dir)
        success = repo.clone_from(
            url=config.url,
            branch=config.branch,
            depth=1  # Shallow clone for faster download
        )
        if not success:
            logger.error(f"Failed to clone repository: {config.url}")
            return False
        if config.lake_update:
            if not repo.lake_update():
                logger.warning(f"Failed to update repository: {config.url}")
            else:
                logger.info(f"Successfully cloned repository: {config.url}")
        if config.lake_build:
            if not repo.lake_build():
                logger.warning(f"Failed to build repository: {config.url}")
            else:
                logger.info(f"Successfully built repository: {config.url}")
        if config.build_packages:
            for package in config.build_packages:
                if package:
                    logger.info(f"Building package: {package}")
                else:
                    logger.info("Running lake build")
                if not repo.lake_build(package):
                    logger.warning(f"Failed to build package: {package}")
        return True
