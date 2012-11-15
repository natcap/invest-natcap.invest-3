import subprocess

HG_CALL = 'hg log -r . --config ui.report_untrusted=False'

def invest_version():
    import invest_version
    if invest_version.release == None:
        return 'dev%s' % invest_version.build_id
    else:
        return invest_version.release

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

    # Determine how to record the release version in the invest_version file.
    if get_tag_distance() == 0:
        release_version = get_latest_tag()
    else:
        release_version = None
    fp.write('release = \'%s\'\n' % release_version)

    # Even though we're also saving the release version, we also want to save
    # the build_id, as it can be very informative.
    fp.write('build_id = \'%s\'\n' % get_build_id())

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
    return run_command(cmd)

def run_command(cmd):
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.read()

