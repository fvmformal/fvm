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

The concepts are described below, with a link to their respective folders in the repository.

To run any of them, just execute the following command from the root folder of the repository:

.. code-block:: zsh

   python3 concepts/<conceptname>/formal.py

Where `<conceptname>` is the name of the proof of concept you want to run.

parameterized_sequences
-----------------------

An example of how we can define a sequence with parameters, and afterwards when
can assign values to those parameters in the properties we define reusing the
sequence. This is a better way of increasing the abstraction level for defining
properties.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/parameterized_sequences

inheriting_vunits
-----------------

An example on how we can define a sequence in a .psl file and include it (with
the inherit keyword) inside other PSL code. This is important to better
leverage our wavedrom-to-psl converter.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/inheriting_vunits

inheriting_multiple_vunits
--------------------------

This is the same as `inheriting_vunits`, but demonstrates that we can include
sequences defined in multiple PSL files.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/inheriting_multiple_vunits

parameterized_properties
------------------------

An example of how to define a property that receives parameters using the
keyword property, and how to use it in verification directives like assert.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/parameterized_properties


multiple_designs
----------------

This is an example of passing a list of toplevels to the FVM framework, which
tells it to run all the tests on each of the designs specified in the list.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/multiple_designs

user_defined_hdltypes
---------------------

PSL sequences can receive many datatypes as parameters. In particular, for the FVM, it is very interesting to be able to specify user-defined hdltypes, because that allows to implement the formal analogue to Transaction-Level Modeling (TLM).

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/user_defined_hdltypes

user_defined_hdltypes_in_package
--------------------------------

The same as user_defined_hdltypes, but the specific user-defined datatypes have
been defined in a VHDL package. This is very interesting when considering formal verification as a `complement` to simulation, because it allows us to define our transactions in a VHDL package that can be used both from a TLM testbench made in a modern simulation verification methodology and the properties for formal verification with FVM.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/user_defined_hdltypes

user_defined_hdltypes_in_external_package
-----------------------------------------

The same as user_defined_hdltypes, but one of the user-defined datatypes has
been defined in a VHDL package that is loaded from the PSL vunit and not from
inside the VHDL entity.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/user_defined_hdltypes_in_external_package

assert_to_assume
----------------

An example of how we can define properties for a submodule and afterwards
assume that they hold when proving properties for the top-level. We just change
a `.psl` file that has properties of the form assert named_property for a file
that has assume named_property. In this case, assuming proven properties does
not improvethe proof times for the top-level module, is a working example of
the technique.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/assert_to_assume

.. _designconfigurations:

design_configurations
---------------------

.. todo::

   actually write this


