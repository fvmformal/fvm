# Proof of concepts for FVM

These are some proof of concepts we made during the first stages of the
project, during the definition of the methodology

## Contents

- [``parameterized_sequences``](parameterized_sequences): an example of how we can define a sequence with
  parameters, and afterwards when can assign values to those parameters in the
  properties we define reusing the sequence. This is a better way of increasing
  the abstraction level for defining properties
- [``inheriting_vunits``](inheriting_vunits): an example on how we can define a sequence in a
  ``.psl`` file and include it (with the ``inherit`` keyword) inside other PSL
  code. This is important to better leverage our wavedrom-to-psl converter
- [``inheriting_multiple_vunits``](inheriting_multiple_vunits): this is the same as ``inheriting_vunits``,
  but demonstrates that we can include sequences defined in multiple PSL files
- [``parameterized_properties``](parameterized_properties): an example of how to define a property that
  receives parameters using the keyword ``property``, and how to use it in
  verification directives like ``assert``
- [``multiple_designs``](multiple_designs): this is an example of passing a list of toplevels to
  the FVM framework, which tells it to run all the tests on each of the designs
  specified in the list
- [``user_defined_hdltypes``](user_defined_hdltypes): specify a couple of user-defined ``hdltype`` in a PSL
  ``sequence``
- [``user_defined_hdltypes_in_package``](user_defined_hdltypes_in_package): the same as ``user_defined_hdltypes``,
  but the specific user-defined datatypes have been defined in a VHDL package
- [``user_defined_hdltypes_in_external_package``](user_defined_hdltypes_in_external_package): the same as ``user_defined_hdltypes``,
  but one of the user-defined datatypes has been defined in a VHDL package that
  is loaded from the PSL vunit and not from inside the VHDL entity
- [``assert_to_assume``](assert_to_assume): an example of how we can define
  properties for a submodule and afterwards assume that they hold when proving
  properties for the top-level. We just change a ``.psl`` file that has
  properties of the form ``assert named_property`` for a file that has ``assume
  named_property``. This example doesn't improve the proof times for the
  top-level module, but at least is a working example on how to try this
  approach
