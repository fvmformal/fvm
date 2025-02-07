# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'fvm'
copyright = '2025, Universidad de Sevilla'
author = 'Universidad de Sevilla'
release = '0.1-dev'

# Connect to autodoc-process-docstring

undocumented_count = 0

def warn_undocumented(app, what, name, obj, options, lines):
    global undocumented_count
    if not lines:  # No docstring found
        print(f"WARNING: {what} '{name}' is undocumented!")
        undocumented_count += 1

def print_undocumented_count(app, exception):
    global undocumented_count
    print(f"\nTotal undocumented members: {undocumented_count}")

def setup(app):
    app.connect("autodoc-process-docstring", warn_undocumented)
    app.connect("build-finished", print_undocumented_count)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",       # Extract docstrings
    "sphinx.ext.napoleon",      # Support Google/NumPy-style docstrings
    "sphinx.ext.viewcode",      # Add links to source code
    "sphinx_autodoc_typehints", # Show type hints
    #"sphinx.ext.coverage",      # Report documentation coverage (we are not
      #using it, because when using autodoc, coverage believes everything is
      #documented)
]

autodoc_typehints = "description"  # Type hints appear in descriptions

# Having these options will warn about missing docstrings
autodoc_default_options = {
    "members": True,         # Include documented members (classes, functions, etc) in documentation output
    "undoc-members": True,   # Include undocumented members (classes, functions, etc) in documentation output
    "private-members": True, # Check also private methods of classes
    "special-members": "__init__", # Include special methods as needed
    "show-inheritance": True,
}


# For sphinx.ext.coverage
#coverage_show_missing_items = True

#nitpicky = True  # Will throw warnings if docstrings are missing

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
