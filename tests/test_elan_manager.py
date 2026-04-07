import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from leanup.repo.elan import ElanManager
from leanup.const import OS_TYPE


class TestElanManager:
    """Test cases for ElanManager class"""
    
    def test_init(self, mock_elan_home):
        """Test ElanManager initialization"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            assert manager.elan_home == mock_elan_home
            assert manager.elan_bin_dir == mock_elan_home / 'bin'
    
    def test_get_elan_executable_exists(self, mock_elan_home):
        """Test getting elan executable when it exists"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            # Create mock elan executable
            elan_exe = 'elan.exe' if OS_TYPE == 'Windows' else 'elan'
            elan_path = mock_elan_home / 'bin' / elan_exe
            elan_path.touch()
            
            result = manager.get_elan_executable()
            assert result == elan_path
    
    def test_get_elan_executable_in_path(self, mock_elan_home):
        """Test getting elan executable from PATH"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            with patch('shutil.which', return_value='/usr/bin/elan'):
                result = manager.get_elan_executable()
                assert result == Path('/usr/bin/elan')
    
    def test_get_elan_executable_not_found(self, mock_elan_home):
        """Test getting elan executable when not found"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            with patch('shutil.which', return_value=None):
                result = manager.get_elan_executable()
                assert result is None
    
    def test_is_elan_installed_true(self, mock_elan_home):
        """Test elan installation check when installed"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            with patch.object(manager, 'get_elan_executable', return_value=Path('/usr/bin/elan')):
                assert manager.is_elan_installed() is True
    
    def test_is_elan_installed_false(self, mock_elan_home):
        """Test elan installation check when not installed"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            with patch.object(manager, 'get_elan_executable', return_value=None):
                assert manager.is_elan_installed() is False
    
    @patch('leanup.repo.elan.execute_command')
    def test_get_elan_version_success(self, mock_execute, mock_elan_home):
        """Test getting elan version successfully"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            mock_execute.return_value = ('elan 3.0.0', '', 0)
            
            with patch.object(manager, 'get_elan_executable', return_value=Path('/usr/bin/elan')):
                version = manager.get_elan_version()
                assert version == '3.0.0'
    
    @patch('leanup.repo.elan.execute_command')
    def test_get_elan_version_failure(self, mock_execute, mock_elan_home):
        """Test getting elan version when command fails"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            mock_execute.return_value = ('', 'error', 1)
            
            with patch.object(manager, 'get_elan_executable', return_value=Path('/usr/bin/elan')):
                version = manager.get_elan_version()
                assert version is None
    
    @patch('leanup.repo.elan.requests.get')
    def test_download_installer_success(self, mock_get, mock_elan_home, temp_dir):
        """Test successful installer download"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.iter_content.return_value = [b'script content']
            mock_get.return_value = mock_response
            
            target_path = temp_dir / 'installer.sh'
            result = manager.download('http://example.com/script.sh', target_path)
            
            assert result is True
            assert target_path.exists()

    def test_install_lean_skips_when_version_already_installed(self, mock_elan_home):
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()

            with patch.object(
                manager,
                'get_installed_toolchains',
                return_value=['leanprover/lean4:v4.22.0', 'stable'],
            ), patch.object(manager, 'proxy_elan_command') as mock_proxy:
                assert manager.install_lean('v4.22.0') is True
                mock_proxy.assert_not_called()

    def test_install_lean_installs_when_version_missing(self, mock_elan_home):
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()

            with patch.object(manager, 'get_installed_toolchains', return_value=[]), \
                 patch.object(manager, 'proxy_elan_command', return_value=0) as mock_proxy:
                assert manager.install_lean('v4.22.0') is True
                mock_proxy.assert_called_once_with(['toolchain', 'install', 'v4.22.0'])
    
    @patch('subprocess.run')
    @pytest.mark.skipif(OS_TYPE == 'Windows', reason="Windows path separator issue")
    def test_proxy_elan_command_success(self, mock_run, mock_elan_home):
        """Test successful elan command proxy"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            mock_run.return_value.returncode = 0
            
            with patch.object(manager, 'get_elan_executable', return_value=Path('/usr/bin/elan')):
                result = manager.proxy_elan_command(['--version'])
                assert result == 0
                mock_run.assert_called_once_with(['/usr/bin/elan', '--version'], check=False)
    
    @pytest.mark.skipif(OS_TYPE == 'Windows', reason="Windows path separator issue")
    def test_get_status_info_installed(self, mock_elan_home):
        """Test getting status info when elan is installed"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            with patch.object(manager, 'is_elan_installed', return_value=True), \
                 patch.object(manager, 'get_elan_version', return_value='3.0.0'), \
                 patch.object(manager, 'get_elan_executable', return_value=Path('/usr/bin/elan')), \
                 patch.object(manager, 'get_installed_toolchains', return_value=['stable']):
                
                info = manager.get_status_info()
                assert info['installed'] is True
                assert info['version'] == '3.0.0'
                assert info['executable'] == '/usr/bin/elan'
                assert info['toolchains'] == ['stable']
    
    def test_get_status_info_not_installed(self, mock_elan_home):
        """Test getting status info when elan is not installed"""
        with patch.dict(os.environ, {'ELAN_HOME': str(mock_elan_home)}):
            manager = ElanManager()
            
            with patch.object(manager, 'is_elan_installed', return_value=False):
                info = manager.get_status_info()
                assert info['installed'] is False
                assert info['version'] is None
                assert info['executable'] is None
                assert info['toolchains'] == []
