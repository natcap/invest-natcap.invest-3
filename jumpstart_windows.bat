SET ENVDIR=invest_python_environment
DEL /S /Q build
DEL /S /Q %ENVDIR%
python bootstrap_invest_environment.py > setup_environment.py
python setup_environment.py --clear --system-site-packages %ENVDIR%
copy C:\Python27\Lib\distutils\distutils.cfg .\%ENVDIR%\Lib\distutils\distutils.cfg
%ENVDIR%\Scripts\python setup.py install

%ENVDIR%\Scripts\python invest_monthly_water_yield.py
