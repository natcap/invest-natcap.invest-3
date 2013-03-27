setlocal EnableDelayedExpansion
CALL "C:\Program Files\Microsoft SDKs\Windows\v7.0\Bin\SetEnv.cmd" /x64 /release
set DISTUTILS_USE_SDK=1
C:\Users\rpsharp\AppData\Jenkins\tools\Python\Windows7-Python-2.7\Python27_x64\python.exe setup.py build_ext --compiler=msvc py2exe