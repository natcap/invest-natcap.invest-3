@echo off
SET OSGEO4W_ROOT=Z:\local\workspace\invest-natcap.invest-3\OSGeo4W
call %OSGEO4W_ROOT%\bin\o4w_env.bat
call %OSGEO4W_ROOT%\apps\grass\grass-6.4.2RC2\etc\env.bat
"%WINGISBASE%"\etc\init.bat %*
