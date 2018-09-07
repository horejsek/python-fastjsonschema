# -*- coding: utf-8 -*-

import time
import sys

sys.path.insert(0, '.')
sys.path.insert(0, '..')

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinxtogithub',
]

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'fastjsonschema'
copyright = u'2016-{}, Michal Horejsek'.format(time.strftime("%Y"))

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = ''
# The full version, including alpha/beta/rc tags.
release = version

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'pastie'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    '**': [
        'localtoc.html',
        'relations.html',
        'searchbox.html',
    ]
}

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'alabaster'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# http://alabaster.readthedocs.io/en/latest/customization.html
html_theme_options = {
    'font_family': 'Arial, sans-serif',
    'head_font_family': 'Arial, sans-serif',
    'page_width': '1000px',
    'show_related': True,
}

# This config value contains the locations and names of other projects that should be linked to in this documentation.
intersphinx_mapping = {
}
