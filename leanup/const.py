import platform

if platform.system() == 'Windows':
    OS_TYPE = 'Windows'
elif platform.system() == 'Darwin':
    OS_TYPE = 'MacOS'
elif platform.system() == 'Linux':
    OS_TYPE = 'Linux'
