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
source=('git+file:///home/csb/efiboot')
md5sums=('SKIP')

pkgver() {
    cd "${srcdir}/efiboot"

    # The version follows the format `{tag}.r{count}.{commit}` where:
    # - {tag} is the most recent tag, minus any leading `v` character,
    # - {count} is the number of commits since the tag,
    # - {commit} is the commit hash.
    #
    # If we are at an early commit, before the first tag, `git describe --long`
    # will fail. So we assume a base tag of 0.0.0.
    local version
	version=$(git describe --long | sed 's/^v//;s/-/.r/;s/-/./' || true)
    if [[ -z "$version" ]]
    then
        version="0.0.0.r$(git rev-list --count HEAD).$(git describe --always)"
    fi
    echo $version
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
