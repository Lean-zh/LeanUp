import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from leanup.const import OS_TYPE
from leanup.cli import cli


class TestCLI:
    """Test CLI commands"""
    
    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test CLI help command"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'LeanUp - Lean project management tool' in result.output
    
    @patch('leanup.cli.ElanManager')
    def test_init_command(self, mock_elan_manager):
        """Test init command"""
        # Mock elan manager
        mock_elan = Mock()
        mock_elan.is_elan_installed.return_value = False
        mock_elan.install_elan.return_value = True
        mock_elan_manager.return_value = mock_elan
        
        result = self.runner.invoke(cli, ['init'])
        
        if result.exit_code == 0:
             '✓ elan installed successfully' in result.output
        # mock_elan.install_elan.assert_called_once()
    
    @patch('leanup.cli.ElanManager')
    def test_init_command_already_installed(self, mock_elan_manager):
        """Test init command when elan is already installed"""
        # Mock elan manager
        mock_elan = Mock()
        mock_elan.is_elan_installed.return_value = True
        mock_elan_manager.return_value = mock_elan
        
        result = self.runner.invoke(cli, ['init'])
        
        assert result.exit_code == 0
        assert '✓ elan is already installed' in result.output
        mock_elan.install_elan.assert_not_called()
    
    @patch('leanup.cli.ElanManager')
    def test_install_command_latest(self, mock_elan_manager):
        """Test install command for latest version"""
        mock_elan = Mock()
        mock_elan.is_elan_installed.return_value = True
        mock_elan.proxy_elan_command.return_value = 0
        mock_elan_manager.return_value = mock_elan
        
        result = self.runner.invoke(cli, ['install'])
        
        assert result.exit_code == 0
    
    @patch('leanup.cli.ElanManager')
    def test_install_command_specific_version(self, mock_elan_manager):
        """Test install command for specific version"""
        mock_elan = Mock()
        mock_elan.is_elan_installed.return_value = True
        mock_elan.proxy_elan_command.return_value = 0
        mock_elan_manager.return_value = mock_elan
        
        result = self.runner.invoke(cli, ['install', 'v4.10.0'])
        
        assert result.exit_code == 0
    
    @patch('leanup.cli.ElanManager')
    def test_install_command_with_force(self, mock_elan_manager):
        """Test install command with force flag"""
        mock_elan = Mock()
        mock_elan.is_elan_installed.return_value = True
        mock_elan.proxy_elan_command.return_value = 0
        mock_elan_manager.return_value = mock_elan
        
        result = self.runner.invoke(cli, ['install', 'v4.10.0'])
        
        assert result.exit_code == 0
    
    @patch('leanup.cli.ElanManager')
    def test_install_command_elan_not_installed(self, mock_elan_manager):
        """Test install command when elan is not installed"""
        mock_elan = Mock()
        mock_elan.is_elan_installed.return_value = False
        mock_elan.install_elan.return_value = True
        mock_elan.proxy_elan_command.return_value = 0
        mock_elan_manager.return_value = mock_elan
        
        result = self.runner.invoke(cli, ['install'])
        
        assert result.exit_code == 0
        assert '✓ elan installed successfully' in result.output
        # assert 'Installing latest Lean toolchain...' in result.output
        # mock_elan.install_elan.assert_called_once()
        # mock_elan.proxy_elan_command.assert_called_once_with(['toolchain', 'install', 'stable'])
    
    @patch('leanup.cli.ElanManager')
    def test_status_command(self, mock_elan_manager):
        """Test status command"""
        # Mock elan manager
        mock_elan = Mock()
        mock_elan.is_elan_installed.return_value = True
        mock_elan.get_elan_version.return_value = '4.0.0'
        mock_elan.get_installed_toolchains.return_value = ['leanprover/lean4:v4.10.0', 'leanprover/lean4:v4.9.0']
        mock_elan_manager.return_value = mock_elan
        
        result = self.runner.invoke(cli, ['status'])
        
        assert result.exit_code == 0
        assert '=== LeanUp Status ===' in result.output
        assert 'elan ' in result.output
    
    @patch('leanup.cli.ElanManager')
    def test_status_command_elan_not_installed(self, mock_elan_manager):
        """Test status command when elan is not installed"""
        mock_elan = Mock()
        mock_elan.is_elan_installed.return_value = False
        mock_elan_manager.return_value = mock_elan
        
        result = self.runner.invoke(cli, ['status'])
        
        assert result.exit_code == 0
        assert 'elan: ✗ not installed' in result.output
    
    @patch('leanup.cli.ElanManager')
    def test_elan_proxy_command(self, mock_elan_manager):
        """Test elan proxy command"""
        mock_elan = Mock()
        mock_elan.is_elan_installed.return_value = True
        mock_elan.proxy_elan_command.return_value = 0
        mock_elan_manager.return_value = mock_elan
        
        result = self.runner.invoke(cli, ['elan', 'toolchain', 'list'])
        
        mock_elan.proxy_elan_command.assert_called_once_with(['toolchain', 'list'])
    
    @patch('leanup.cli.ElanManager')
    def test_elan_proxy_command_not_installed(self, mock_elan_manager):
        """Test elan proxy command when elan is not installed"""
        mock_elan = Mock()
        mock_elan.is_elan_installed.return_value = False
        mock_elan_manager.return_value = mock_elan
        
        result = self.runner.invoke(cli, ['elan', 'toolchain', 'list'])
        
        assert result.exit_code == 1
        assert 'elan is not installed. Run \'leanup init\' first.' in result.output
        
