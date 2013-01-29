import virtualenv, textwrap
output = virtualenv.create_bootstrap_script(textwrap.dedent("""
import os, subprocess, sys
def after_install(options, home_dir):
    print("Home dir: ", home_dir)
    print("CWD: ", os.getcwd())
    if sys.platform == 'win32':
        bin = 'Scripts'
    else:
        bin = 'bin'
    subprocess.call([join(home_dir, bin, 'easy_install').replace(' ', '\ '),
                     'numpy'])
    subprocess.call([join(home_dir, bin, 'easy_install').replace(' ', '\ '),
                     'scipy'])
    subprocess.call([join(home_dir, bin, 'easy_install').replace(' ', '\ '),
                     'nose'])
    subprocess.call([join(home_dir, bin, 'easy_install').replace(' ', '\ '),
                     'setuptools'])
"""))
print output
