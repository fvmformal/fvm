.. _metrics:

Coverage metrics in formal verification
=======================================

In formal verification, coverage metrics measure **how completely** your formal
properties have explored the design.

Formal verification doesn't rely on test vectors, it uses mathematical proofs.
So, coverage metrics help you understand how well your properties cover the
design's behavior.

The main coverage metrics are:

Supported by FVM
----------------

- **Assertion coverage**: Measures the **percentage of assertions that have
  been proven** during formal verification. Since assertions are a formal
  specification of expected behavior, high assertion coverage indicates that
  your properties are effectively checking the design's correctness. After
  execution of the property checker during the ``prove`` step, FVM shows the
  number of proven assertions with respect to the total.

- **Reachability**: This metric shows which elements of the design are
  reachable and which are not. It helps to analyze which parts of the design
  are made of redundant or unusable code, such as statements inside redundant
  if/elsif conditions. FVM shows reachability analysis in the ``reachability``
  step and ``prove.formalcover`` step.

- **Observability**: It indicates which elements of the design can be observed
  by the properties. It helps to identify parts of the design that are not being
  checked by the properties. FVM shows observability analysis in the
  ``prove.formalcover`` step.

- **Signoff**: It is the primary metric for measuring the completeness of
  properties. It is the `observability` result after excluding the unreachables
  from `reachability`, thus obtaining the proportion of what the properties
  have observed from what was reachable. This is the main result of FVM in
  ``prove.formalcover``.

- **Bounded reachability**: It's like signoff but with bounded proofs, which
  are assertions that hold up to a certain depth in the design, but haven't
  been proven or disproven for all time. FVM shows it in the
  ``prove.formalcover`` step.

- **Simulation coverage**: Although not typically used in formal verification,
  FVM simulates the reached cover statements and any counterexamples found for
  the assertions in the ``prove`` step during the ``prove.simcover`` step. This
  provides a metric for evaluating the completeness of the cover directives, as
  the previous metrics only consider the assertions. It also servers to bridge
  the gap between simulation and formal verification, by providing a metric
  which is widely known to verification engineers, which is simulation code coverage.

Not supported by FVM yet
------------------------

- **Overconstraint coverage**: It measures **how much the design has been
  constrained by assumptions**. Excessive use of assumes can lead to overconstraining
  the design, which may hide potential issues. **FVM doesn't currently provide this
  metric, but it's intended to be added in future releases.**

- **Mutation coverage**: It evaluates the **effectiveness of properties by
  introducing small changes (mutations)** to the design and checking if the
  properties can detect these changes. **FVM doesn't currently provide this
  metric, but it's intended to be added in future releases.**

- **More types of coverage may be included in the future.**
