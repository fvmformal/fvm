.. _installation:

Installation
============

There are two ways of installing the FVM:

Installing from pip
-------------------

The recommended way of installing the FVM is to install it from the Python
Package Index (`PyPI <https://pypi.org/>`_), using pip:

.. code-block:: zsh

   pip3 install --pre fvm-formal

Here, we use the ``--pre`` flag to tell pip to include development and release
candidate versions in its search. After ``1.0.0`` becomes stable, we can stop
using the ``--pre`` flag.

.. note::

   In recent pip versions you may need to create a python virtual environment
   (``venv``), or else you will get an "externally-managed-environment" error
   when trying to install packages using pip.

   The following code:

   .. code-block:: zsh

      python3 -m venv venv       # Create the venv in the venv folder
      source venv/bin/activate   # Activate the newly created venv

   will create a ``venv`` and activate it in the current shell. With the
   ``venv`` activated, ``pip3 install`` will install the FVM inside the venv.

   See https://docs.python.org/3/tutorial/venv.html for details.


Installing from the git repository
----------------------------------

Installing from the repository allows to perform an editable installation
(passing the ``-e`` flag to ``pip3 install``), so you can modify the python sources
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

   The ``-e`` option tells python that the FVM sources reside in the recently
   cloned ``fvm`` directory. If you intend to remove that directory, you should
   remove the ``-e`` flag, but of course in that case the installation will not
   be editable.

Non-python dependencies
-----------------------

All python dependencies should be correctly managed by ``pip`` when you install
the FVM. Nevertheless, there are two non-python dependencies which you should
make sure you have in your system:

- **The actual formal tools:** The FVM currently only supports the Questa
  formal tools (and the Questa OneSim simulator to compute simulation code
  coverage). You should have the tools installed in the system and the
  executables (``qverify``, ``vlib``, ``vcom``, ``vsim``, etc) in your
  ``PATH``, and of course a valid license.

- **Java:** The FVM uses `Allure Report <https://allurereport.org/>`_ to create
  beautiful HTML reports with the formal verification results. The FVM
  framework will download and use a specific release of Allure Report when
  needed. This framework is based on Java, so if you want to be able to create
  and view the reports you will need to install it, for example you can install
  the Open Java Development Kit (OpenJDK):

  - On Debian 13:

    .. code:: zsh

       sudo apt install openjdk-11-jre

  - On Rocky Linux 8:

    .. code:: zsh

       sudo yum install java-1.8.0-openjdk
