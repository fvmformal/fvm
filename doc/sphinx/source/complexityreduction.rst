.. _complexityreduction:

*************************************
Techniques to reduce proof complexity
*************************************

After verifying your first trivial examples, you will encounter designs which
are not very tractable using formal verification. Fortunately, there are number
of techniques than can be used to reduce the complexity of the formal proofs.

.. todo::

   Describe the techniques here, and link to the examples in the repository.
   Maybe we can even make a table, as we did in the FVM paper. But we cannot
   make exactly the same table now, because the paper can't have been
   previously published. So maybe we make a subsection for each technique and
   add the table after the paper is published

Cutpoint
========

Definition
----------

A **cutpoint** is an individual signal which is left as a *free variable* for
formal verification, meaning that the driving logic for that signal is no
longer considered to assign its value: instead, the formal solver can choose
any value(s) it wants for the specific signal.

Nevertheless, we can still write some properties (for example, *assumptions*),
to constrain the values the signal can take.

When to use it
--------------

It is interesting to use a **cutpoint** when there is a signal that takes a
very high number of clock cycles to reach an interesting value.

For example, in the case of a 64-bit counter, it is not feasible to wait around
:math:`1.8 \times 10^{19}` clock cycles for the counter to overflow, but we can
**cutpoint** its output and let the solver give any value it considers. If our
design properties are proven after adding the cutpoint, then it means that they
hold for any possible value of the 64-bit counter's output.

How to do it
------------

Just use the function :py:func:`fvm.FvmFramework.cutpoint` and pass to it at
least the signal you want to cutpoint. Use it for all the signals you need to
convert into free variables. If needed, a python :code:`for` loop can be used
to apply the function to multiple signals.

.. code-block:: python

   from fvm import FvmFramework

   fvm.add_vhdl_source("concepts/cutpoint_example/counter.vhd")
   fvm = FvmFramework()
   fvm.cutpoint("Q")

The function can receive more arguments than just the signal name so don't
forget to check the function documentation:
:py:func:`fvm.FvmFramework.cutpoint`

Example
-------

A complete example is provided in `<concepts/cutpoint_example>`

.. todo::

   Add link to public repo

Blackbox
========

Definition
----------

A **blackbox** is when we ignore a complete submodule for formal verification
purposes. The submodule, then, becomes literally a black box because we are
ignoring all that is inside it, and leaving the values of its outputs to the
formal solver.

If needed, we can write properties (typically *assumptions*) to constraint the
black box's outputs.

**Blackboxing** a module would be equivalent to **cutpointing** all its output
signals.

When to use it
--------------

It is interesting to **blackbox** submodules that have already been verified
when their presence adds a lot of complexity to the formal proofs.

An example of entities that are typically blackboxed are memories. When an
internal memory is blackboxed, it will output any data the solver wants,
independently of its inputs (such as input data or address). If our properties
hold for any value of the 'stored' information, then blackboxing the memory is
a good way of making the proof more tractable.

How to do it
------------

.. todo::

   Add links to public repo

If you want to blackbox all instances of a specific entity, use the function
:py:func:`fvm.FvmFramework.blackbox` and pass to it the entity name.

.. code-block:: python

   from fvm import FvmFramework

   fvm = FvmFramework()
   fvm.add_vhdl_sources("concepts/blackbox_instance/*.vhd")
   fvm.set_toplevel('dualcounter')
   fvm.blackbox('counter')

If you want to blackbox a specific instance of an entity, you need to use the
function :py:func:`fvm.FvmFramework.blackbox_instance`, providing the entity
name as argument.

.. code-block:: python

   from fvm import FvmFramework

   fvm = FvmFramework()
   fvm.add_vhdl_sources("concepts/blackbox_instance/*.vhd")
   fvm.set_toplevel('dualcounter')
   fvm.blackbox_instance('counter0')
   fvm.blackbox_instance('counter1')

Example
-------

An example of blackboxing an entity is provided in
`<concepts/blackbox_example>`

An example of blackboxing instances is provided in
`<concepts/blackbox_instance>`

Counter abstraction
===================

Definition
----------

**Counter abstraction** happens when we convert a wide counter (such as a
64-bit counter) into a smaller counter, that has *just enough states* to
represent interesting behavior.

When to use it
--------------



How to do it
------------

**Cutpoint** the counter's count and add assumptions to model a small state
machine:

In the :file:`formal.py` script:

.. code-block:: python

   from fvm import FvmFramework

   fvm.add_vhdl_source("concepts/cutpoint_example/counter.vhd")
   fvm = FvmFramework()
   fvm.cutpoint("Q")

In your PSL properties:

.. code-block:: VHDL

    signal cnt : unsigned(1 downto 0) := (others => '0');

    assume_initial_Q: assume Q = 0;
    assume_rst_Q: assume always ( {rst = '1'}                        |=> {Q = 0} );
    assume_s1: assume always ( {Q = 0 and rst = '0'}                 |=> {Q = MAX_COUNT/2} );
    assume_s2: assume always ( {Q = MAX_COUNT/2 and rst = '0'}       |=> {Q = (MAX_COUNT - 1)} );
    assume_s3: assume always ( {Q = (MAX_COUNT - 1) and rst = '0'}   |=> {Q = MAX_COUNT} );
    assume_s4: assume always ( {Q = MAX_COUNT and rst = '0'}         |=> {Q = 0} );

    assume_cnt_0: assume always ( {Q = 0}                 |-> {cnt = "00"} );
    assume_cnt_1: assume always ( {Q = MAX_COUNT/2}       |-> {cnt = "01"} );
    assume_cnt_2: assume always ( {Q = (MAX_COUNT - 1)}   |-> {cnt = "10"} );
    assume_cnt_3: assume always ( {Q = MAX_COUNT}         |-> {cnt = "11"} );

.. todo::

   Hay que separar el example de cutpoint del de counter abstraction!

Example
-------


Memory abstraction
==================

Definition
----------

When to use it
--------------

How to do it
------------

Example
-------


Structural reduction
====================

Definition
----------

When to use it
--------------

How to do it
------------

Example
-------


Data independence
=================

Definition
----------

When to use it
--------------

How to do it
------------

Example
-------


Symbolic constants
==================

Definition
----------

When to use it
--------------

How to do it
------------

Example
-------


Assertion decomposition / property simplification
=================================================

Definition
----------

When to use it
--------------

How to do it
------------

Example
-------


Hierarchical verification
=========================

Definition
----------

When to use it
--------------

How to do it
------------

Example
-------

