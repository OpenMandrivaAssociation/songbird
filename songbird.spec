%define pkgname Songbird

%define buildrel 1018

Name:		songbird
Summary:	The desktop media player mashed-up with the Web
Version:	1.1.1
Release:	%mkrel 2
# Songbird requires an upstream patched xulrunner and taglib to function
# properly. Bundled vendor sources can be found at:
# http://wiki.songbirdnest.com/Developer/Articles/Builds/Contributed_Builds 
Source0:	http://download.songbirdnest.com/source/%{pkgname}%{version}-%{buildrel}.tar.bz2
Source1:	http://rpm.rutgers.edu/fedora/%{pkgname}%{version}-%{buildrel}-vendor-reduced.tar.bz2
Source2:	http://rpm.rutgers.edu/fedora/songbird.desktop
Source3:	http://rpm.rutgers.edu/fedora/find-external-requires
Source4:	http://rpm.rutgers.edu/fedora/songbird.sh.in
Patch0:		http://rpm.rutgers.edu/fedora/nsAppRunner.patch
Group:		Sound
License:	GPLv2
URL:		http://www.getsongbird.com/
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires:	cmake, desktop-file-utils
BuildRequires:	libgstreamer-plugins-base-devel >= 0.10.7
BuildRequires:	libgstreamer-devel >= 0.10.1
BuildRequires:	libxt-devel
BuildRequires:	libIDL-devel
BuildRequires:	libcurl-devel
BuildRequires:	gtk2-devel
BuildRequires:	dbus-glib-devel
BuildRequires:	hal-devel
BuildRequires:  zlib-devel
BuildRequires:	zip
BuildRequires:  subversion
Requires:	gstreamer0.10-plugins-base
Suggests:	gstreamer0.10-plugins-ugly

# Filter internal provides
AutoProv: 0
%define _use_internal_dependency_generator 0
%define __find_requires %{SOURCE3}

%description
Songbird provides a public playground for Web media mash-ups by 
providing developers with both desktop and Web APIs, developer 
resources and fostering Open Web media standards.

%prep
%setup -q -n %{pkgname}%{version} -a1

# Upstream scripts generalize archs. Specify the proper
# paths to match upstream for a sane build.
%ifnarch i386
%define sb_arch %{_arch}
%endif

%ifarch %ix86
%define sb_arch i686
%endif


# Songbird bugzilla 15676
%patch0 -p0 -b .fixarch

mkdir -p build/checkout/linux-%{sb_arch}
mkdir -p build/linux-%{sb_arch}
rm -rf dependencies/vendor
mv %{pkgname}%{version}-vendor dependencies/vendor

%build
# Build XULRunner

cd dependencies/vendor/xulrunner/mozilla

# Setup XULRunner mozconfig
cat << "EOF" > .mozconfig
MOZILLA_OFFICIAL=1
export MOZILLA_OFFICIAL
BUILD_OFFICIAL=1
export BUILD_OFFICIAL

mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/compiled/xulrunner
ac_add_options --prefix=%{_prefix}
ac_add_options --libdir=%{_libdir}
ac_add_options --mandir=%{_mandir}
ac_add_options --enable-application=xulrunner
ac_add_options --with-xulrunner-stub-name=songbird-bin
ac_add_options --enable-optimize
ac_add_options --disable-debug
ac_add_options --disable-tests
ac_add_options --disable-auto-deps
ac_add_options --disable-crashreporter
ac_add_options --disable-javaxpcom
ac_add_options --disable-updater
ac_add_options --disable-installer
ac_add_options --enable-extensions=default,inspector,venkman
ac_add_options --disable-dbus
ac_add_options --enable-jemalloc
mk_add_options BUILD_OFFICIAL=1
mk_add_options MOZILLA_OFFICIAL=1
mk_add_options MOZ_DEBUG_SYMBOLS=1
mk_add_options MOZ_MAKE_FLAGS=%{?_smp_mflags}
EOF

mkdir -p compiled/xulrunner

make -f client.mk build_all

cd ../../../..

mkdir -p dependencies/linux-%{sb_arch}/mozilla/release
mkdir -p dependencies/linux-%{sb_arch}/xulrunner/release

# Package XULRunner
cd tools/scripts
./make-mozilla-sdk.sh ../../dependencies/vendor/xulrunner/mozilla ../../dependencies/vendor/xulrunner/mozilla/compiled/xulrunner ../../dependencies/linux-%{sb_arch}/mozilla/release
./make-xulrunner-tarball.sh ../../dependencies/vendor/xulrunner/mozilla/compiled/xulrunner/dist/bin ../../dependencies/linux-%{sb_arch}/xulrunner/release xulrunner.tar.gz

# Link the completed package where make expects it
ln -s ../../dependencies/linux-%{sb_arch}/mozilla ../../build/linux-%{sb_arch}/mozilla

cd ../..

# Build the included vendor libraries(taglib)
cd dependencies/vendor/taglib
SB_VENDOR_BUILD_ROOT=%{_builddir}/%{pkgname}%{version}/build make -f Makefile.songbird release

cd ../../..

# Move compiled taglib into the dependecies area
cd build/linux-%{sb_arch}
mv taglib ../../dependencies/linux-%{sb_arch}/
cd ../..

# Build Songbird
export SB_ENABLE_INSTALLER=1
export SONGBIRD_OFFICIAL=1
export SB_ENABLE_JARS=1

# Force system library usage
echo "ac_add_options --with-media-core=gstreamer-system" > songbird.config

# In order for debug packages to be created, -gstabs+ must be
# removed from the compile options under 64 bit or debugedit chokes,
# bug 453506
%ifarch x86_64 ppc64
sed -i s/-gstabs+//g configure.ac
%endif

make -f songbird.mk MOZ_MAKE_FLAGS=%{?_smp_mflags}


%install
rm -rf %{buildroot} 

cd compiled
mkdir -p %{buildroot}%{_libdir}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/64x64/apps
mkdir -p %{buildroot}%{_datadir}/applications
cp -pR dist %{buildroot}%{_libdir}/songbird-%{version}

cp -p ../app/branding/icon64.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/songbird.png

desktop-file-install --vendor="" --dir=%{buildroot}%{_datadir}/applications %{SOURCE2}

# set up the songbird start script
cat %{SOURCE4} | sed -e 's,SONGBIRD_VERSION,%{version},g' > %{buildroot}%{_bindir}/songbird
chmod 755 %{buildroot}%{_bindir}/songbird

cd %{_builddir}/%{pkgname}%{version}/compiled/dist
cp -p TRADEMARK.txt README.txt LICENSE.html ../..

%clean
rm -rf %{buildroot}

%if %mdkversion < 200900
%post
%update_desktop_database
%update_icon_cache hicolor
%endif

%if %mdkversion < 200900
%postun
%clean_desktop_database
%clean_icon_cache hicolor
%endif

%files 
%defattr(-, root, root, -)
%doc TRADEMARK.txt README.txt LICENSE.html
%{_bindir}/songbird
%{_libdir}/songbird-%{version}
%{_datadir}/applications/songbird.desktop
%{_datadir}/icons/hicolor/64x64/apps/songbird.png

