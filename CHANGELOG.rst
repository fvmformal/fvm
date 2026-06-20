ChangeLog
=========

Changes added to each version of this project will be documented in this file

The format used here is a ``.rst`` version of the `Keep a
Changelog <https://keepachangelog.com/en/1.1.0/>`_ format, with
``Added``/``Changed``/``Fixed``/``Deprecated``/``Removed`` change categories.

This project adheres to `Semantic
Versioning <https://semver.org/spec/v2.0.0.html>`_.

.. note::

  If you want to access a specific release, you can find:

  - All releases on PyPI: https://pypi.org/project/fvm-formal/#history
  - All releases on Gitlab: https://gitlab.com/fvmformal/fvm/-/tags
  - All releases on the Github mirror: https://github.com/fvmformal/fvm/tags
  - Documentation for all releases: https://fvm.us.es/doc/ (Use the 'Other
    Versions' selector at the bottom left and click on the version you want)

Development version - Unreleased
--------------------------------

:Changed:     Dashboards are now generated in `fvm_dashboard` output subdirectory
:Changed:     Pin examples/ipv6 version of cloned code
:Changed:     Small typo/expression changes throughout the documentation
:Changed:     Improved comments in the examples in ``examples/`` and ``concepts/``
:Fixed:       Add missing spaces in generated parameters when defining cutpoints
:Fixed:       Fixed error in ``prove.simcover`` when using ``--guinorun``

1.0.0rc3 - 18-06-2026
---------------------

:Added:       Use `nox <https://nox.thea.codes/en/stable/index.html>`_ inside CI
              to run the test suite for all python versions between 3.9 and 3.15
:Added:       Use `deptry <https://deptry.com/>`_  inside CI to detect unused and
              undeclared dependencies
:Added:       Added test to detect API-breaking changes, using `griffe
              <https://mkdocstrings.github.io/griffe/>`_
:Changed:     Improve CI pipeline times by reusing docker images
:Changed:     Improved 'remove_from_path' tests in test suite
:Fixed:       Fix build of internal API doc

1.0.0rc2 - 24-02-2026
---------------------

:Added:    Add ``CHANGELOG.rst`` (this file)
:Added:    Add minimalist copyright header to sources
:Added:    Add ``NOTICE`` file
:Fixed:    Improved documentation
:Fixed:    Typo in docstring of ``std_vhdl_std``
:Fixed:    Add ``packaging`` as dependency
:Removed:  Remove ``pathlib`` as dependency

1.0.0rc1 - 22-10-2025
---------------------

- First public release
