Installation
============

How to install the FVM

Installing from pip
-------------------

.. warning::

   This option is not currently available, since the package hasn't been
   uploaded to pip yet

.. code-block:: zsh

   pip3 install fvm

Installing from the repository
------------------------------

This option is interesting if you want a specific version, since you can check
out the specific commit, branch or tag you want

.. todo::

   Update path to repository when the FVM is published

.. code-block:: zsh

   git clone path/to/fvm.git
   pip3 install -e fvm

Installing using poetry
-----------------------

FVM uses `poetry <https://python-poetry.org/>`_ to manage its dependencies. The
repository includes a `Makefile` with which to install the FVM using poetry. By
default, the install target creates a python `venv
<https://docs.python.org/3/library/venv.html>`_ (virtual environment) in which
it will install poetry, all dependencies and the FVM.

.. todo::

   Update path to repository when the FVM is published

.. code-block:: zsh

   git clone path/to/fvm.git
   cd fvm
   make install
