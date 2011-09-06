@echo off
set OSGEO4W_ROOT=..\..\OSGeo4W
PATH=%OSGEO4W_ROOT%\bin;%PATH%
for %%f in (%OSGEO4W_ROOT%\etc\ini\*.bat) do call %%f
@echo on

%OSGEO4W_ROOT%\bin\python.exe %1 %2 %3
