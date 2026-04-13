from click.testing import CliRunner
from leanup.cli import cli


class TestCLI:
    """Test CLI commands"""

    def setup_method(self):
        """Setup test environment"""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help command"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "LeanUp - Lean project management tool" in result.output

    def test_cache_help_lists_top_level_commands(self):
        result = self.runner.invoke(cli, ["cache", "--help"])

        assert result.exit_code == 0
        assert "get" in result.output
        assert "pack" in result.output
        assert "serve" in result.output
        assert "create" in result.output
