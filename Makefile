#
# fgAPIServer makefile
#
PKGNUM = 0
VERSION = $$(git tag | tail -n 1 | sed s/v//)
DEBPKGDIR = fgAPIServer_$(VERSION)-$(PKGNUM)
SRCPKGDIR = packages
DEBPKGNAME = fgAPIServer_$(VERSION)-$(PKGNUM).deb
PKGDIR = /tmp/$(DEBPKGDIR)
FGUSER = futuregateway
HOMEDIR = /home
define DEBCONTROL
Package: fgAPIServer
Version: %VERSION% 
Section: base
Priority: optional
Architecture: all
Depends: mysql-client, apache2, libapache2-mod-wsgi, python-dev, python-pip, python-flask, python-flask-login, python-crypto, python-mysqldb, screen, lsb-release
Homepage: https://github.com/indigo-dc/fgAPIServer
Maintainer: Riccardo Bruno <riccardo.bruno@ct.infn.it>
Description: FutureGateway' API Server component
 FutureGateway' APIServer
 This package installs the FutureGateway' APIServear.
endef

define DEBPOSTINST
#!/bin/bash
#
# fgAPIServer post-installation script
#
FGPRODUCT=fgAPIServer
FGUSER=$(FGUSER)
HOMEDIR=$(HOMEDIR)
# Timestamp
get_ts() {
  TS=$$(date +%y%m%d%H%M%S)
}

# Output function notify messages
# Arguments: $$1 - Message to print
#            $$2 - No new line if not zero
#            $$3 - No timestamp if not zero
out() {
  # Get timestamp in TS variable  
  get_ts

  # Prepare output flags
  OUTCMD=echo
  MESSAGE=$$1
  NONEWLINE=$$2
  NOTIMESTAMP=$$3 
  if [ "$$NONEWLINE" != "" -a $$((1*NONEWLINE)) -ne 0 ]; then
    OUTCMD=printf
  fi
  if [ "$$3" != "" -a $$((1*NOTIMESTAMP)) -ne 0 ]; then
    TS=""
  fi
  OUTMSG=$$(echo $$TS" "$$MESSAGE)
  $$OUTCMD "$$OUTMSG" >&1
  if [ "$$FGLOG" != "" ]; then
    $$OUTCMD "$$OUTMSG" >> $$FGLOG
  fi  
}

# Error function notify about errors
err() {
  get_ts
  echo $$TS" "$$1 >&2 
}

# Check if the FGUSER exists
check_user() {
  getent passwd $$FGUSER >/dev/null 2>&1
  return $$?
}

# Show output and error files
outf() {
  OUTF=$$1
  ERRF=$$2
  if [ "$$OUTF" != "" -a -f "$$OUTF" ]; then
    while read out_line; do
      out "$$out_line"
    done < $$OUTF
  fi
  if [ "$$ERRF" != "" -a -f "$$ERRF" ]; then
    while read err_line; do
      err "$$err_line"
    done < $$ERRF
  fi
}

# Execute the given command
# $$1 Command to execute
# $$2 If not null does not print the command (optional)
cmd_exec() {
  TMPOUT=$$(mktemp /tmp/fg_out_XXXXXXXX)
  TMPERR=$$(mktemp /tmp/fg_err_XXXXXXXX)
  if [ "$$2" = "" ]; then
    out "Executing: '""$$1""'"
  fi  
  eval "$$1" >$$TMPOUT 2>$$TMPERR
  RET=$$?
  outf $$TMPOUT $$TMPERR
  rm -f $$TMPOUT
  rm -f $$TMPERR
  return $$RET
}

# Function that replace the 1st matching occurrence of
# a pattern with a given line into the specified filename
#  $$1 # File to change
#  $$2 # Matching pattern that identifies the line
#  $$3 # New line content
#  $$4 # Optionally specify a suffix to keep a safe copy
replace_line() {
  file_name=$$1   # File to change
  pattern=$$2     # Matching pattern that identifies the line
  new_line=$$3    # New line content
  keep_suffix=$$4 # Optionally specify a suffix to keep a safe copy

  if [ "$$file_name" != "" -a -f $$file_name -a "$$pattern" != "" ]; then
    TMP=$$(mktemp)
    cp $$file_name $$TMP
    if [ "$$keep_suffix" != "" ]; then # keep a copy of replaced file
      cp $$file_name $$file_name"_"$$keep_suffix
    fi
    MATCHING_LINE=$$(cat $$TMP | grep -n "$$pattern" | head -n 1 | awk -F':' '{ print $$1 }' | xargs echo)
    if [ "$$MATCHING_LINE" != "" ]; then
      cat $$TMP | head -n $$((MATCHING_LINE-1)) > $$file_name
      printf "$$new_line\n" >> $$file_name
      cat $$TMP | tail -n +$$((MATCHING_LINE+1)) >> $$file_name
    else
      echo "WARNING: Did not find '"$$pattern"' in file: '"$$file_name"'"
    fi
    rm -f $$TMP
  else
    echo "You must provide an existing filename and a valid pattern"
    return 1
  fi
}

#
# Post installation script
#
out "$$FGPRODUCT post install (begin)"
if check_user; then
  out "User $$FGUSER already exists"
else
  out "Creating $$FGUSER"
  cmd_exec "adduser --disabled-password --gecos \"\" $$FGUSER"
fi 
cmd_exec "pip install --upgrade flask-login"
cmd_exec "chmod a+x /etc/init.d/futuregateway"
cmd_exec "update-rc.d futuregateway defaults"
# Ubuntu 14.04 bug, screen section does not start at boot
cmd_exec "replace_line \"/etc/rc.local\" \"# By default this script does nothing.\\n\\n\" \"# By default this script does nothing.\\n/etc/init.d/futuregateway start\\n\" \"fg\""
# Environment
cmd_exec "cat $$HOMEDIR/$$FGUSER/.bash_profile"
cmd_exec "if [ ! -f $$HOMEDIR/$$FGUSER/.bash_profile -o \"$$(cat $$HOMEDIR/$$FGUSER/.bash_profile | grep fgsetenv_fga | wc -l)\" -eq 0 ]; then printf \"# Loading FutureGateway environment\\nsource .fgsetenv_fga\\n\" >> $$HOMEDIR/$$FGUSER/.bash_profile; fi"
out "$$FGPRODUCT post install (end)"
endef

define DEBSRVCTL
#! /bin/sh
### BEGIN INIT INFO
# Provides: futuregateway
# Required-Start: \$$remote_fs \$$syslog
# Required-Stop: \$$remote_fs \$$syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: FutureGateway
# Description: This file starts and stops FutureGateway portal and/or its API Server
#
### END INIT INFO

ENABLEFRONTEND=1 # In production environment this flag should be placed to 0
FRONTENDSESSIONNAME=fgAPIServer
SCREEN=\$$(which screen)
FGUSER=$(FGUSER)
TOMCAT_DIR=\$$(su - \$$FGUSER -c "echo \\\$$CATALINA_HOME")
export JAVA_HOME=\$$(su - \$$FGUSER -c "echo \\\$$JAVA_HOME")

futuregateway_proc() {
  JAVAPROC=\$$(ps -ef | grep java | grep tomcat | grep -v grep | grep -v ps | awk '{ print \$$2}')
  echo \$$JAVAPROC
}

frontend_session() {
  SESSION=\$$(su - \$$FGUSER -c "screen -ls | grep \$$FRONTENDSESSIONNAME")
  echo \$$SESSION | awk '{ print \$$1 }' | xargs echo
}

fgAPIServer_start() {
  if [ "\$$SCREEN" = "" ]; then
    echo "Unable to start fgAPIServer without screen command"
    return 1
  fi
  FRONTENDSESSION=\$$(frontend_session)
  if [ "\$$FRONTENDSESSION" != "" ]; then
    echo "APIServer front-end screen session already exists"
  else
    FGPROC=\$$(ps -ef | grep python | grep fgapiserver.py | head -n 1)
    if [ "\$$FGPROC" != "" ]; then
      echo "APIServer front-end is already running"
    else
      su - \$$FGUSER -c "screen -dmS \$$FRONTENDSESSIONNAME bash"
      FRONTENDSESSION=\$$(frontend_session)
      su - \$$FGUSER -c "screen -S \$$FRONTENDSESSIONNAME -X stuff \"cd \\\\\\\$$FGLOCATION/fgAPIServer\\n\""
      su - \$$FGUSER -c "screen -S \$$FRONTENDSESSIONNAME -X stuff \"./fgapiserver.py\\n\""
    fi
  fi
}

fgAPIServer_stop() {
  if [ "\$$SCREEN" = "" ]; then
    echo "Unable to stop fgAPIServer without screen command"
    return 1
  fi
  FRONTENDSESSION=\$$(frontend_session)
  if [ "\$$FRONTENDSESSION" = "" ]; then
    echo "APIServer front-end already stopped"
  else
    su - \$$FGUSER -c "screen -X -S \$$FRONTENDSESSIONNAME quit"
  fi
}

futuregateway_start() {
  JAVAPROC=\$$(futuregateway_proc)
  if [ "\$$JAVAPROC" != "" ]; then
    echo "FutureGateway already running"
  else
    su - \$$FGUSER -c start_tomcat
  fi
  if [ \$$ENABLEFRONTEND -ne 0 ]; then
    fgAPIServer_start
  else
    echo "fgAPIServer front-end disabled"
  fi
}

futuregateway_stop() {
  JAVAPROC=\$$(futuregateway_proc)
  if [ "\$$JAVAPROC" != "" ]; then
    su - \$$FGUSER -c stop_tomcat
    sleep 10
    JAVAPROC=\$$(futuregateway_proc)
    if [ "\$$JAVAPROC" != "" ]; then
      printf "Java process still active; killing ... "
      while [ "\$$JAVAPROC" != "" ]; do
        kill \$$JAVAPROC;
        JAVAPROC=\$$(futuregateway_proc)
      done
      echo "done"
    fi
  else
    echo "FurureGateway already stopped"
  fi
  if [ \$$ENABLEFRONTEND -ne 0 ]; then
    fgAPIServer_stop
  else
    echo "fgAPIServer front-end disabled"
  fi
}

futuregateway_status() {
  if [ \$$ENABLEFRONTEND -eq 0 ]; then
    echo "fgAPIServer front-end disabled"
  else
    JAVAPROC=\$$(futuregateway_proc)
    if [ "\$$JAVAPROC" != "" ]; then
      echo "Futuregateway is up and running"
    else
      echo "Futuregateway is stopped"
    fi
    FRONTENDSESSION=\$$(frontend_session)
    if [ "\$$FRONTENDSESSION" != "" ]; then
      echo "APIServer front-end is up and running"
    else
      echo "APIServer front-end is stopped"
    fi
  fi
}

case "\$$1" in
 start)
   futuregateway_start
   ;;
 stop)
   futuregateway_stop
   ;;
 restart)
   futuregateway_stop
   sleep 20
   futuregateway_start
   ;;
 status)
   futuregateway_status
   ;;
 *)
   echo "Usage: futuregateway {start|stop|restart|status}" >&2
   exit 3
   ;;
esac
endef

define DEBFGENV
#!/bin/bash
#
# This is the FutureGateway environment variable file
#
# Author: Riccardo Bruno <riccardo.bruno@ct.infn.it>
#
export RUNDIR=$(HOMEDIR)/$(FGUSER)
export FGLOCATION=$$RUNDIR
endef

help:
	@echo "fgAPIServer Makefile"
	@echo "Rules:"
	@echo "    deb  - Create the $(DEBPKGNAME) package file (Ubuntu 14.04LTS)"
	@echo "    help - Display this message"

export DEBPOSTINST
export DEBCONTROL
export DEBSRVCTL
export DEBFGENV
deb:
	# Preparing files
	@echo "Creating deb package: '"$(DEBPKGNAME)"'"
	@echo "Pakcage dir: '"$(PKGDIR)"'"
	@if [ -d $(PKGDIR) ]; then rm -rf $(PKGDIR); fi
	@if [ -f $(SRCPKGDIR)/$(DEBPKGNAME) ]; then rm -rf $(SRCPKGDIR)/$(DEBPKGNAME); fi
	@mkdir -p $(PKGDIR)$(HOMEDIR)/$(FGUSER)/$(DEBPKGDIR)
	@mkdir -p $(PKGDIR)/etc/init.d
	@cd $(PKGDIR)/$(HOMEDIR)/$(FGUSER) && ln -s $$(ls -1 | grep fgAPIServer | head -n 1) fgAPIServer && cd -
	@cp -r . $(PKGDIR)$(HOMEDIR)/$(FGUSER)/$(DEBPKGDIR)
	@mkdir -p $(PKGDIR)/DEBIAN
	@mkdir -p $(SRCPKGDIR)
	@echo "$$DEBSRVCTL" > $(PKGDIR)/etc/init.d/futuregateway
	@echo "$$DEBCONTROL" > $(PKGDIR)/DEBIAN/control
	@echo "$$DEBPOSTINST" > $(PKGDIR)/DEBIAN/postinst
	@chmod 775 $(PKGDIR)/DEBIAN/postinst
	@echo "$$DEBFGENV" > $(PKGDIR)$(HOMEDIR)/$(FGUSER)/.fgsetenv_fga
	@sed -i -e "s/%VERSION%/$(VERSION)-$(PKGNUM)/" $(PKGDIR)/DEBIAN/control
	#Building deb
	@dpkg-deb --build $(PKGDIR)
	@cp /tmp/$(DEBPKGNAME) $(SRCPKGDIR) 
	#@rm -rf $(PKGDIR)

