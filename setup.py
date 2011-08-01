"""Installs pyprocgame using distutils.

Run:
    python setup.py install

to install this package.


If you want to develop using the source code directly and not install, you can run:

    python setup.py develop

    python setup.py develop --uninstall

See "Development Mode" at http://peak.telecommunity.com/DevCenter/setuptool for more.

"""
VERSION = '1.0.1'

from ez_setup import use_setuptools
use_setuptools()

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import sys
import os

setup(
    name='pyprocgame',
    version=VERSION,
    description='A Python-based pinball software development framework for use with P-ROC.',
    long_description=open('README.markdown').read(),
    license='MIT License',
    url='http://pyprocgame.pindev.org/',
    author='Adam Preble and Gerry Stellenberg',
    author_email='pyprocgame@pindev.org',
    packages=['procgame', 'procgame.dmd', 'procgame.game', 'procgame.highscore', 'procgame.modes', 'procgame.desktop', 'procgame.tools'],
    zip_safe = True, # False for non-zipped install
    # This works but it copies the files into /System/Library/Frameworks/Python.framework/Versions/2.6/tools -- not good
    # data_files = [
    #     ('tools', ['tools/dmdconvert.py', 'tools/dmdplayer.py']),
    # ],
    #scripts = [os.path.join('procgame', 'procgame')],
    entry_points = {
        'console_scripts': [
            'procgame = procgame.tools.cmd:main',
        ]
    },
    )
