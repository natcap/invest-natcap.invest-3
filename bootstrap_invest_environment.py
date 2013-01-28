import virtualenv, textwrap
output = virtualenv.create_bootstrap_script(textwrap.dedent("""
import os, subprocess
def after_install(options, home_dir):
    if sys.platform == 'win32':
        bin = 'Scripts'
    else:
        bin = 'bin'
    subprocess.call(['pip', 'numpy'])
    subprocess.call(['pip', 'scipy'])
    subprocess.call(['pip', 'nose'])
    subprocess.call(['pip', 'setuptools'])
"""))
print output
