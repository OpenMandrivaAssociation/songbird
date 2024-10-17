%define pkgname Songbird

%define buildrel 1438
%define mozappdir %{_libdir}/songbird-%{version}

Name:		songbird
Summary:	The desktop media player mashed-up with the Web
Version:	1.4.3
Release:	%mkrel 3
# Songbird requires an upstream patched xulrunner and taglib to function
# properly. Bundled vendor sources can be found at:
# http://wiki.songbirdnest.com/Developer/Articles/Builds/Contributed_Builds 
Source0:	http://download.songbirdnest.com/source/%{pkgname}%{version}-%{buildrel}.tar.bz2
Source1:	http://rpm.rutgers.edu/fedora/%{pkgname}%{version}-%{buildrel}-vendor-reduced.tar.bz2
Source2:	http://rpm.rutgers.edu/fedora/songbird.desktop
Source3:	http://rpm.rutgers.edu/fedora/find-external-requires
Source4:	http://rpm.rutgers.edu/fedora/songbird.sh.in
# (fc) 1.2.0-1mdv fix format security errors
Patch1:		xulrunner-1.9.0.5-fix-string-format.patch
# add upstream patch to some bugs with system gstreamer
# http://bugzilla.songbirdnest.com/show_bug.cgi?id=20660
Patch2:		changeset_r18100.diff
Patch3:		Songbird1.4.3-fix-build.patch
Group:		Sound
License:	GPLv2
URL:		https://www.getsongbird.com/
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires:	cmake, desktop-file-utils
BuildRequires:	libgstreamer-plugins-base-devel >= 0.10.22
BuildRequires:	libgstreamer-devel >= 0.10.22
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
Suggests:	gstreamer0.10-plugins-bad

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

%ifarch %{ix86}
%define sb_arch i686
%else
%define sb_arch %{_arch}
%endif

mkdir -p build/checkout/linux-%{sb_arch}
mkdir -p build/linux-%{sb_arch}
rm -rf dependencies/vendor
mv %{pkgname}%{version}-vendor dependencies/vendor

cd dependencies/vendor/xulrunner/mozilla
%patch1 -p0 -b .format-security
cd -

# gstreamer patch
%patch2 -p2 -b .gstreamer

# fix build
cd dependencies/vendor/xulrunner/mozilla/modules/libpr0n/build
%patch3 -p0
cd -

# disable ipod support
sed -i -e 's|DEFAULT_EXTENSIONS += ipod|echo "DEFAULT_EXTENSIONS += ipod"|g' extensions/Makefile.in

%build
# Build XULRunner

cd dependencies/vendor/xulrunner/mozilla

# Build with -Os as it helps the browser; also, don't override mozilla's warning
# level; they use -Wall but disable a few warnings that show up _everywhere_
MOZ_OPT_FLAGS=$(echo $RPM_OPT_FLAGS | %{__sed} -e 's/-O2/-Os/' -e 's/-Wall//')

export RPM_OPT_FLAGS=$MOZ_OPT_FLAGS
export LDFLAGS="-Wl,-rpath,%{mozappdir}"

#Setup XULRunner mozconfig
cat << "EOF" > .mozconfig
MOZILLA_OFFICIAL=1
export MOZILLA_OFFICIAL
BUILD_OFFICIAL=1
export BUILD_OFFICIAL

mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/compiled/xulrunner
ac_add_options --prefix=%{_prefix}
ac_add_options --libdir=%{_libdir}
ac_add_options --mandir=%{_mandir}
ac_add_options --with-system-jpeg
ac_add_options --with-system-zlib
ac_add_options --with-pthreads
ac_add_options --enable-optimize="$RPM_OPT_FLAGS"
ac_add_options --enable-pango
ac_add_options --enable-system-cairo
ac_add_options --enable-svg
ac_add_options --enable-canvas
ac_add_options --enable-application=xulrunner
ac_add_options --with-xulrunner-stub-name=songbird-bin
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

cp -f ../../dependencies/vendor/xulrunner/make-mozilla-sdk.sh .
cp -f ../../dependencies/vendor/xulrunner/make-xulrunner-tarball.sh .

./make-mozilla-sdk.sh \
 ../../dependencies/vendor/xulrunner/mozilla \
 ../../dependencies/vendor/xulrunner/mozilla/compiled/xulrunner \
 ../../dependencies/linux-%{sb_arch}/mozilla/release
./make-xulrunner-tarball.sh \
 ../../dependencies/vendor/xulrunner/mozilla/compiled/xulrunner/dist/bin \
 ../../dependencies/linux-%{sb_arch}/xulrunner/release xulrunner.tar.bz2

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

# prevent the build system from trying to keep your mozbrowser up-to-date
export SB_DISABLE_DEPEND_PKG_MGMT=1
export SB_DISABLE_PKG_AUTODEPS=1

# Force system library usage
echo "ac_add_options --with-media-core=gstreamer-system" > songbird.config

# In order for debug packages to be created, -gstabs+ must be
# removed from the compile options under 64 bit or debugedit chokes,
# bug 453506
sed -i s/-gstabs+//g configure.ac

make -f songbird.mk MOZ_MAKE_FLAGS=%{?_smp_mflags}

%install
rm -rf %{buildroot} 

cd compiled
mkdir -p %{buildroot}%{_libdir}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/32x32/apps
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/64x64/apps
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/128x128/apps
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/256x256/apps
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/512x512/apps
mkdir -p %{buildroot}%{_datadir}/applications
cp -pR dist %{buildroot}%{mozappdir}

cp -p ../app/branding/songbird-32.png %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/songbird.png
cp -p ../app/branding/songbird-64.png %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/songbird.png
cp -p ../app/branding/songbird-128.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/songbird.png
cp -p ../app/branding/songbird-256.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/songbird.png
cp -p ../app/branding/songbird-512.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/songbird.png

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
%defattr(644,root,root,755)
%doc %{mozappdir}/TRADEMARK.txt
%doc %{mozappdir}/README.txt
%doc %{mozappdir}/LICENSE.html
%dir %{mozappdir}
%{mozappdir}/chrome
%{mozappdir}/components/*.txt
%{mozappdir}/defaults
%{mozappdir}/extensions
%{mozappdir}/plugins
%{mozappdir}/scripts
%{mozappdir}/searchplugins
%{mozappdir}/xulrunner/chrome
%{mozappdir}/xulrunner/*.chk
%{mozappdir}/xulrunner/dependentlibs.list
%{mozappdir}/xulrunner/platform.ini
%{mozappdir}/xulrunner/updater.ini
%{mozappdir}/updater.ini
%{mozappdir}/application.ini
%{mozappdir}/songbird.ini
%{mozappdir}/gstreamer
%{mozappdir}/blocklist.xml
%{mozappdir}/xulrunner/dictionaries/*
%{mozappdir}/xulrunner/defaults/*
%{mozappdir}/xulrunner/res/*
%{mozappdir}/xulrunner/icons/*
%{mozappdir}/xulrunner/components/*.js
%{mozappdir}/xulrunner/greprefs/*.js
%{mozappdir}/xulrunner/modules/*.js
%{mozappdir}/xulrunner/modules/*.jsm
%{mozappdir}/xulrunner/README.txt
%{mozappdir}/xulrunner/LICENSE
%{mozappdir}/jsmodules/*.jsm
%{mozappdir}/components/*.jsm
%{mozappdir}/components/*.js
%{mozappdir}/songbird-512.png
%{_datadir}/applications/songbird.desktop
%{_datadir}/icons/hicolor/32x32/apps/songbird.png
%{_datadir}/icons/hicolor/64x64/apps/songbird.png
%{_datadir}/icons/hicolor/128x128/apps/songbird.png
%{_datadir}/icons/hicolor/256x256/apps/songbird.png
%{_datadir}/icons/hicolor/512x512/apps/songbird.png
%{mozappdir}/.autoreg

%defattr(755,root,root,755)
%dir %{mozappdir}/xulrunner
%dir %{mozappdir}/xulrunner/defaults
%dir %{mozappdir}/xulrunner/greprefs
%dir %{mozappdir}/xulrunner/dictionaries
%dir %{mozappdir}/xulrunner/components
%dir %{mozappdir}/xulrunner/res
%dir %{mozappdir}/xulrunner/modules
%dir %{mozappdir}/xulrunner/icons
%dir %{mozappdir}/xulrunner/plugins
%dir %{mozappdir}/jsmodules
%dir %{mozappdir}/components
%dir %{mozappdir}/lib

%{_bindir}/songbird
%{mozappdir}/xulrunner/components/*.xpt
%{mozappdir}/components/*.xpt
%{mozappdir}/components/*.so
%{mozappdir}/xulrunner/*.so
%{mozappdir}/lib/*.so
%{mozappdir}/*.so
%{mozappdir}/songbird-bin
%{mozappdir}/songbird
%{mozappdir}/xulrunner/components/*.so
%{mozappdir}/xulrunner/plugins/*.so
%{mozappdir}/xulrunner/mangle
%{mozappdir}/xulrunner/mozilla-xremote-client
%{mozappdir}/xulrunner/nsinstall
%{mozappdir}/xulrunner/regxpcom
%{mozappdir}/xulrunner/shlibsign
%{mozappdir}/xulrunner/ssltunnel
%{mozappdir}/xulrunner/xpcshell
%{mozappdir}/xulrunner/xpidl
%{mozappdir}/xulrunner/xpt_dump
%{mozappdir}/xulrunner/xpt_link
%{mozappdir}/xulrunner/xulrunner
%{mozappdir}/xulrunner/xulrunner-bin
%{mozappdir}/xulrunner/run-mozilla.sh

