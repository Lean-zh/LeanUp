import pytest
import shutil
from unittest.mock import patch, Mock
from pathlib import Path
import tempfile

from leanup.repo.manager import LeanRepo, InstallConfig


class TestInstallConfig:
    """Test cases for InstallConfig class"""
    
    def test_install_config_basic(self):
        """Test basic InstallConfig initialization"""
        config = InstallConfig(
            suffix='test/repo',
            source='https://github.com'
        )
        
        assert config.suffix == 'test/repo'
        assert config.source == 'https://github.com'
        assert config.url == 'https://github.com/test/repo'
        assert config.is_valid is True
    
    def test_install_config_with_url(self):
        """Test InstallConfig with direct URL"""
        config = InstallConfig(
            url='https://gitlab.com/user/project.git'
        )
        
        assert config.url == 'https://gitlab.com/user/project.git'
        assert config.suffix == 'project'
        assert config.is_valid is True
    
    def test_install_config_dest_name_generation(self):
        """Test destination name generation"""
        config = InstallConfig(
            suffix='user/repo',
            branch='main'
        )
        
        assert config.dest_name == 'user/repo/main'
    
    def test_install_config_copy_and_update(self):
        """Test config copy and update methods"""
        config = InstallConfig(
            suffix='test/repo',
            lake_update=False
        )
        
        # Test copy
        config_copy = config.copy()
        assert config_copy.suffix == config.suffix
        assert config_copy is not config
        
        # Test update
        updated_config = config.update(lake_update=True, branch='main')
        assert updated_config.lake_update is True
        assert updated_config.branch == 'main'
        assert config.lake_update is False  # Original unchanged


class TestRepoManager:
    """Test cases for RepoManager class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_manager = LeanRepo(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test RepoManager initialization"""
        assert self.repo_manager.cwd == Path(self.temp_dir).resolve()
        assert not self.repo_manager.is_gitrepo
    
    @patch('leanup.repo.manager.execute_command')
    def test_clone_from_success(self, mock_execute):
        """Test successful repository cloning"""
        mock_execute.return_value = ('', '', 0)
        
        result = self.repo_manager.clone_from('https://github.com/test/repo.git')
        
        assert result is True
        mock_execute.assert_called_once()
    
    @patch('leanup.repo.manager.execute_command')
    def test_clone_from_failure(self, mock_execute):
        """Test failed repository cloning"""
        mock_execute.return_value = ('', 'error', 1)
        
        result = self.repo_manager.clone_from('https://github.com/test/repo.git')
        
        assert result is False
    
    def test_read_write_file(self):
        """Test file read/write operations"""
        content = "test content"
        file_path = "test.txt"
        
        # Test write
        result = self.repo_manager.write_file(file_path, content)
        assert result is True
        
        # Test read
        read_content = self.repo_manager.read_file(file_path)
        assert read_content == content
    
    def test_edit_file(self):
        """Test file editing"""
        original_content = "Hello world"
        file_path = "test.txt"
        
        # Create file
        self.repo_manager.write_file(file_path, original_content)
        
        # Edit file
        result = self.repo_manager.edit_file(file_path, "world", "universe")
        assert result is True
        
        # Verify edit
        new_content = self.repo_manager.read_file(file_path)
        assert new_content == "Hello universe"
    
    def test_list_files_and_dirs(self):
        """Test listing files and directories"""
        # Create test files and directories
        (Path(self.temp_dir) / "file1.txt").write_text("content")
        (Path(self.temp_dir) / "file2.py").write_text("content")
        (Path(self.temp_dir) / "subdir").mkdir()
        
        # Test list files
        files = self.repo_manager.list_files()
        assert len(files) == 2
        
        # Test list files with pattern
        py_files = self.repo_manager.list_files("*.py")
        assert len(py_files) == 1
        assert py_files[0].name == "file2.py"
        
        # Test list directories
        dirs = self.repo_manager.list_dirs()
        assert len(dirs) == 1
        assert dirs[0].name == "subdir"
    
    @patch('leanup.repo.manager.LeanRepo')
    def test_install_method(self, mock_lean_repo):
        """Test RepoManager install method"""
        # Mock LeanRepo
        mock_repo = Mock()
        mock_repo.clone_from.return_value = True
        mock_repo.lake_update.return_value = ("output", "", 0)
        mock_repo.lake_build.return_value = ("output", "", 0)
        mock_lean_repo.return_value = mock_repo
        
        # Create config
        config = InstallConfig(
            url='https://github.com/test/repo.git',
            dest_dir=Path(self.temp_dir),
            dest_name='test_repo',
            lake_update=True,
            lake_build=True
        )
        
        result = self.repo_manager.install(config)
        
        assert result is True
        mock_repo.clone_from.assert_called_once()
        mock_repo.lake_update.assert_called_once()
        mock_repo.lake_build.assert_called_once()


class TestLeanRepo:
    """Test cases for LeanRepo class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.lean_repo = LeanRepo(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_lean_toolchain_exists(self):
        """Test reading lean-toolchain file when it exists"""
        toolchain_content = "leanprover/lean4:v4.3.0"
        toolchain_file = Path(self.temp_dir) / "lean-toolchain"
        toolchain_file.write_text(toolchain_content)
        
        result = self.lean_repo.get_lean_toolchain()
        assert result == toolchain_content
    
    def test_get_lean_toolchain_not_exists(self):
        """Test reading lean-toolchain file when it doesn't exist"""
        result = self.lean_repo.get_lean_toolchain()
        assert result is None
    
    @patch('leanup.repo.manager.execute_command')
    def test_lake_init(self, mock_execute):
        """Test lake init command"""
        mock_execute.return_value = ('output', '', 0)
        
        result = self.lean_repo.lake_init('test_project', 'std')
        
        assert result == ('output', '', 0)
        lake = shutil.which('lake')
        # mock_execute.assert_called_once_with([str(lake), 'init', 'test_project', 'std'], cwd=str(self.lean_repo.cwd))
    
    @patch('leanup.repo.manager.execute_command')
    def test_lake_env_lean(self, mock_execute):
        """Test lake env lean command"""
        mock_execute.return_value = ('output', '', 0)
        
        result = self.lean_repo.lake_env_lean('test.lean', json=True, nproc=4)
        
        assert result == ('output', '', 0)
        lake = shutil.which('lake')
        expected_cmd = [str(lake), 'env', 'lean', '--json', '-j', '4', 'test.lean']
        # mock_execute.assert_called_once_with(expected_cmd, cwd=str(self.lean_repo.cwd))
    
    def test_get_project_info(self):
        """Test getting project information"""
        # Create some files
        (Path(self.temp_dir) / "lean-toolchain").write_text("leanprover/lean4:v4.3.0")
        (Path(self.temp_dir) / "lakefile.toml").write_text("[package]\nname = 'test'")
        (Path(self.temp_dir) / ".lake").mkdir()
        
        info = self.lean_repo.get_project_info()
        
        assert info['lean_version'] == "leanprover/lean4:v4.3.0"
        assert info['has_lakefile_toml'] is True
        assert info['has_lakefile_lean'] is False
        assert info['build_dir_exists'] is True
        assert info['has_lake_manifest'] is False

    def test_normalize_lean_version_adds_prefix(self):
        assert LeanRepo.normalize_lean_version('4.14.0') == 'v4.14.0'

    def test_normalize_lean_version_keeps_prefixed_version(self):
        assert LeanRepo.normalize_lean_version('v4.14.0') == 'v4.14.0'

    def test_build_math_lakefile_uses_version_and_package_name(self):
        content = LeanRepo.build_math_lakefile('lean4web', 'v4.14.0')

        assert 'package «lean4web» where' in content
        assert '"https://github.com/leanprover-community/mathlib4.git" @ "v4.14.0"' in content
        assert 'lean_lib «Lean4web» where' in content

    def test_package_name_to_module_name_handles_separators(self):
        assert LeanRepo.package_name_to_module_name('lean4-web_app') == 'Lean4WebApp'

    @patch('leanup.repo.manager.shutil.move')
    @patch.object(LeanRepo, 'lake_build')
    @patch.object(LeanRepo, 'lake_cache_get')
    @patch.object(LeanRepo, 'lake_update')
    @patch.object(LeanRepo, 'lake')
    def test_create_math_project_runs_expected_stages(
        self,
        mock_lake,
        mock_lake_update,
        mock_lake_cache_get,
        mock_lake_build,
        mock_move,
    ):
        mock_lake.return_value = ('', '', 0)
        mock_lake_update.return_value = ('', '', 0)
        mock_lake_cache_get.return_value = ('', '', 0)
        mock_lake_build.return_value = ('', '', 0)
        progress_messages = []

        result = self.lean_repo.create_math_project(
            lean_version='4.14.0',
            project_name='lean4web',
            progress=progress_messages.append,
        )

        assert result is True
        assert progress_messages == [
            'INFO: Validate Lean version',
            'INFO: Prepare target directory',
            'INFO: Run lake new',
            'INFO: Write lean-toolchain',
            'INFO: Write lakefile.lean',
            'INFO: Run lake update',
            'INFO: Run lake exe cache get',
            'INFO: Run lake build',
            'INFO: Move project to target directory',
        ]
        mock_lake.assert_called_once_with(['new', 'lean4web', 'math.lean'])
        mock_lake_update.assert_called_once()
        mock_lake_cache_get.assert_called_once()
        mock_lake_build.assert_called_once()
        mock_move.assert_called_once()
