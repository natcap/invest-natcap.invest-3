import subprocess
import imp
import os
import logging
import traceback

HG_CALL = 'hg log -r . --config ui.report_untrusted=False'

LOGGER = logging.getLogger('build_utils')

def invest_version(uri=None, force_new=False):
    """Get the version of InVEST by importing invest_natcap.invest_version and
    using the appropriate version string from that module.  If
    invest_natcap.invest_version cannot be found, it is programmatically
    generated and then reimported.

    NOTE: invest_natcap.invest_version should be generated and distributed with
    the invest_natcap package, or else we run the risk of causing invest_natcap
    programs to crash if the do not have CLI mercurial installed.

    Returns a python bytestring with the version identifier, as appropriate for
    the development version or the release version."""

    def get_file_name(uri):
        """This function gets the file's basename without the extension."""
        return os.path.splitext(os.path.basename(uri))[0]

    if uri == None:
        new_uri = os.path.join(os.path.abspath(os.path.dirname(__file__)),
            'invest_version.pyc')
    else:
        new_uri = uri

    LOGGER.debug('Getting the InVEST version for URI=%s' % uri)
    try:
        name = get_file_name(new_uri)
        new_uri_extension = os.path.splitext(new_uri)[1]
        if new_uri_extension == '.pyc':
            version_info = imp.load_compiled(name, new_uri)
        elif new_uri_extension == '.py':
            version_info = imp.load_source(name, new_uri)
        elif new_uri_extension == '.pyd':
            version_info = imp.load_dynamic(name, new_uri)
        else:
            raise IOError('Module %s must be importable by python' % new_uri)
#        print 'imported version'
        LOGGER.debug('Successfully imported version file')
        found_file = True
    except (ImportError, IOError, AttributeError, TypeError):
        # ImportError thrown when we can't import the target source
        # IOError thrown if the target source file does not exist on disk
        # AttributeError thrown in some odd cases
        # TypeError thrown when uri == None.
        # In any of these cases, try creating the version file and import
        # once again.
        LOGGER.debug('Unable to import version.  Creating a new file')
#        print "can't import version from %s" % new_uri
        found_file = False

    # We only want to write a new version file if the user wants to force the
    # file's creation, OR if the user specified a URI, but we can't find it.
    if force_new or (not found_file and uri != None):
        try:
            write_version_file(new_uri)
            name = get_file_name(new_uri)
            version_info = imp.load_source(name, new_uri)
            print 'Wrote a new version file'
        except ValueError as e:
            # Thrown when Mercurial is not found to be installed in the local
            # directory.  This is a band-aid fix for when we import InVEST from
            # within a distributed version of RIOS.
            # When this happens, return the exception as a string.
            return str(e)
    elif not found_file and uri == None:
        # If we have not found the version file and no URI is provided, we need
        # to get the version info from HG.
#        print 'getting version from hg'
        return get_version_from_hg()

    if version_info.release == 'None':
        return build_dev_id(version_info.build_id)
    else:
        return version_info.release

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

def build_dev_id(build_id=None):
    """This function builds the dev version string.  Returns a string."""
    if build_id == None:
        build_id = get_build_id()
    return 'dev%s' % build_id

def get_version_from_hg():
    """Get the version from mercurial.  If we're on a tag, return that.
    Otherwise, build the dev id and return that instead."""
    # TODO: Test that Hg exists before getting this information.
    if get_tag_distance() == 0:
        return get_latest_tag()
    else:
        return build_dev_id()

def get_build_id():
    """Call mercurial with a template argument to get the build ID.  Returns a
    python bytestring."""
    cmd = HG_CALL + ' --template "{latesttagdistance}:{latesttag} [{node|short}]"'
    return run_command(cmd)

def get_tag_distance():
    """Call mercurial with a template argument to get the distance to the latest
    tag.  Returns an int."""
    cmd = HG_CALL + ' --template "{latesttagdistance}"'
    return int(run_command(cmd))

def get_latest_tag():
    """Call mercurial with a template argument to get the latest tag.  Returns a
    python bytestring."""
    cmd = HG_CALL + ' --template "{latesttag}"'
    return run_command(cmd)

def run_command(cmd):
    """Run a subprocess.Popen command.  This function is intended for internal
    use only and ensures a certain degree of uniformity across the various
    subprocess calls made in this module.

    cmd - a python string to be executed in the shell.

    Returns a python bytestring of the output of the input command."""
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.read()

