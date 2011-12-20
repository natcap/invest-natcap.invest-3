#############################################################################
#
# MODULE:   	Grass Compilation
# AUTHOR(S):	Original author unknown - probably CERL
#		Markus Neteler - Germany/Italy - neteler@itc.it
#   	    	Justin Hickey - Thailand - jhickey@hpcc.nectec.or.th
#   	    	Huidae Cho - Korea - grass4u@gmail.com
#   	    	Eric G. Miller - egm2@jps.net
# PURPOSE:  	The source file for this Makefile is in src/CMD/head/head.in.
#		It is the top part of a file called make.rules which is used
#		for compiling all GRASS modules. This part of the file provides
#		make variables that are dependent on the results of the
#		configure script.
# COPYRIGHT:    (C) 2000 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#   	    	License (>=v2). Read the file COPYING that comes with GRASS
#   	    	for details.
#
#############################################################################

############################## Make Variables ###############################

CC                  = gcc
#FC                  = @F77@
CXX                 = c++
LEX                 = flex
YACC                = bison -y
PERL                = no
AR                  = ar
RANLIB              = ranlib
MKDIR               = mkdir -p
CHMOD               = chmod
INSTALL             = /bin/install -c 
INSTALL_DATA        = ${INSTALL} -m 644

prefix              = /c/OSGeo4W/apps/grass
exec_prefix         = ${prefix}
ARCH                = i686-pc-mingw32
UNIX_BIN            = /c/OSGeo4W/bin
INST_DIR            = ${prefix}/grass-6.4.2RC2

PLAT_OBJS           = 
STRIPFLAG           = 
CC_SEARCH_FLAGS     = 
LD_SEARCH_FLAGS     = 
LD_LIBRARY_PATH_VAR = PATH
LIB_RUNTIME_DIR     = $(ARCH_LIBDIR)

#static libs:
STLIB_LD            = ${AR} cr
STLIB_PREFIX        = lib
STLIB_SUFFIX        = .a

#shared libs
SHLIB_PREFIX        = lib
SHLIB_LD            = gcc -shared
SHLIB_LD_EXTRAS     = 
SHLIB_LD_FLAGS      = 
SHLIB_LD_LIBS       = ${LIBS}
SHLIB_CFLAGS        = 
SHLIB_SUFFIX        = .dll
EXE                 = .exe


# GRASS dirs
GRASS_HOME          = /c/OSGeo4W/apps/grass/grass-6.4.2RC2
RUN_GISBASE         = /c/OSGeo4W/apps/grass/grass-6.4.2RC2
RUN_GISRC           = ${ARCH_DISTDIR}/demolocation/.grassrc${GRASS_VERSION_MAJOR}${GRASS_VERSION_MINOR}

DEFAULT_DATABASE    =
DEFAULT_LOCATION    =

CPPFLAGS            =   -I/c/OSGeo4W/include
CFLAGS1             = -g -O2 
CXXFLAGS1           = -g -O2
INCLUDE_DIRS        =  -I/c/OSGeo4W/include

COMPILE_FLAGS       = $(CPPFLAGS) $(CFLAGS1) $(INCLUDE_DIRS)
COMPILE_FLAGS_CXX   = $(CPPFLAGS) $(CXXFLAGS1) $(INCLUDE_DIRS)
LINK_FLAGS          =   -Wl,--export-dynamic,--enable-runtime-pseudo-reloc  -L/c/OSGeo4W/lib -L/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/mswindows/osgeo4w/lib

DLLIB               = 
XCFLAGS             = 
XMINC               = 
XLIBPATH            = 
XLIB                =  
XTLIB               = 
XMLIB               = 
XEXTRALIBS          = 
USE_X11             = 

COMPATLIB           = 
CURSES              = -lcurses $(COMPATLIB)
USE_CURSES          = 1
MATHLIB             =  
XDRLIB              = -lxdr -liberty -lws2_32    -lz 
ICONVLIB            = -liconv
INTLLIB             = -lintl
SOCKLIB             = 

#ZLIB:
ZLIB                =    -lz 
ZLIBINCPATH         = 
ZLIBLIBPATH         = 

#DBM:
#DBMINCPATH          = @DBMINCPATH@
#DBMLIBPATH          = @DBMLIBPATH@
#DBMLIB              = @DBMLIB@
DBMIEXTRALIB        = 

#readline
READLINEINCPATH     = 
READLINELIBPATH     = 
READLINELIB         = 
HISTORYLIB          = 

#PostgreSQL:
PQINCPATH           = 
PQLIBPATH           = 
PQLIB               =  -lpq 

#MySQL:
MYSQLINCPATH        = 
MYSQLLIBPATH        = 
MYSQLLIB            = 
MYSQLDLIB            = 

#SQLite:
SQLITEINCPATH        = 
SQLITELIBPATH        = 
SQLITELIB            =  -lsqlite3 

#FFMPEG
FFMPEGINCPATH        = 
FFMPEGLIBPATH        = 
FFMPEGLIB            = 

#ODBC:
ODBCINC             = 
ODBCLIB             =  -lodbc32 

#Image formats:
PNGINC              = 
PNGLIB              =  -lpng  -lz  
USE_PNG             = 1

JPEGINCPATH         = 
JPEGLIBPATH         = 
JPEGLIB             =  -ljpeg 

TIFFINCPATH         = 
TIFFLIBPATH         = 
TIFFLIB             =  -ltiff 

#openGL files for NVIZ/r3.showdspf
OPENGLINC           = 
OPENGLWINC          = 
OPENGLLIB           =   -lopengl32 
OPENGLULIB          =   -lglu32 
OPENGLWM            = 
# USE_GLWM            = @USE_GLWM@
OPENGL_X11          = 
OPENGL_AQUA         = 
OPENGL_WINDOWS      = 1
USE_OPENGL          = 1

#tcl/tk stuff
TCLINCDIR           = 
TKINCDIR            = 
TCLTKLIBPATH        = 
TCLTKLIBS           =  -ltk85   -ltcl85 
TCLVERSION          = 8.5
MACOSX_ARCHS_TCLTK  = 

#FFTW:
FFTWINC             = 
FFTWLIB             =  -lfftw3 

#LAPACK/BLAS stuff for gmath lib:
BLASLIB             = 
BLASINC				= 
LAPACKLIB           = 
LAPACKINC			= 

#GDAL/OGR
GDALLIBS            = /c/OSGeo4W/lib/gdal_i.lib
GDALCFLAGS          = -I/c/OSGeo4W/include
USE_GDAL            = 1
USE_OGR             = 1

#GEOS
GEOSLIBS            = /c/OSGeo4W/lib/geos_c_i.lib -lgeos_c_i 
GEOSCFLAGS          = -I/c/OSGeo4W/include
USE_GEOS            = 1

#FreeType:
FTINC               =  -I/c/OSGeo4W/include/freetype2
FTLIB               =  -lfreetype 

#PROJ.4:
PROJINC             =  $(GDALCFLAGS)
PROJLIB             =  -lproj 
NAD2BIN             = /c/OSGeo4W/bin/nad2bin
PROJSHARE           = /c/OSGeo4W/share/proj

#OPENDWG:
OPENDWGINCPATH      = 
OPENDWGLIBPATH      = 
OPENDWGLIB          = 
USE_OPENDWG         = 

#cairo
CAIROINC            = 
CAIROLIB            = 
USE_CAIRO           = 

#Python
PYTHON              = python
PYTHONINC           = 
PYTHONCFLAGS        = 
PYTHONLDFLAGS       = 
SWIG                = @SWIG@
USE_PYTHON          = 
MACOSX_ARCHS_PYTHON = 

#wxWidgets
WXVERSION           = 
WXWIDGETSCXXFLAGS   = 
WXWIDGETSCPPFLAGS   = 
WXWIDGETSLIB        = 
USE_WXWIDGETS       = 
MACOSX_ARCHS_WXPYTHON = 

#regex
REGEXINCPATH        = 
REGEXLIBPATH        = 
REGEXLIB            =  -lregex 
USE_REGEX           = 1

#i18N
HAVE_NLS            = 1

#Large File Support (LFS)
USE_LARGEFILES      = 1

#BSD sockets
HAVE_SOCKET         = 

MINGW		    = yes
MACOSX_APP	    = 
MACOSX_ARCHS        = 
MACOSX_SDK          = 

# Cross compilation
CROSS_COMPILING =  
