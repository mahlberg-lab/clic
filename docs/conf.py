# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import os.path
import subprocess
import sys

server_dir = os.path.abspath('../server')
sys.path.insert(0, server_dir)


# -- Project information -----------------------------------------------------

project = 'CLiC User Guide'
copyright = '%s, Michaela Mahlberg, Viola Wiegand, Jamie Lentin & Anthony Hennessey' % (
    subprocess.check_output("git log -1 --format=%ai".split()).decode('utf8').split('-', 1)[0],
)
author = 'Michaela Mahlberg, Viola Wiegand, Jamie Lentin & Anthony Hennessey'

# The short X.Y version
version = subprocess.check_output("git rev-parse --abbrev-ref HEAD".split()).decode('utf8').strip()
# The full version, including alpha/beta/rc tags
release = subprocess.check_output("git describe --abbrev=0".split()).decode('utf8').strip()


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['ntemplates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['lib', 'lib64']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None

# -- Numbering figures -------------------------------------------------------
numfig = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'clic-userguidedoc'


# -- Options for LaTeX output ------------------------------------------------

# Add CLiC logo to title page
# NB: Ideally we would use sphinxcontrib-svg2pdfconverter, but rsvg-convert not available:
# https://github.com/rtfd/readthedocs-docker-images/pull/79
latex_logo = 'clic-logo.pdf'

# Include the appendices that are hidden in index.rst
latex_appendices = ['appendices', 'glossary']

latex_elements = {
    'preamble': '''
\\addto\\captionsenglish{\\renewcommand{\\bibname}{References}}
    ''',

    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'clic-userguide.tex', 'CLiC Documentation',
     'Michaela Mahlberg', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'clic-userguide', 'CLiC Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'clic-userguide', 'CLiC Documentation',
     author, 'clic-userguide', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']

# -- Autodoc configuration ---------------------------------------------------
import sphinx.apidoc

def run_apidoc(_):
    """
    Auto-run sphinx-autodoc
    """
    from sphinx.ext import apidoc

    if not os.path.isdir('module'):
        os.makedirs('module')
    apidoc.main([
        "--doc-project", "Module documentation",
        "--force",
        "--separate",
        "--no-headings",
        "--maxdepth", "10",
        "-o", "module",
        server_dir,
        os.path.join(server_dir, 'appconfig.py'),
        os.path.join(server_dir, 'clic', 'uwsgi.py'),
        os.path.join(server_dir, 'conftest.py'),
        os.path.join(server_dir, 'tests', '*.py'),
        os.path.join(server_dir, 'setup.py'),
    ])

autodoc_mock_imports = """
appconfig
numpy pandas
pybtex
psycopg2
icu
unidecode
flask flask_cors
""".split()

# ----------------------------------------------------------------------------

def setup(app):
    app.connect('builder-inited', run_apidoc)
