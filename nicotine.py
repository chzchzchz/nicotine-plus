#!/usr/bin/env python
#
# Copyright (C) 2007 daelstorm. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Based on code from PySoulSeek and Nicotine

"""
Contact info:
daelstorm@gmail.com
"""
import platform, os
import sys
from pynicotine.logfacility import log

# Detect if we're running on Windows
win32 = sys.platform.startswith("win")
# Detect if we're running a packed exe created with py2exe
py2exe = False
if win32 and hasattr(sys, 'frozen'):
	py2exe = True

# Disable py2exe log feature by routing stdout/sterr to the special nul file
if win32 and py2exe:
	try:
		sys.stdout = open("nul", "w")
	except:
		print('Failed to close stdout (not so bad if you are using PyInstaller)')
	try:
		sys.stderr = open("nul", "w")
	except:
		print('Failed to close stderr (not so bad if you are using PyInstaller)')

from gettext import gettext as _

LOAD_PSYCO = False
if win32 and platform.architecture()[0] == "32bit":
	LOAD_PSYCO = True
else:
	try:
		if os.uname()[4] in ("i386", "i586", "i686") and platform.architecture()[0] == "32bit":
			LOAD_PSYCO = True
	except AttributeError, error:
		pass
if LOAD_PSYCO:
	try:
		import psyco
		psyco.profile()
	except ImportError:
		# Deprecated
		#log.addwarning(_("""Nicotine supports \"psyco\", an inline optimizer for python code, you can get it at http://sourceforge.net/projects/psyco/"""))
		pass



def checkenv():
	import sys, string
	ver = sys.version_info[0]*100+sys.version_info[1]*10+sys.version_info[2]
	if ver < 220:
		return _("""You're using an old version of Python interpreter (%s).
You should install Python 2.2.0 or newer.""") %(string.split(sys.version)[0])

	try:
		import pynicotine
	except ImportError,e:
		return _("""Can not find Nicotine modules. 
Perhaps they're installed in a directory which is not 
in an interpreter's module search path. 
(there could be a version mismatch between 
what version of python was used to build the Nicotine 
binary package and what you try to run Nicotine with.)""")

	# Windows stuff: detect GTK dll's path and add it to %PATH% if we're not running a py2exe package
	if win32 and not py2exe:
		# Fetchs gtk2 path from registry
		import _winreg
		try:
			k = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "Software\\GTK\\2.0")
		except EnvironmentError:
			print _("You must install the Gtk+ 2.x Runtime Environment to run this program")
			sys.exit(1)
		else:
			gtkdir = _winreg.QueryValueEx(k, "Path")
			msg = "GTK DLLs found at %s" % (gtkdir[0])
			log.add(msg)
			import os
			os.environ['PATH'] += ";%s/lib;%s/bin" % (gtkdir[0], gtkdir[0])

	if win32:
		try:
			import dbhash
		except:
			log.add(_("Warning: the Berkeley DB module, dbhash, could not be loaded."))

	innerexception = None
	try:
		if win32:
			try:
				import gtk
			except Exception, e:
				innerexception = e
				import pygtk
		else:
			import pygtk
			pygtk.require("2.0")
	except Exception, e:
		import sys
		msg = [_("Can not find required PyGTK. The current search path is \n%s") % (sys.path,),
		       "\n" + _("Exception: %s") % (e,)]
		if win32 and innerexception:
			msg.append("\n")
			msg.append(_("Second exception: %s") % (innerexception))
			msg.append("\n")
			msg.append("You have to solve either the first or the second exception.")
		return ''.join(msg)

	import gtk
	major, minor, micro = gtk.pygtk_version
	v = (major<<16) + (minor<< 8) + micro
	if v < ((1<<16) + (99<<8) + 16):
		return _("Your PyGTK is too old, upgrade to at least PyGTK 1.99.16")

	try:
		import GeoIP
	except ImportError:
		try:
			import _GeoIP
		except ImportError:
			msg = _("""Nicotine supports a country code blocker but that requires a (GPL'ed) library called GeoIP. You can find it here:
	C library:       http://www.maxmind.com/app/c
	Python bindings: http://www.maxmind.com/app/python
	(the python bindings require the C library)""")
			log.addwarning(msg)

	import pynicotine.upnp as upnp
	if not upnp.upnppossible:
		log.addwarning(_('Disabled UPnP support due to errors: %(errors)s') % {'errors':'. Also: '.join(upnp.miniupnpc_errors)})
	
	return None
def version():
	try:
		import pynicotine.utils
		print _("Nicotine-Plus version %s" % pynicotine.utils.version )
	except ImportError, error:
		print _("Cannot find the pynicotine.utils module.")

def usage():
	print _("""Nicotine-Plus is a Soulseek client.
Usage: nicotine [OPTION]...
  -c file, --config=file      Use non-default configuration file
  -p dir,  --plugins=dir      Use non-default directory for plugins
  -t,      --enable-trayicon
  -d,      --disable-trayicon
  -r,      --enable-rgba 
  -x,      --disable-rgba
  -v,      --version          Display version and exit
  -h,      --help             Display this help and exit
  -s,      --hidden           Start n+ hidden
  -b ip,   --bindip=ip        Bind sockets to the given IP (useful for VPN)

Please report any problems to our bugtracker:
http://www.nicotine-plus.org/newticket""")

def renameprocess(newname, debug = False):
	errors = []
	# Renaming ourselves for ps et al.
	try:
		import procname
		procname.setprocname(newname)
	except:
		errors.append("Failed procname module")
	# Renaming ourselves for pkill et al.
	try:
		import ctypes
		# Linux style
		libc = ctypes.CDLL('libc.so.6')
		libc.prctl(15, newname, 0, 0, 0)
	except:
		errors.append("Failed linux style")
	try:
		import dl
		# FreeBSD style
		libc = dl.open('/lib/libc.so.6')
		libc.call('setproctitle', newname + '\0')
		renamed = True
	except:
		errors.append("Failed FreeBSD style")
	if debug and errors:
		msg = [_("Errors occured while trying to change process name:")]
		for i in errors:
			msg.append("%s" % (i,))
		log.addwarning('\n'.join(msg))
def run():
	renameprocess('nicotine')
	import locale
	# Win32 hack to fix LANG and LC_ALL environnment variables with unix compliant language code
	# See pynicotine/libi18n.py
	if win32:
		import pynicotine.libi18n
		pynicotine.libi18n.fix_locale()
		del pynicotine.libi18n
	try:
		locale.setlocale(locale.LC_ALL, '')
	except:
		log.addwarning(_("Cannot set locale"))

	import gettext
	gettext.textdomain("nicotine")

	import sys, getopt, os.path
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hc:p:tdvswb:", ["help", "config=", "plugins=", "profile", "enable-trayicon", "disable-trayicon", "enable-rgba", "disable-rgba", "version", "hidden", "disable-webbrowser", "bindip="])
	except getopt.GetoptError:
		# print help information and exit:
		usage()
		sys.exit(2)

	if win32:
		try:
			mydir = os.path.join(os.environ['APPDATA'], 'nicotine')
		except KeyError:
			# windows 9x?
			mydir,x = os.path.split(sys.argv[0])
		config = os.path.join(mydir, "config", "config")
		plugins = os.path.join(mydir, "plugins")
	else:
		config = os.path.join(os.path.expanduser("~"),'.nicotine','config')
		plugins = os.path.join(os.path.expanduser("~"),'.nicotine','plugins')
	profile = 0
	trayicon = 1
	webbrowser = True
	tryrgba = False
	hidden = False
	bindip = None
	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit()
		if o in ("-c", "--config"):
			config = a
		if o in ("-p", "--plugins"):
			plugins = a
		if o in ("-b", "--bindip"):
			bindip = a
		if o == "--profile":
			profile = 1
		if o in ("-t", "--enable-trayicon"):
			trayicon=1
		if o in ("-d", "--disable-trayicon"):
			trayicon=0
		if o in ("-w", "--disable-webbrowser"):
			webbrowser = False
		if o in ('-r', '--enable-rgba'):
			tryrgba = True
		if o in ('-x', '--disable-rgba'):
			tryrgba = False
		if o in ('-s', '--hidden'):
			hidden = True
		if o in ("-v", "--version"):
			version()
			sys.exit()
	result = checkenv()
	if result is None:
		from pynicotine.gtkgui import frame

		app = frame.MainApp(config, plugins, trayicon, tryrgba, hidden, webbrowser, bindip)
		if profile:
			import hotshot
			logfile = os.path.expanduser(config) + ".profile"
			profiler = hotshot.Profile(logfile)
			log.add(_("Starting using the profiler (saving log to %s)") % logfile)
			profiler.runcall(app.MainLoop)
		else:
			app.MainLoop()
	else:
		print result

if __name__ == '__main__':
	try:
		run()
	except SystemExit:
		raise
	except: # BaseException doesn't exist in python2.4
		import traceback
		traceback.print_exc()
