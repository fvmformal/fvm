.. _concepts:

How to do specific things with PSL and the FVM
==============================================

.. note::

   If you are already familiar with PSL or you want to learn by looking at how
   the example designs have been verified, you may skip this section and go
   directly to the :ref:`examples` section

The FVM repository provides, in its `concepts` folder, some simple proofs of
concept on how to do specific things with PSL and the methodology. While it is
advisable to get acquainted with these concepts sooner or later, users may skip
towards the examples to see these concepts in action in bigger designs, and
come back if there is something they don't understand.

All of these examples are self-sustaining and have their own `formal.py` script
to run them, so users are encouraged to take a look at their code.

parameterized_sequences
-----------------------

.. todo::

   Add link to code in repository

An example of how we can define a sequence with parameters, and afterwards when
can assign values to those parameters in the properties we define reusing the
sequence. This is a better way of increasing the abstraction level for defining
properties.

inheriting_vunits
-----------------

.. todo::

   Add link to code in repository

An example on how we can define a sequence in a .psl file and include it (with
the inherit keyword) inside other PSL code. This is important to better
leverage our wavedrom-to-psl converter.

.. todo::

   Add code snippet here

inheriting_multiple_vunits
--------------------------

.. todo::

   Add link to code in repository

this is the same as inheriting_vunits, but demonstrates that we can include
sequences defined in multiple PSL files.

.. todo::

   Add code snippet here

parameterized_properties
------------------------

.. todo::

   Add link to code in repository

an example of how to define a property that receives parameters using the
keyword property, and how to use it in verification directives like assert.

.. todo::

   Add code snippet here


multiple_designs
----------------

.. todo::

   Add link to code in repository

This is an example of passing a list of toplevels to the FVM framework, which
tells it to run all the tests on each of the designs specified in the list.

.. todo::

   Add code snippet here

user_defined_hdltypes
---------------------

.. todo::

   Add link to code in repository

Specify a couple of user-defined hdltypes in a PSL sequence.

.. todo::

   Add code snippet here

user_defined_hdltypes_in_package
--------------------------------

.. todo::

   Add link to code in repository

The same as user_defined_hdltypes, but the specific user-defined datatypes have
been defined in a VHDL package.

.. todo::

   Add code snippet here

user_defined_hdltypes_in_external_package
-----------------------------------------

.. todo::

   Add link to code in repository

The same as user_defined_hdltypes, but one of the user-defined datatypes has
been defined in a VHDL package that is loaded from the PSL vunit and not from
inside the VHDL entity.

.. todo::

   Add code snippet here

assert_to_assume
----------------

.. todo::

   Add link to code in repository

An example of how we can define properties for a submodule and afterwards
assume that they hold when proving properties for the top-level. We just change
a `.psl` file that has properties of the form assert named_property for a file
that has assume named_property. In this case, assuming proven properties does
not improvethe proof times for the top-level module, is a working example of
the technique.

.. todo::

   Add code snippet here

