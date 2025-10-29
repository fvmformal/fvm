.. _directives:

Assert/assume/cover
===================

In formal verification, there are three main directives:

- **Assert**: The formal tool attempts to prove that a property is true.

  If the property is proven, the tool confirms that the property holds
  under all possible scenarios. If the property is disproven, the tool
  provides a counterexample trace that demonstrates a scenario where the property
  does not hold. Example:

  .. code-block:: vhdl

    -- Assert if there's an ack, there's a req
    assert always (ack = '1') -> (req = '1');

- **Assume**: The formal tool assumes that a property is true.

  Assumes are used to impose restrictions on the design's inputs, either to
  avoid cases that won't occur, focus only on valid scenarios, or simplify
  formal verification. It's important to note that assumes constrain the
  design, so they must be written carefully to avoid masking unexpected
  behavior. Example:

  .. code-block:: vhdl

    -- Assume if there's a request, reset is low. So, request will never be
    -- asserted during reset
    assume always (req = '1') -> (rst = '0');

- **Cover**: The formal tool looks for a trace that satisfies the specified
  sequence.
  
  While an assert asks "Can this fail?", a cover asks "Can this happen? How
  does it happen?". Example:

  .. code-block:: vhdl

    -- Shows the trace that leads to valid being asserted
    cover {valid = '1'};

