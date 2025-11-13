.. _drom2psl:

drom2psl
========

There are three ways to use the ``drom2psl`` tool:

Adding drom sources
-------------------

The functions :py:func:`fvm.FvmFramework.add_drom_source` and
:py:func:`fvm.FvmFramework.add_drom_sources` allow to respectively add
one or multiple wavedrom sources, in JSON format, to an FVM project.

This is the recommended way of working with wavedrom sources if no
modifications are needed on the generated PSL outputs.

During the *setup* stage of the FVM framework, all the drom sources will be
converted to PSL files, which will be included in the generated scripts for the
``prove`` step.

.. autofunction:: fvm.FvmFramework.add_drom_source

.. autofunction:: fvm.FvmFramework.add_drom_sources


Manually running drom2psl
-------------------------

Alternatively, the user can just run the ``drom2psl`` executable to:

.. argparse::
   :module: fvm.drom2psl.generator
   :func: create_parser
   :prog: drom2psl

Calling the drom2psl.generator function
---------------------------------------

The third way of invoking ``drom2psl`` is by calling the
:py:func:`fvm.drom2psl.generator.generator` function from any python
script:

.. autofunction:: fvm.drom2psl.generator.generator

