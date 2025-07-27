"""
Elan 工具链管理器
处理 elan 的安装、检测和命令代理
"""

import os
import requests
import toml  # 添加这一行
from pathlib import Path
from typing import Optional, List, Dict
import subprocess
import shutil
from loguru import logger

from .const import OS_TYPE, LEANUP_CACHE_DIR
from .utils.executor import CommandExecutor


class ElanManager:
    """Elan 工具链管理器"""

    def __init__(self):
        self.executor = CommandExecutor()
        self.elan_home = Path(os.environ.get('ELAN_HOME', Path.home() / '.elan'))
        self.elan_bin_dir = self.elan_home / 'bin'
        
    def get_elan_executable(self) -> Optional[Path]:
        """获取 elan 可执行文件路径"""
        elan_exe = 'elan.exe' if OS_TYPE == 'Windows' else 'elan'
        elan_path = self.elan_bin_dir / elan_exe
        
        if elan_path.exists() and elan_path.is_file():
            return elan_path
        
        # 尝试在 PATH 中查找
        elan_in_path = shutil.which('elan')
        if elan_in_path:
            return Path(elan_in_path)
            
        return None
    
    def is_elan_installed(self) -> bool:
        """检查 elan 是否已安装"""
        return self.get_elan_executable() is not None
    
    def get_elan_version(self) -> Optional[str]:
        """获取已安装的 elan 版本"""
        elan_path = self.get_elan_executable()
        if not elan_path:
            return None
            
        try:
            output, error, code = self.executor.execute([str(elan_path), '--version'])
            if code == 0:
                # 从输出中提取版本号
                for line in output.strip().split('\n'):
                    if 'elan' in line.lower():
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if 'elan' in part.lower() and i + 1 < len(parts):
                                return parts[i + 1]
                return output.strip().split('\n')[0]
            return None
        except Exception as e:
            logger.error(f"获取 elan 版本失败: {e}")
            return None
    
    def get_download_url(self, version: Optional[str] = None) -> str:
        """获取 elan 安装脚本的下载 URL"""
        if OS_TYPE == 'Windows':
            # Windows 使用官方 PowerShell 脚本
            return "https://elan.lean-lang.org/elan-init.ps1"
        else:
            # Linux 和 macOS 使用官方 shell 脚本  
            return "https://elan.lean-lang.org/elan-init.sh"
    
    def download_installer(self, url: str, target_path: Path) -> bool:
        """下载 elan 安装程序"""
        try:
            logger.info(f"正在下载 elan 安装程序: {url}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 给安装脚本执行权限
            if OS_TYPE != 'Windows':
                target_path.chmod(0o755)
                
            logger.info(f"下载完成: {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"下载 elan 安装程序失败: {e}")
            return False
    
    def install_elan(self, version: Optional[str] = None, force: bool = False) -> bool:
        """安装 elan"""
        
        # 检查是否已安装
        if self.is_elan_installed() and not force:
            current_version = self.get_elan_version()
            logger.info(f"elan 已安装 (版本: {current_version})")
            if version is None or current_version == version:
                return True
            logger.info(f"正在安装指定版本: {version}")
        
        # 创建临时目录
        temp_dir = LEANUP_CACHE_DIR / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            download_url = self.get_download_url(version)
            
            if OS_TYPE == 'Windows':
                # Windows 使用 PowerShell 直接从网络运行脚本（官方推荐方式）
                logger.info("正在通过 PowerShell 安装 elan...")
                # 设置环境变量以进行非交互式安装
                env = os.environ.copy()
                env['ELAN_HOME'] = str(self.elan_home)
                
                # 根据官方文档的建议，使用 PowerShell 直接下载和执行
                script_content = f"""
                $env:ELAN_HOME = "{self.elan_home}"
                Invoke-WebRequest -Uri "https://elan.lean-lang.org/elan-init.ps1" -OutFile "elan-init.ps1"
                & .\\elan-init.ps1 -y
                Remove-Item "elan-init.ps1" -ErrorAction SilentlyContinue
                """
                
                cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', script_content]
                output, error, code = self.executor.execute(cmd, cwd=str(temp_dir))
                
                if code != 0:
                    logger.error(f"安装失败: {error}")
                    return False
                    
            else:
                # Linux/macOS 使用 shell 脚本安装
                installer_path = temp_dir / 'elan-init.sh'
                if not self.download_installer(download_url, installer_path):
                    return False
                
                logger.info("正在运行 elan 安装脚本...")
                # 设置环境变量以进行非交互式安装
                env = os.environ.copy()
                env['ELAN_HOME'] = str(self.elan_home)
                
                cmd = ['sh', str(installer_path), '-y']
                output, error, code = self.executor.execute(cmd)
                
                if code != 0:
                    logger.error(f"安装失败: {error}")
                    return False
            
            # 验证安装
            if self.is_elan_installed():
                installed_version = self.get_elan_version()
                logger.info(f"elan 安装成功! 版本: {installed_version}")
                return True
            else:
                logger.error("安装完成，但无法找到 elan 可执行文件")
                return False
                
        except Exception as e:
            logger.error(f"安装 elan 时发生错误: {e}")
            return False
        finally:
            # 清理临时文件
            try:
                if OS_TYPE != 'Windows' and 'installer_path' in locals() and installer_path.exists():
                    installer_path.unlink()
            except OSError:
                # 忽略文件删除错误
                pass
    
    def proxy_elan_command(self, args: List[str]) -> int:
        """代理执行 elan 命令"""
        elan_path = self.get_elan_executable()
        
        if not elan_path:
            logger.error("elan 未安装。请先运行 'leanup install' 安装 elan。")
            return 1
        
        # 构建完整命令
        cmd = [str(elan_path)] + args
        
        try:
            # 直接传递给 subprocess，保持交互性
            result = subprocess.run(cmd, check=False)
            return result.returncode
        except Exception as e:
            logger.error(f"执行 elan 命令失败: {e}")
            return 1
    
    def get_installed_toolchains(self) -> List[str]:
        """获取已安装的工具链列表"""
        elan_path = self.get_elan_executable()
        if not elan_path:
            return []
        
        try:
            output, error, code = self.executor.execute([str(elan_path), 'toolchain', 'list'])
            if code == 0:
                toolchains = []
                for line in output.strip().split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 移除状态标记（如 (default)）
                        toolchain = line.split()[0]
                        toolchains.append(toolchain)
                return toolchains
            return []
        except Exception as e:
            logger.error(f"获取工具链列表失败: {e}")
            return []
    
    def get_status_info(self) -> Dict[str, any]:
        """获取 elan 状态信息"""
        info = {
            'installed': self.is_elan_installed(),
            'version': None,
            'elan_home': str(self.elan_home),
            'executable': None,
            'toolchains': []
        }
        
        if info['installed']:
            info['version'] = self.get_elan_version()
            info['executable'] = str(self.get_elan_executable())
            info['toolchains'] = self.get_installed_toolchains()
        
        return info
    
    def get_default_toolchain(self) -> Optional[str]:
        """获取当前默认工具链"""
        settings_path = self.elan_home / 'settings.toml'
        if not settings_path.exists():
            return None
            
        try:
            settings = toml.load(settings_path)
            return settings.get('default_toolchain')
        except Exception as e:
            logger.error(f"读取默认工具链失败: {e}")
            return None
    
    def install_toolchain(self, toolchain: str, set_as_default: bool = False) -> bool:
        """安装特定工具链
        
        Args:
            toolchain: 要安装的工具链名称或版本
            set_as_default: 是否设置为默认工具链
            
        Returns:
            bool: 安装是否成功
        """
        elan_path = self.get_elan_executable()
        if not elan_path:
            logger.error("elan 未安装，请先运行 'leanup init' 初始化环境")
            return False
            
        try:
            # 安装工具链
            cmd = [str(elan_path), 'toolchain', 'install', toolchain]
            output, error, code = self.executor.execute(cmd)
            
            if code != 0:
                logger.error(f"安装工具链失败: {error}")
                return False
                
            # 如果需要，设置为默认工具链
            if set_as_default:
                cmd = [str(elan_path), 'default', toolchain]
                output, error, code = self.executor.execute(cmd)
                
                if code != 0:
                    logger.error(f"设置默认工具链失败: {error}")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"安装工具链时发生错误: {e}")
            return False
