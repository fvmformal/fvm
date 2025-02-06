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

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",      # Extract docstrings
    "sphinx.ext.napoleon",     # Support Google/NumPy-style docstrings
    "sphinx.ext.viewcode",     # Add links to source code
    "sphinx_autodoc_typehints" # Show type hints
]

autodoc_typehints = "description"  # Type hints appear in descriptions

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
