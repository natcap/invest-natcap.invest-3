import subprocess

HG_CALL = 'hg log -r . --config ui.report_untrusted=False'

def invest_version():
    if get_tag_distance() == 0:
        return get_latest_tag()
    else:
        import invest_version
        return 'dev%s' % invest_version.version

def write_version_file(filepath):
    """Write the version number to the file designated by filepath.  Returns
    nothing."""
    comments = [
        'The version noted below is used throughout InVEST as a static version',
        'that differs only from build to build.  Its value is determined by ',
        'setup.py and is based off of the time and date of the last revision.',
        '',
        'This file is programmatically generated when invest_natcap is built. ',
    ]

    # Open the version file for writing
    fp = open(filepath, 'w')

    # Write the comments as comments to the file and write the version to the
    # file as well.
    for comment in comments:
        fp.write('# %s\n' % comment)
    fp.write('version = \'%s\'\n' % get_build_id())

    # Close the file.
    fp.close()

def get_build_id():
    cmd = HG_CALL + ' --template "{latesttagdistance}:{latesttag} [{node|short}]"'
    return run_command(cmd)

def get_tag_distance():
    cmd = HG_CALL + ' --template "{latesttagdistance}"'
    return int(run_command(cmd))

def get_latest_tag():
    cmd = HG_CALL + ' --template "{latesttag}"'

def run_command(cmd):
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.read()

