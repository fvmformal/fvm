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

.. _designconfigurations:
design_configurations
---------------------

An example of how to define *design configurations*, which are sets of generics
to apply to a design, so we can formally verify it in specific configurations.
In the example, a simple counter is configured for different values of its
``MAX_COUNT`` generic and the formal tools are run over those diferent design
configurations.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/design_configurations

design_configurations_reachability
----------------------------------

An example that shows how reachability may change in different design
configurations. In this specific case, the ``MAX_COUNT`` generic of the counter
is changed but the counter still has 8 bits for the internal count, so the
number of bits that can be actually toggled depends on the specific design
configuration.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/design_configurations_reachability

user_defined_hdltypes
---------------------

PSL sequences can receive many datatypes as parameters. In particular, for the FVM, it is very interesting to be able to specify user-defined hdltypes, because that allows to implement the formal analogue to Transaction-Level Modeling (TLM).

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/user_defined_hdltypes

user_defined_hdltypes_in_package
--------------------------------

The same as `user_defined_hdltypes`, but the specific user-defined datatypes have
been defined in a VHDL package. This is very interesting when considering formal verification as a `complement` to simulation, because it allows us to define our transactions in a VHDL package that can be used both from a TLM testbench made in a modern simulation verification methodology and the properties for formal verification with FVM.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/user_defined_hdltypes

user_defined_hdltypes_in_external_package
-----------------------------------------

The same as `user_defined_hdltypes`, but one of the user-defined datatypes has
been defined in a VHDL package that is loaded from the PSL vunit and not from
inside the VHDL entity.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/user_defined_hdltypes_in_external_package

defining_clocks_and_resets
--------------------------

Clock and reset domains can be specified in the ``formal.py`` script, in order
to provide more information to the Clock Domain Crossing and Reset Domain
Crossing tools, and also to avoid warnings about 'inferred clocks', which are
clocks that are auto-detected by the formal tools but not specified by the
user.

This example shows how to define in the FVM framework clock signals, clock
domains, reset signals and reset domains.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/defining_clocks_and_resets

adding_drom_sources
-------------------

This example shows how to directly add wavedrom sources to the FVM Framework. A
flavor must be specified so ``drom2psl`` knows which flavor of PSL to generate.
Currently only the ``vhdl`` flavor is supported.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/adding_drom_sources

.. _assert_to_assume:
assert_to_assume
----------------

An example of how we can define properties for a submodule and afterwards
assume that they hold when proving properties for the top-level. We just change
a `.psl` file that has properties of the form ``assert named_property`` for a file
that has ``assume named_property``. In this case, assuming proven properties does
not improve the proof times for the top-level module, it is just a working example of
the technique.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/assert_to_assume

hooks
-----

Sometimes a user may find that they would like to have some extra functionality
during formal verification, but integrated within the FVM framework for
convenience. The FVM framework provides the user with the capability of
defining `hooks`, which are user-defined functions that are called before or
after a specific step:

- A `pre_hook` is a hook that is called just *before* running a specific step.
  Use :py:func:`fvm.FvmFramework.set_pre_hook` to add one.
- A `post_hook` is a hook that is called just *after* running a specific step
  Use :py:func:`fvm.FvmFramework.set_post_hook` to add one.

These hooks can be specified for a single design or for all designs (for
example, in the case of having multiple designs or using design
configurations), depending on the arguments passed to the relevant functions.

- Link: https://gitlab.com/fvmformal/fvm/-/tree/main/concepts/hooks

