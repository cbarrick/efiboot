# Maintainer: Chris Barrick <cbarrick1@gmail.com>

pkgname=efiboot-git
pkgdesc='A configuration framework for EFI boot entries'
url='https://github.com/cbarrick/efiboot'
license=('Apache')

pkgver='git'
pkgrel=1

arch=('any')
provides=("${pkgname%-git}")
conflicts=("${pkgname%-git}")
depends=(
	'efibootmgr'
	'python>=3.8.0'
	'python-docopt>=0.6.2'
	'python-toml>=0.9.0'
)
makedepends=(
    'git'
    'python-pip'
    'python-sphinx'
    'python-sphinx-furo'
    'python-build'
    'python-flit'
)

# TODO: update source before publishing.
source=('git+ssh://csb@192.168.1.210/Users/csb/Dev/efiboot')
md5sums=('SKIP')

pkgver() {
    cd "${srcdir}/efiboot"
	git describe --long | sed 's/-/.r/;s/-/./'
}

build() {
    cd "${srcdir}/efiboot"
    make all
}

package() {
    cd "${srcdir}/efiboot"

    # Install everything. The install-all target includes docs and the license.
    #
    # Set PIP_CONFIG_FILE='/dev/null' and PIPFLAGS='--isolated' so that the
    # packager's personal pip config is ignored.
    #
    # The Makefile uses pip to install the package, but it does so without
    # touching the network or checking on dependencies. The runtime
    # dependencies are not required at build time.
    make install-all \
        PIP_CONFIG_FILE='/dev/null' \
        PIPFLAGS='--isolated' \
        DESTDIR="${pkgdir}" \
        prefix='/usr'

    # Compile the .pyc files.
    #
    # Use `-s $pkgdir` to strip build paths from compiled paths.
    python -m compileall \
        -s "${pkgdir}" \
        -o 1 \
        "${pkgdir}"/usr/lib/python*/site-packages
}
