Installation
============

There are two ways of installing the FVM:

Installing from pip
-------------------

The recommended way of installing the FVM is to install it from the Python
Package Index (`PyPI <https://pypi.org/>`_), using pip:

.. code-block:: zsh

   pip3 install fvmframework

.. note::

   In recent pip versions you may need to create a python virtual environment
   (venv), or else you will get an "externally-managed-environment" error when
   trying to install packages using pip.

   The following code:

   .. code-block:: zsh

      python3 -m venv venv       # Create the venv in the venv folder
      source venv/bin/activate   # Activate the newly created venv

   will create a `venv` and activate it in the current shell. With the venv
   activated, `pip3 install` will install the FVM inside the venv.

   See https://docs.python.org/3/tutorial/venv.html for details.


Installing from the git repository
----------------------------------

Installing from the repository allows to perform an editable installation
(passing the `-e` flag to `pip3 install`), so you can modify the python sources
and the changes will be immediately available.

This option is also interesting if you want a specific version that was not
tagged and pushed on PyPI, for example if you need to check out a specific
commit, branch or tag.

.. code-block:: zsh

   git clone https://gitlab.com/fvmformal/fvm.git
   pip3 install -e fvm

.. note::

   The FVM is also available on github:

   .. code-block:: zsh

      git clone https://github.com/fvmformal/fvm.git
      pip3 install -e fvm

.. note::

   The `-e` option tells python that the FVM sources reside in the recently
   cloned `fvm` directory. If you intend to remove that directory, do not use
   the `-e` flag.
