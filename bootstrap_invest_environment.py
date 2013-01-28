import virtualenv, textwrap
output = virtualenv.create_bootstrap_script(textwrap.dedent("""
import os, subprocess
def after_install(options, home_dir):
    if sys.platform == 'win32':
        bin = 'Scripts'
    else:
        bin = 'bin'
    subprocess.call([join('easy_install'),
                     'numpy'])
    subprocess.call([join('easy_install'),
                     'scipy'])
    subprocess.call([join('easy_install'),
                     'nose'])
    subprocess.call([join('easy_install'),
                     'setuptools'])
"""))
print output
