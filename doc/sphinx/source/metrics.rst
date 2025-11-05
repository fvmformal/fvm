.. _metrics:

Coverage metrics in formal verification
=======================================

In formal verification, coverage metrics measure **how completely** your formal
properties have explored the design.

Formal verification doesn't rely on test vectors, it uses mathematical proofs.
So, coverage metrics help you understand how well your properties cover the
design's behavior.

The main coverage metrics are:

- **Assertion coverage**: Measures the **percentage of assertions that have been
  proven** during formal verification. Since assertions are a formal
  specification of expected behavior, high assertion coverage indicates that
  your properties are effectively checking the design's correctness. FVM 
  shows the number of proven assertions versus the total after execution.

- **Reachability**: It shows which elements of the design are achievable and
  which are not. It helps to analyze which parts of the design are unused. FVM
  shows reachability analysis in the ``reachability`` step and
  ``prove.formalcover`` step.

- **Observability**: It indicates which elements of the design can be observed
  by the properties. It helps to identify parts of the design that are not being
  checked by the properties. FVM shows observability analysis in the
  ``prove.formalcover`` step.

- **Signoff**: It is the primary metric for measuring the completeness of
  properties. It is the `observability` result after excluding the
  unreachables from `reachability`, thus obtaining what the properties have
  observed of what was reachable. This is the main result of FVM in
  ``prove.formalcover``.

- **Bounded reachability**: It's like signoff but with bounded proofs
  (assertions that hold up to a certain depth in the design, but haven't been
  proven or disproven for all time). FVM shows it in the
  ``prove.formalcover`` step.

- **Simulation coverage**: Although not typically used in formal verification,
  FVM simulates the covers and counterexamples of the assertions in the
  ``prove`` step during the ``prove.simcover`` step. This provides a metric for
  evaluating the completeness of the covers, as the previous metrics only
  consider the assertions.

- **Overconstraint coverage**: It measures **how much the design has been
  constrained by assumes**. Excessive use of assumes can lead to overconstraining
  the design, which may hide potential issues. **FVM doesn't currently provide this
  metric, but it's intended to be added in future releases.**

- **Mutation coverage**: It evaluates the **effectiveness of properties by
  introducing small changes (mutations)** to the design and checking if the
  properties can detect these changes. **FVM doesn't currently provide this
  metric, but it's intended to be added in future releases.**

- **More types of coverage may be included in the future.**