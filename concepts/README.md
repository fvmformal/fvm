# Proof of concepts for FVM

These are some proof of concepts we made during the first stages of the
project, during the definition of the methodology

## Contents

- ``transactions_deprecated``: a first example of how to increase the
  abstraction level at which to write properties, but it requires extra VHDL
  code in the PSL file and doesn't seem to scale well to multi-cycle
  transactions, so it is kind of a dead end. It will remain here for historical
  reasons, since it is also good to know what didn't work
- ``parameterized_sequences``: an example of how we can define a sequence with
  parameters, and afterwards when can assign values to those parameters in the
  properties we define reusing the sequence. This is a better way of increasing
  the abstraction level for defining properties
- ``inheriting_vunits``: an example on how we can define a sequence in a
  ``.psl`` file and include it (with the ``inherit`` keyword) inside other PSL
  code. This is important to better leverage our wavedrom-to-psl converter
- ``inheriting_multiple_vunits``: this is the same as ``inheriting_vunits``,
  but demonstrates that we can include sequences defined in multiple PSL files
- ``parameterized_properties``: an example of how to define a property that
  receives parameters using the keyword ``property``, and how to use it in
  verification directives like ``assert``
- ``multiple_designs``: this is an example of passing a list of toplevels to
  the FVM framework, which tells it to run all the tests on each of the designs
  specified in the list
- ``user_defined_hdltypes``: specify a user-defined ``hdltype`` in a PSL
  ``sequence``
- ``user_defined_hdltypes_in_package``: the same as ``user_defined_hdltypes``,
  but the specific user-defined datatype has been defined in a VHDL package
