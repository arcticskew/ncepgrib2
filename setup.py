import setuptools
from distutils.core import setup, Extension
import os, glob, sys
from os import environ
if sys.version_info[0] < 3:
    import ConfigParser as configparser
else:
    import configparser

class _ConfigParser(configparser.ConfigParser):
    def getq(self, s, k, fallback):
        try:
            return self.get(s, k)
        except:
            return fallback

# build time dependancy
try:
    from Cython.Distutils import build_ext
    redtoreg_pyx = 'redtoreg.pyx'
    g2clib_pyx  = 'g2clib.pyx'
except ImportError:
    from distutils.command.build_ext import build_ext
    redtoreg_pyx = 'redtoreg.c'
    g2clib_pyx  = 'g2clib.c'

class NumpyBuildExtCommand(build_ext):
    """
    build_ext command for use when numpy headers are needed.
    from https://stackoverflow.com/questions/2379898/
    and https://stackoverflow.com/questions/48283503/
    """
    def run(self):
        self.distribution.fetch_build_eggs(['numpy'])
        import numpy
        self.include_dirs.append(numpy.get_include())
        build_ext.run(self)

cmdclass = {'build_ext': NumpyBuildExtCommand}

setup_cfg = environ.get('SETUPCFG', 'setup.cfg')
config = _ConfigParser()
# contents of setup.cfg will override env vars.
if os.path.exists(setup_cfg):
    sys.stdout.write('reading from setup.cfg...')
    config.read(setup_cfg)
packages_to_install = config.getq(
    "install_options", "packages_to_install", ["pygrib","ncepgrib2"])
jasper_dir = config.getq(
    "directories", "jasper_dir", environ.get('JASPER_DIR'))
jasper_libdir = config.getq(
    "directories", "jasper_libdir", environ.get('JASPER_LIBDIR'))
jasper_incdir = config.getq(
    "directories", "jasper_incdir", environ.get('JASPER_INCDIR'))
png_dir = config.getq(
    "directories", "png_dir", environ.get('PNG_DIR'))
png_libdir = config.getq(
    "directories", "png_libdir", environ.get('PNG_LIBDIR'))
png_incdir = config.getq(
    "directories", "png_incdir", environ.get('PNG_INCDIR'))
zlib_dir = config.getq(
    "directories", "zlib_dir", environ.get('ZLIB_DIR'))
zlib_libdir = config.getq(
    "directories", "zlib_libdir", environ.get('ZLIB_LIBDIR'))
zlib_incdir = config.getq(
    "directories", "zlib_incdir", environ.get('ZLIB_INCDIR'))
# where to install man pages?
man_dir = config.getq(
    "directories", "man_dir", environ.get('MAN_DIR'))

libraries=[]
libdirs=[]
incdirs=[]

if jasper_dir is not None or jasper_libdir is not None:
    libraries.append("jasper")
if jasper_libdir is None and jasper_dir is not None:
    libdirs.append(os.path.join(jasper_dir,'lib'))
    libdirs.append(os.path.join(jasper_dir,'lib64'))
if jasper_incdir is None and jasper_dir is not None:
    incdirs.append(os.path.join(jasper_dir,'include'))
    incdirs.append(os.path.join(jasper_dir,'include/jasper'))

if png_dir is not None or png_libdir is not None:
    libraries.append("png")
if png_libdir is None and png_dir is not None:
    libdirs.append(os.path.join(png_dir,'lib'))
    libdirs.append(os.path.join(png_dir,'lib64'))
if png_incdir is None and png_dir is not None:
    incdirs.append(os.path.join(png_dir,'include'))

if zlib_dir is not None or zlib_libdir is not None:
    libraries.append("z")
if zlib_libdir is None and zlib_dir is not None:
    libdirs.append(os.path.join(zlib_dir,'lib'))
    libdirs.append(os.path.join(zlib_dir,'lib64'))
if zlib_incdir is None and zlib_dir is not None:
    incdirs.append(os.path.join(zlib_dir,'include'))

g2clib_deps = glob.glob('g2clib_src/*.c')
g2clib_deps.append(g2clib_pyx)
incdirs.append("g2clib_src")
macros=[]

# if jasper or openjpeg lib not available...
if 'jasper' not in libraries and 'openjpeg' not in libraries:
    g2clib_deps.remove(os.path.join('g2clib_src', 'jpcpack.c'))
    g2clib_deps.remove(os.path.join('g2clib_src', 'jpcunpack.c'))
else:
    macros.append(('USE_JPEG2000',1))
# if png lib not available...
if 'png' not in libraries:
    g2clib_deps.remove(os.path.join('g2clib_src', 'pngpack.c'))
    g2clib_deps.remove(os.path.join('g2clib_src', 'pngunpack.c'))
else:
    macros.append(('USE_PNG',1))

if hasattr(sys,'maxsize'):
    if sys.maxsize > 2**31-1: macros.append(('__64BIT__',1))
else:
    if sys.maxint > 2**31-1: macros.append(('__64BIT__',1))

runtime_libdirs = libdirs if os.name != "nt" else None
g2clibext = Extension("g2clib",g2clib_deps,include_dirs=incdirs,\
            library_dirs=libdirs,libraries=libraries,runtime_library_dirs=runtime_libdirs,
            define_macros=macros)
redtoregext =\
Extension("redtoreg",[redtoreg_pyx])

# man pages installed in man_dir/man1
if man_dir is not None:
    manpages = glob.glob(os.path.join('man','*.1'))
    data_files = [(os.path.join(man_dir,'man1'), manpages)]
# if man_dir not set, man pages not installed
else:
    data_files = None

install_scripts = []
install_ext_modules = []
install_py_modules = []

if "ncepgrib2" in packages_to_install:
    install_ext_modules += [g2clibext,redtoregext]
    install_py_modules += ["ncepgrib2"]

# Make sure only 1 instance of redtoregext exists in install_ext_modules
install_ext_modules = list(set(install_ext_modules))

# Import README.md as PyPi long_description
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

install_requires = ["numpy"]

# pyproj is a runtime dependency
try:
    import pyproj
except ImportError:
    try:
        from mpl_toolkits.basemap import pyproj
    except:
        install_requires.append("pyproj")

setup(name = "ncepgrib2",
      version = "2.1",
      description       = "Python module for reading/writing GRIB files using NCEP g2c",
      author            = "",
      author_email      = "",
      url               = "",
      classifiers       = ["Development Status :: 4 - Beta",
                           "Programming Language :: Python :: 2",
                           "Programming Language :: Python :: 2.6",
                           "Programming Language :: Python :: 2.7",
                           "Programming Language :: Python :: 3",
                           "Programming Language :: Python :: 3.3",
                           "Programming Language :: Python :: 3.4",
                           "Programming Language :: Python :: 3.5",
                           "Programming Language :: Python :: 3.6",
                           "Intended Audience :: Science/Research",
                           "License :: OSI Approved",
                           "Topic :: Software Development :: Libraries :: Python Modules"],
      cmdclass          = cmdclass,
      scripts           = install_scripts,
      ext_modules       = install_ext_modules,
      py_modules        = install_py_modules,
      data_files        = data_files,
      long_description  = long_description,
      long_description_content_type = 'text/markdown',
      install_requires  = install_requires)
