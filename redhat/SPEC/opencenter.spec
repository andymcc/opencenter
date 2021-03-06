%define ver 6

# disable python byte compiling
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')

Name:       opencenter
Version:    0.2.0
Release:    %{ver}%{?dist}
Summary:        Pluggable, modular OpenCenter server
Group:          System
License:        Apache2
URL:            https://github.com/rcbops/opencenter
Source0:        opencenter-%{version}.tgz
Source1:        opencenter.conf
Source2:        opencenter.upstart
Source3:        opencenter.systemd
Source4:        opencenter.sysconfig
BuildArch: noarch

%description
some description

%package server
Summary:        Some summary
BuildRequires:  python-setuptools
Requires:       python-requests
Requires:       python >= 2.6
Requires:       python-requests
Requires:       python-flask
%if 0%{?rhel} == 6
Requires:       python-sqlalchemy0.7
%else
Requires:       python-sqlalchemy >= 0.7
%endif
Requires:       python-migrate
Requires:       python-daemon
Requires:       python-chef
# we don't have python-gevent in epel yet - so this comes from our repo
Requires:       python-gevent
Requires:       python-mako
Requires:       python-netifaces
Requires:       opencenter >= %{version}
Requires:       python-opencenter >= %{version}
Requires:       MySQL-python
Requires:       openssl
Requires:       mod_ssl

%description server
The server description

%package -n python-opencenter
Summary: The Python bindings for OpenCenter
Requires: python >= 2.6
Requires: python-requests
Requires: python-requests
Requires: python-flask
%if 0%{?rhel} == 6
Requires:       python-sqlalchemy0.7
%else
Requires:       python-sqlalchemy >= 0.7
%endif
Requires: python-migrate
Requires: python-daemon
Requires: python-chef
# we don't have python-gevent in epel yet
Requires: python-gevent
Requires: python-mako
Requires: python-netifaces
Group: System

%description -n python-opencenter
The Python bindings for OpenCenter

%prep
%setup -q -n %{name}-%{version}

%build
CFLAGS="$RPM_OPT_FLAGS" %{__python} -B setup.py build

%install
mkdir -p $RPM_BUILD_ROOT/usr/bin
mkdir -p $RPM_BUILD_ROOT/etc/init
mkdir -p $RPM_BUILD_ROOT/etc/opencenter
mkdir -p $RPM_BUILD_ROOT/usr/share/opencenter
mkdir -p $RPM_BUILD_ROOT/var/log/opencenter
install -m 600 $RPM_SOURCE_DIR/opencenter.conf $RPM_BUILD_ROOT/etc/opencenter/opencenter.conf
%if 0%{?rhel} == 6
install -m 755 $RPM_SOURCE_DIR/opencenter.upstart $RPM_BUILD_ROOT/etc/init/opencenter.conf
%else
mkdir -p $RPM_BUILD_ROOT/etc/sysconfig
mkdir -p $RPM_BUILD_ROOT/etc/systemd/system
install -m 755 $RPM_SOURCE_DIR/opencenter.sysconfig $RPM_BUILD_ROOT/etc/sysconfig/opencenter
install -m 755 $RPM_SOURCE_DIR/opencenter.systemd $RPM_BUILD_ROOT/etc/systemd/system/opencenter.service
%endif
%{__python} -B setup.py install --skip-build --root $RPM_BUILD_ROOT

%files 
%config(noreplace) /etc/opencenter

%files server
%defattr(-,root,root)
/usr/bin/opencenter
%if 0%{?rhel} == 6
/etc/init/opencenter.conf
%else
/etc/systemd/system/opencenter.service
%config(noreplace) /etc/sysconfig/opencenter
%endif
/usr/share/opencenter

%files -n python-opencenter
%defattr(-,root,root)
%{python_sitelib}/*opencenter*

%clean
rm -rf $RPM_BUILD_ROOT

%post

# *******************************************************
# ATTENTION: changelog is in reverse chronological order
# *******************************************************
%changelog
* Wed Mar 20 2013 RCB Builder (rcb-deploy@lists.rackspace.com) - 0.2.0
- Fixed Fedora packaging
- Fixed default value for vncserver_listen env template
- Added new facts
  ram_allocation_ratio
  cpu_allocation_ratio
  use_single_gateway
  nova_network_dhcp_name
- Fixed node deletion showing up in updates
- Removed manage.py

* Mon Sep 10 2012 Joseph W. Breu (joseph.breu@rackspace.com) - 0.1.0
- Initial build
