# $Id: kernel-module-freeswan.spec 201 2004-04-03 15:24:49Z dag $
# Authority: dag
# Upstream: <dev@lists.openswan.org>

# Archs: i686 i586 i386 athlon
# Distcc: 0
# Soapbox: 0
# BuildAsRoot: 1

%define _libmoddir /lib/modules

%{!?kernel:%define kernel %(rpm -q kernel-source --qf '%{RPMTAG_VERSION}-%{RPMTAG_RELEASE}' | tail -1)}

%define kversion %(echo "%{kernel}" | sed -e 's|-.*||')
%define krelease %(echo "%{kernel}" | sed -e 's|.*-||')

%define real_name openswan
%define real_version 2.1.1
%define real_release 1

%define moduledir /kernel/net/openswan
%define modules linux/net/ipsec/ipsec.o

Summary: Linux drivers for OpenS/WAN IPsec support
Name: kernel-module-openswan
Version: %{real_version}
Release: %{real_release}_%{kversion}_%{krelease}
License: GPL
Group: System Environment/Kernel
URL: http://www.openswan.org/

Packager: Dag Wieers <dag@wieers.com>
Vendor: Dag Apt Repository, http://dag.wieers.com/apt/

Source: http://www.openswan.org/code/openswan-%{real_version}.tar.gz
Patch0: openswan-2.1.1-mts.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

BuildRequires: libpcap, gmp-devel
BuildRequires: /usr/bin/man2html

Requires: /boot/vmlinuz-%{kversion}-%{krelease}
Requires: openswan-utils

Provides: kernel-modules
Provides: freeswan-modules = %{version}-%{release}, freeswan-module = %{version}-%{release}
Obsoletes: freeswan-modules <= %{version}, freeswan-module <= %{version}, openswan

%description
Linux drivers for OpenS/WAN IPsec support.

These drivers are built for kernel %{kversion}-%{krelease}
and architecture %{_target_cpu}.
They might work with newer/older kernels.

%package -n kernel-smp-module-openswan
Summary: Linux SMP drivers for OpenS/WAN IPsec support
Release: %{real_release}_%{kversion}_%{krelease}
Group: System Environment/Kernel

Requires: /boot/vmlinuz-%{kversion}-%{krelease}smp
Requires: openswan-utils

Provides: kernel-modules
Provides: freeswan-modules = %{version}-%{release}, freeswan-module = %{version}-%{release}
#Obsoletes: freeswan-modules <= %{version}, freeswan-module <= %{version}

%description -n kernel-smp-module-openswan
Linux SMP drivers for OpenS/WAN IPsec support.

These drivers are built for kernel %{kversion}-%{krelease}smp
and architecture %{_target_cpu}.
They might work with newer/older kernels.

%package -n openswan-utils
Summary: OpenS/WAN programs and libraries
Release: %{real_release}
Group: System Environment/Base

Provides: freeswan = %{version}-%{release}, freeswan-programs = %{version}-%{release}
Provides: freeswan-userland = %{version}-%{release}, freeswan-utils = %{version}-%{release}
Obsoletes: freeswan <= %{version}, freeswan-programs <= %{version}
Obsoletes: freeswan-userland <= %{version}, freeswan-doc <= %{version}

%description -n openswan-utils
OpenS/WAN programs and libraries.

%prep
%setup -n %{real_name}-%{real_version}
#%setup -n %{real_name}-%{real_version} -a 1
%patch0
#%{__cat} x509-*/freeswan.diff | patch -p1

%{__cat} <<EOF >ipsec.secrets
### This file holds shared secrets or RSA private keys for inter-Pluto
### authentication. See ipsec_pluto(8) manpage and HTML documentation.

### RSA private key for this host, authenticating it to any other host
### which knows the public part. Suitable public keys, for ipsec.conf, DNS,
### or configuration of other implementations, can be extracted conveniently
### with "ipsec showhostkey".

: RSA	{
	}
EOF

%{__cat} <<'EOF' >openswan.sysv
#!/bin/bash
#
# Init file for OpenS/WAN IPsec module loader
#
# Written by Dag Wieers <dag@wieers.com>.
#
# chkconfig: 345 80 20
# description: OpenS/WAN IPsec module loader.
#
# config: %{_sysconfdir}/ipsec.conf

source %{_initrddir}/functions

[ -x %{_sbindir}/ipsec ] || exit 1
[ -r %{_sysconfdir}/ipsec.conf ] || exit 1

RETVAL=255
prog="openswan"
desc="OpenS/WAN IPsec module loader"

start() {
	echo -n $"Starting $desc ($prog): "
	if ! grep -q '^ipsec' /proc/modules; then
		modprobe ipsec &>/dev/null
		RETVAL=$?
	fi
	if [ $RETVAL -eq 0 ]; then
		success $"ipsec.o loaded"
		touch %{_localstatedir}/lock/subsys/$prog
	else
		failure $"ipsec.o load failed"
	fi
	echo
	return $RETVAL
}

stop() {
	echo -n $"Shutting down $desc ($prog): "
	if grep -q '^ipsec' /proc/modules; then
		rmmod ipsec &>/dev/null
		RETVAL=$?
	fi
	if [ $RETVAL -eq 0 ]; then
		success $"ipsec.o unloaded"
		rm -f %{_localstatedir}/lock/subsys/$prog
	else
		failure $"ipsec.o unload failed"
	fi
	echo
	return $RETVAL
}

restart() {
	stop
	start
}

status() {
	if grep -q '^ipsec ' /proc/modules; then
		echo -n $"ipsec.o is loaded..."
	else
		echo -n $"ipsec.o is not loaded..."
	fi
	echo
}

case "$1" in
  start)
	start
	;;
  stop)
	stop
	;;
  restart|reload)
	restart
	;;
  condrestart)
	[ -e %{_localstatedir}/lock/subsys/$prog ] && restart
	RETVAL=$?
	;;
  status)
	status $prog
	RETVAL=$?
	;;
  *)
	echo $"Usage: $0 {start|stop|restart|condrestart|status}"
	RETVAL=1
esac

exit $RETVAL
EOF

%build
%{__rm} -rf %{buildroot}
echo -e "\nDriver version: %{real_version}\nKernel version: %{kversion}-%{krelease}\n"

### Prepare UP kernel.
cd %{_usrsrc}/linux-%{kversion}-%{krelease}
%{__make} -s distclean &>/dev/null
%{__cp} -f configs/kernel-%{kversion}-%{_target_cpu}.config .config
%{__make} -s symlinks oldconfig dep EXTRAVERSION="-%{krelease}" &>/dev/null
cd -

### Make UP module.
%{__make} clean module \
	KERNELSRC="%{_libmoddir}/%{kversion}-%{krelease}/build" \
	ARCH="%{_arch}" \
	SUBARCH="%{_arch}" \
	CC="${CC:-%{__cc}}"
%{__install} -d -m0755 %{buildroot}%{_libmoddir}/%{kversion}-%{krelease}%{moduledir}
%{__install} -m0644 %{modules} %{buildroot}%{_libmoddir}/%{kversion}-%{krelease}%{moduledir}

### Prepare SMP kernel.
cd %{_usrsrc}/linux-%{kversion}-%{krelease}
%{__make} -s distclean &>/dev/null
%{__cp} -f configs/kernel-%{kversion}-%{_target_cpu}-smp.config .config
%{__make} -s symlinks oldconfig dep EXTRAVERSION="-%{krelease}smp" &>/dev/null
cd -

### Make SMP module.
%{__make} clean module \
	KERNELSRC="%{_libmoddir}/%{kversion}-%{krelease}/build" \
	ARCH="%{_arch}" \
	SUBARCH="%{_arch}" \
	CC="${CC:-%{__cc}}"
%{__install} -d -m0755 %{buildroot}%{_libmoddir}/%{kversion}-%{krelease}smp%{moduledir}
%{__install} -m0644 %{modules} %{buildroot}%{_libmoddir}/%{kversion}-%{krelease}smp%{moduledir}

### Build utilities.
%{__make} %{?_smp_mflags} programs \
	USERCOMPILE="-g %{optflags}" \
	INC_USRLOCAL="%{_prefix}" \
	MANTREE="%{_mandir}" \
	INC_RCDEFAULT="%{_initrddir}"

%install
### Install utilities.
#makeinstall 
%{__make} install \
	DESTDIR="%{buildroot}" \
	INC_USRLOCAL="%{_prefix}" \
	MANTREE="%{buildroot}%{_mandir}" \
	INC_RCDEFAULT="%{_initrddir}"

%{__install} -d -m0700 %{buildroot}%{_localstatedir}/run/pluto/ \
			%{buildroot}%{_sysconfdir}/ipsec.d/
#%{__install} -m0755 freeswan.sysv %{buildroot}%{_initrddir}/freeswan
%{__install} -m0644 ipsec.secrets %{buildroot}%{_sysconfdir}

### Clean up buildroot
%{__perl} -pi -e 's|/usr/local|%{_prefix}|g' %{buildroot}%{_libexecdir}/ipsec/* %{buildroot}%{_libdir}/ipsec/*
%{__mv} -f %{buildroot}%{_docdir}/freeswan/ipsec.conf-sample %{buildroot}%{_sysconfdir}/ipsec.conf

### Clean up docroot
%{__mv} -f %{buildroot}%{_prefix}/share/doc/freeswan/ rpm-doc/
%{__rm} -f rpm-doc/*.{pdf,ps}

%post
/sbin/depmod -ae %{kversion}-%{krelease} || :

%postun
/sbin/depmod -ae %{kversion}-%{krelease} || :

%post -n kernel-smp-module-openswan
/sbin/depmod -ae %{kversion}-%{krelease}smp || :

%postun -n kernel-smp-module-openswan
/sbin/depmod -ae %{kversion}-%{krelease}smp || :

%post -n openswan-utils
/sbin/chkconfig --add ipsec

%preun -n openswan-utils
if [ $1 -eq 0 ]; then
        /sbin/service ipsec stop &>/dev/null || :
        /sbin/chkconfig --del ipsec
fi

%postun -n openswan-utils
/sbin/service ipsec condrestart &>/dev/null || :

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
%{_libmoddir}/%{kversion}-%{krelease}%{moduledir}/

%files -n kernel-smp-module-openswan
%defattr(-, root, root, 0755)
%{_libmoddir}/%{kversion}-%{krelease}smp%{moduledir}/

%files -n openswan-utils
%defattr(-, root, root, 0755)
%doc BUGS* CHANGES* COPYING CREDITS INSTALL LICENSE README* doc/ rpm-doc/*
%doc programs/_confread/ipsec.conf
%doc %{_mandir}/man?/*
%config(noreplace) %{_sysconfdir}/ipsec.secrets
%config(noreplace) %{_sysconfdir}/ipsec.conf
%config(noreplace) %{_sysconfdir}/ipsec.d/
#%config %{_initrddir}/freeswan
%config %{_initrddir}/ipsec
%{_sbindir}/*
%{_libdir}/ipsec/
%{_libexecdir}/ipsec/
%{_localstatedir}/run/pluto/
#%{_includedir}/*.h

%changelog
* Wed Apr 07 2004 Dag Wieers <dag@wieers.com> - 2.1.1-1
- Updated to openswan release 2.1.1.

* Thu Mar 11 2004 Dag Wieers <dag@wieers.com> - 2.05-1
- Fixed the longstanding smp kernel bug. (Bert de Bruijn)

* Tue Feb 17 2004 Dag Wieers <dag@wieers.com> - 2.05-0
- Updated to release 2.05.

* Fri Jan 09 2004 Dag Wieers <dag@wieers.com> - 1.99-0
- Initial package. (using DAR)
