import click
import sys
import os
import toml
from pathlib import Path
from loguru import logger
from .elan_manager import ElanManager
from .const import OS_TYPE


# 配置 loguru
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(verbose):
    """LeanUp - Lean Environment Management Tool
    
    A Python tool for managing Lean mathematical proof language environments.
    """
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


@main.command()
@click.option('--force', '-f', is_flag=True, help='Force reinstall even if elan exists')
@click.option('--no-modify-path', is_flag=True, help='Do not modify shell config files')
def init(force, no_modify_path):
    """Initialize Lean environment with elan toolchain manager
    
    This command will:
    1. Install the latest stable version of elan
    2. Create .leanup directory for preferences
    3. Configure environment variables in shell config files
    
    Examples:
        leanup init              # Initialize environment
        leanup init --force      # Force reinstall
        leanup init --no-modify-path  # Don't modify shell config files
    """
    manager = ElanManager()
    
    click.echo(f"Initializing Lean environment for {OS_TYPE}...")
    
    # 1. 安装最新稳定版 elan
    success = manager.install_elan(force=force)
    
    if not success:
        click.echo("elan installation failed!")
        sys.exit(1)
    
    # 2. 创建 .leanup 目录和偏好设置文件
    leanup_dir = Path.home() / '.leanup'
    leanup_dir.mkdir(exist_ok=True)
    
    # 创建偏好设置 toml 文件
    config_path = leanup_dir / 'config.toml'
    if not config_path.exists() or force:
        config = {
            'elan': {
                'home': str(manager.elan_home),
                'default_toolchain': 'stable'
            },
            'preferences': {
                'auto_update_check': True,
                'telemetry_enabled': False
            }
        }
        
        with open(config_path, 'w') as f:
            toml.dump(config, f)
        
        click.echo(f"Created configuration file: {config_path}")
    
    # 3. 配置环境变量（如果用户没有禁用）
    if not no_modify_path and OS_TYPE != 'Windows':
        modified = False
        
        # 检查并更新 .bashrc
        bashrc_path = Path.home() / '.bashrc'
        if bashrc_path.exists():
            modified |= _update_shell_config(bashrc_path, manager.elan_bin_dir)
        
        # 检查并更新 .zshrc
        zshrc_path = Path.home() / '.zshrc'
        if zshrc_path.exists():
            modified |= _update_shell_config(zshrc_path, manager.elan_bin_dir)
        
        if modified:
            click.echo("\nEnvironment variables configured in shell config files.")
            click.echo("Please restart your terminal or run the following command to apply changes:")
            click.echo("   source ~/.bashrc  # or source ~/.zshrc")
    
    # 显示安装信息
    info = manager.get_status_info()
    click.echo("\nelan installation successful!")
    click.echo(f"Installation location: {info['executable']}")
    click.echo(f"ELAN_HOME: {info['elan_home']}")
    click.echo(f"Version: {info['version']}")
    
    # 提示下一步操作
    click.echo("\nYou can now use the following commands:")
    click.echo("   leanup elan --help      # Show elan help")
    click.echo("   leanup status           # Check status")
    click.echo("   leanup elan toolchain install stable  # Install stable toolchain")

@main.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_context
def elan(ctx):
    """Proxy elan commands
    
    Pass all arguments directly to the elan tool. This allows you to use leanup elan just like native elan.
    
    Examples:
        leanup elan --help                    # Show elan help
        leanup elan toolchain list            # List installed toolchains
        leanup elan toolchain install stable  # Install stable toolchain
        leanup elan default stable            # Set default toolchain
        leanup elan update                    # Update toolchains
    """
    manager = ElanManager()
    
    # 传递所有额外参数给 elan
    exit_code = manager.proxy_elan_command(ctx.args)
    sys.exit(exit_code)


@main.command()
def status():
    """Show LeanUp and elan status information"""
    manager = ElanManager()
    info = manager.get_status_info()
    
    click.echo("LeanUp Status Information")
    click.echo("=" * 50)
    
    click.echo(f"Operating System: {OS_TYPE}")
    
    # 检查 .leanup 目录
    leanup_dir = Path.home() / '.leanup'
    if leanup_dir.exists():
        click.echo(f"LeanUp Config: {leanup_dir / 'config.toml'}")
    else:
        click.echo("LeanUp Config: Not initialized (run 'leanup init')")
    
    if info['installed']:
        click.echo("elan Status: Installed")
        click.echo(f"Version: {info['version']}")
        click.echo(f"Executable: {info['executable']}")
        click.echo(f"ELAN_HOME: {info['elan_home']}")
        
        toolchains = info['toolchains']
        if toolchains:
            click.echo(f"Installed Toolchains ({len(toolchains)}):")
            for toolchain in toolchains:
                click.echo(f"   • {toolchain}")
        else:
            click.echo("Installed Toolchains: None")
            click.echo("Tip: Run 'leanup elan toolchain install stable' to install stable toolchain")
    else:
        click.echo("elan Status: Not Installed")
        click.echo("Tip: Run 'leanup init' to initialize the environment")


@main.command()
def version():
    """Show LeanUp version information"""
    from . import __version__
    click.echo(f"LeanUp Version: {__version__}")


# 保留原有的 repo 组以保持向后兼容
@main.group()
def repo():
    """Manage Lean repository installations (experimental feature)"""
    pass


def _update_shell_config(config_path, bin_dir):
    """更新 shell 配置文件，添加 elan bin 目录到 PATH
    
    Args:
        config_path: shell 配置文件路径
        bin_dir: elan bin 目录路径
        
    Returns:
        bool: 是否修改了配置文件
    """
    with open(config_path, 'r') as f:
        content = f.read()
    
    # 检查是否已经配置了 PATH
    path_str = f'export PATH="{bin_dir}:$PATH"'
    if path_str in content:
        return False
    
    # 添加到文件末尾
    with open(config_path, 'a') as f:
        f.write(f"\n# Added by LeanUp\n{path_str}\n")
    
    return True


@main.command()
@click.argument('toolchain', required=False)
@click.option('--force', '-f', is_flag=True, help='Force reinstall even if already installed')
@click.option('--no-default', is_flag=True, help='Do not set as default toolchain')
def install(toolchain, force, no_default):
    """Install specific Lean toolchain
    
    This command installs a specific Lean toolchain using elan.
    If no toolchain is specified, it will install the stable version.
    
    Examples:
        leanup install                # Install stable toolchain
        leanup install leanprover/lean4:stable  # Install specific toolchain
        leanup install --no-default   # Install without setting as default
    """
    manager = ElanManager()
    
    # 检查 elan 是否已安装，如果未安装则自动安装
    if not manager.is_elan_installed():
        click.echo("elan 未安装，正在自动安装...")
        success = manager.install_elan(force=force)
        if not success:
            click.echo("elan 安装失败！无法继续安装工具链。")
            sys.exit(1)
        click.echo("elan 安装成功！继续安装工具链...")
    
    # 如果未指定工具链，默认使用 stable
    if not toolchain:
        toolchain = "stable"
        click.echo(f"未指定工具链，将安装默认的 stable 版本")
    
    # 检查是否有已安装的工具链
    existing_toolchains = manager.get_installed_toolchains()
    default_toolchain = manager.get_default_toolchain()
    
    # 确定是否设置为默认工具链
    set_as_default = False
    if not no_default:
        # 如果是首次安装工具链或强制安装，则设置为默认
        if not existing_toolchains or force:
            set_as_default = True
        # 如果当前没有默认工具链，也设置为默认
        elif not default_toolchain:
            set_as_default = True
    
    click.echo(f"正在安装工具链: {toolchain}")
    success = manager.install_toolchain(toolchain, set_as_default)
    
    if success:
        if set_as_default:
            click.echo(f"工具链 {toolchain} 安装成功并设置为默认工具链")
        else:
            click.echo(f"工具链 {toolchain} 安装成功")
            
        # 显示当前状态
        info = manager.get_status_info()
        if info['toolchains']:
            click.echo("\n已安装的工具链:")
            for tc in info['toolchains']:
                if default_toolchain and tc == default_toolchain:
                    click.echo(f"   • {tc} (default)")
                else:
                    click.echo(f"   • {tc}")
    else:
        click.echo(f"工具链 {toolchain} 安装失败")
        sys.exit(1)


@main.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.pass_context
def elan(ctx):
    """Proxy elan commands
    
    Pass all arguments directly to the elan tool. This allows you to use leanup elan just like native elan.
    
    Examples:
        leanup elan --help                    # Show elan help
        leanup elan toolchain list            # List installed toolchains
        leanup elan toolchain install stable  # Install stable toolchain
        leanup elan default stable            # Set default toolchain
        leanup elan update                    # Update toolchains
    """
    manager = ElanManager()
    
    # 传递所有额外参数给 elan
    exit_code = manager.proxy_elan_command(ctx.args)
    sys.exit(exit_code)


@main.command()
def status():
    """Show LeanUp and elan status information"""
    manager = ElanManager()
    info = manager.get_status_info()
    
    click.echo("LeanUp Status Information")
    click.echo("=" * 50)
    
    click.echo(f"Operating System: {OS_TYPE}")
    
    # 检查 .leanup 目录
    leanup_dir = Path.home() / '.leanup'
    if leanup_dir.exists():
        click.echo(f"LeanUp Config: {leanup_dir / 'config.toml'}")
    else:
        click.echo("LeanUp Config: Not initialized (run 'leanup init')")
    
    if info['installed']:
        click.echo("elan Status: Installed")
        click.echo(f"Version: {info['version']}")
        click.echo(f"Executable: {info['executable']}")
        click.echo(f"ELAN_HOME: {info['elan_home']}")
        
        toolchains = info['toolchains']
        if toolchains:
            click.echo(f"Installed Toolchains ({len(toolchains)}):")
            for toolchain in toolchains:
                click.echo(f"   • {toolchain}")
        else:
            click.echo("Installed Toolchains: None")
            click.echo("Tip: Run 'leanup elan toolchain install stable' to install stable toolchain")
    else:
        click.echo("elan Status: Not Installed")
        click.echo("Tip: Run 'leanup init' to initialize the environment")


@main.command()
def version():
    """Show LeanUp version information"""
    from . import __version__
    click.echo(f"LeanUp Version: {__version__}")


# 保留原有的 repo 组以保持向后兼容
@main.group()
def repo():
    """Manage Lean repository installations (experimental feature)"""
    pass


def _update_shell_config(config_path, bin_dir):
    """更新 shell 配置文件，添加 elan bin 目录到 PATH
    
    Args:
        config_path: shell 配置文件路径
        bin_dir: elan bin 目录路径
        
    Returns:
        bool: 是否修改了配置文件
    """
    with open(config_path, 'r') as f:
        content = f.read()
    
    # 检查是否已经配置了 PATH
    path_str = f'export PATH="{bin_dir}:$PATH"'
    if path_str in content:
        return False
    
    # 添加到文件末尾
    with open(config_path, 'a') as f:
        f.write(f"\n# Added by LeanUp\n{path_str}\n")
    
    return True


if __name__ == '__main__':
    main()

