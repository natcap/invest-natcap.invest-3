#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Sphinx - Python documentation toolchain
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import os

try:
    sys.path.append(os.environ['WORKSPACE'])
except:
    pass

if __name__ == '__main__':
    from sphinx import main
    sys.exit(main(sys.argv))
