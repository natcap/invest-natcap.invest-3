import virtualenv, textwrap
output = virtualenv.create_bootstrap_script(textwrap.dedent("""
import os, subprocess
def after_install(options, home_dir):
    if sys.platform == 'win32':
        bin = 'Scripts'
    else:
        bin = 'bin'
    subprocess.call(['pip', 'install', 'numpy'])
    subprocess.call(['pip', 'install', 'scipy'])
    subprocess.call(['pip', 'install', 'nose'])
    subprocess.call(['pip', 'install', 'setuptools'])
"""))
print output
