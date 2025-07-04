from paver.easy import *  # for sh()


@task
def test():
    """Run unit tests."""
    import unittest
    import tests
    suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
    unittest.TextTestRunner().run(suite)


@task
def revbuild():
    """Increment the build number."""
    import procgame
    version_info = procgame.__version_info__
    version_info = version_info[:-1] + (int(version_info[-1]) + 1,)
    vfile = open('./procgame/_version.py', 'w')
    vfile.write('# Generated by: paver revbuild\n')
    vfile.write('__version_info__ = %s\n' % (repr(version_info)))
    vfile.close()
