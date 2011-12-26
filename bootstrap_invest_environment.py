import virtualenv, textwrap
output = virtualenv.create_bootstrap_script(textwrap.dedent("""
import os, subprocess
def after_install(options, home_dir):
    if sys.platform == 'win32':
        bin = 'Scripts'
    else:
        bin = 'bin'
    subprocess.call([join(home_dir, 'bin', 'easy_install'),
                     'numpy'])
    subprocess.call([join(home_dir, 'bin', 'easy_install'),
                     'scipy'])
    subprocess.call([join(home_dir, 'bin', 'easy_install'),
                     'nose'])
"""))
print output
