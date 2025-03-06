#!/bin/bash
set -eu
# apt install autoconf automake libtool

mkdir -p "$(dirname $0)/build-workdir" && cd "$(dirname $0)/build-workdir"

# ==== Configure Environment ==================================================
# NB: Python version has to match pyodide's bundled version, compile if necessary with
# https://docs.brucerenner.com.au/posts/Debian-Buster-Python-Install/
python3.12 -m venv .
source ./bin/activate
pip install pyodide-build
[ -d emsdk ] || git clone https://github.com/emscripten-core/emsdk.git
rm -r -- .pyodide-xbuildenv-* || true
PYODIDE_EMSCRIPTEN_VERSION=$(pyodide config get emscripten_version)
./emsdk/emsdk install ${PYODIDE_EMSCRIPTEN_VERSION}
./emsdk/emsdk activate ${PYODIDE_EMSCRIPTEN_VERSION}
PYODIDE_EMSCRIPTEN_SYSROOT="$(readlink -f emsdk/upstream/emscripten/cache/sysroot/)"
source emsdk/emsdk_env.sh

# ==== Build thinc ============================================================
[ -d thinc ] && rm -rf -- thinc
git clone https://github.com/explosion/thinc --depth 1 --branch release-v8.3.4
pushd thinc
pyodide build
popd

# ==== Build marisa-trie ==========================================================
[ -d marisa-trie-lib ] && rm -rf -- marisa-trie-lib
git clone https://github.com/s-yata/marisa-trie.git --depth 1 --branch v0.2.6 marisa-trie-lib
pushd marisa-trie-lib
autoreconf -i
emconfigure ./configure --prefix=${PYODIDE_EMSCRIPTEN_SYSROOT}
emmake make
emmake make install
popd

[ -d marisa-trie ] && rm -rf -- marisa-trie
git clone https://github.com/pytries/marisa-trie.git --depth 1 --branch 1.2.1 marisa-trie
pushd marisa-trie
pyodide build
popd

# ==== Build cymem =============================================================
[ -d cymem ] && rm -rf -- cymem
git clone https://github.com/explosion/cymem --depth 1 --branch release-v2.0.11 cymem
pushd cymem
pyodide build
popd

# ==== Build murmurhash =======================================================
[ -d murmurhash ] && rm -rf -- murmurhash
git clone https://github.com/explosion/murmurhash --depth 1 --branch release-v1.0.12 murmurhash
pushd murmurhash
pyodide build
popd

# ==== Build preshed ==========================================================
[ -d preshed ] && rm -rf -- preshed
git clone https://github.com/explosion/preshed --depth 1 --branch v3.0.9 preshed
pushd preshed
pyodide build
popd

# ==== Build blis =============================================================
[ -d blis ] && rm -rf -- blis
git clone https://github.com/explosion/cython-blis --depth 1 --branch release-v1.2.0 blis
pushd blis
BLIS_ARCH=generic pyodide build
popd

# ==== Build Spacy ============================================================
[ -d spaCy ] && rm -rf -- spaCy
git clone https://github.com/explosion/spaCy --depth 1 --branch release-v3.8.4
pushd spaCy
pyodide build
popd

# ==== Build Srsly ============================================================
[ -d srsly ] && rm -rf -- srsly
git clone https://github.com/explosion/srsly --depth 1 --branch release-v2.5.1
pushd srsly
pyodide build
popd

# ==== Build libICU ===========================================================
# NB: Emscripten offers USE_ICU, but usage is vague, and there's no ICU data available anyway:
# https://github.com/emscripten-core/emscripten/issues/14754
# https://unicode-org.atlassian.net/browse/ICU-21437

wget -c https://github.com/unicode-org/icu/archive/refs/tags/release-76-1.tar.gz
tar -zxf release-76-1.tar.gz
pushd "icu-release-76-1/icu4c/source"
# Create native build so ICU tools are available
./runConfigureICU Linux && make
# Create filters file to create a manageable icudt__.dat, default is ~30MB
# https://unicode-org.github.io/icu/userguide/icu_data/buildtool.html
pip install jsonschema  # Validate filters.json on ./configure
cat <<EOF > filters.json
{
  "localeFilter": {
    "filterType": "language",
    "includelist": [
      "en",
      "de"
    ]
  }
}
EOF
# NB: Set CXXFLAGS="-fPIC" / --enable-static=yes to statically compile libICU with pyICU
# https://unicode-org.github.io/icu/userguide/icu4c/packaging.html#link-to-icu-statically
# https://unicode-org.atlassian.net/browse/ICU-21437
# NB: --with-data-packaging=archve creates a combined icudt__.dat file, which will be found:
#   * Location set at runtime with u_setDataDirectory() (which PyICU has no facility for)
#   * env_var ICU_DATA (which our example will do)
#   * C preprocessor variable ICU_DATA_DIR (i.e. ICU_DATA_DIR below, set assuming it's inside wheel)
# Other options are static (manually populate with u_setCommonData()) or library (libICU will try to load shared library)
# https://unicode-org.github.io/icu/userguide/icu_data/#icu-data-directory
# https://unicode-org.github.io/icu/userguide/icu/howtouseicu.html
# https://unicode-org.github.io/icu/userguide/icu/design.html
ICU_DATA_FILTER_FILE=filters.json  \
    CXXFLAGS='-fPIC -DICU_DATA_DIR=\"/lib/python3.12/site-packages/icu\"' \
    CFLAGS="-fPIC" PKG_CONFIG_LIBDIR=${PYODIDE_EMSCRIPTEN_SYSROOT}/lib/pkgconfig \
    emconfigure ./configure \
    --prefix=${PYODIDE_EMSCRIPTEN_SYSROOT} --with-cross-build=`pwd` \
    --enable-static=yes --enable-shared=no --target=wasm32-unknown-emscripten \
    --with-data-packaging=archive \
    --enable-icu-config --enable-extras=no --enable-tools=no --enable-samples=no --enable-tests=no
emmake make clean install
rm data/packagedata || true  # Force rebuild of package data, placeholder not removed by clean
emmake make -C data
popd

# ==== Build icudata ==========================================================
mkdir -p icudata/icudata
pushd icudata
cat <<EOF > pyproject.toml
[project]
name = "icudata"
version = "76.1"
EOF
cat <<EOF > MANIFEST.in
include icudata/*.dat
EOF
cp ../icu-release-76-1/icu4c/source/data/out/*.dat icudata/
python3.12 -m build
popd

# ==== Build PyICU ============================================================
[ -d pyicu ] && rm -rf -- pyicu
git clone https://gitlab.pyicu.org/main/pyicu
pushd pyicu
cat <<EOF | git apply -
diff --git a/setup.py b/setup.py
index 3f03c5e..d38e75e 100644
--- a/setup.py
+++ b/setup.py
@@ -47,13 +47,13 @@ def configure_with_icu_config(flags, config_args, label):

 def configure_with_pkg_config(flags, config_args, label):
     try:
-        output = check_output(('pkg-config',) + config_args + ('icu-i18n',)).strip()
+        output = check_output(('emconfigure', 'pkg-config',) + config_args + ('icu-i18n',)).strip()
         if sys.version_info >= (3,):
             output = str(output, 'ascii')
         flags.extend(output.split())
         if output:
             print('Adding %s="%s" from %s' % (label, output,
-                                              find_executable('pkg-config')))
+                                              find_executable('emconfigure')))
     except:
         print('Could not configure %s with pkg-config' %(label))
         raise
@@ -93,7 +93,7 @@ except:
         CONFIGURE_WITH_ICU_CONFIG[platform] = True
     except:
         try:
-            ICU_VERSION = check_output(('pkg-config', '--modversion', 'icu-i18n')).strip()
+            ICU_VERSION = check_output(('emconfigure', 'pkg-config', '--modversion', 'icu-i18n')).strip()
             CONFIGURE_WITH_PKG_CONFIG[platform] = True
         except:
             raise RuntimeError('''
EOF
rm -r ./build || true
ICU_VERSION=76.1 pyodide build
popd
