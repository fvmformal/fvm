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

Just use the function :py:func:`fvmframework.FvmFramework.cutpoint` and pass to it at
least the signal you want to cutpoint. Use it for all the signals you need to
convert into free variables. If needed, a python :code:`for` loop can be used
to apply the function to multiple signals.

.. code-block:: python

   from fvmframework import FvmFramework

   fvm.add_vhdl_source("concepts/cutpoint_example/counter.vhd")
   fvm = FvmFramework()
   fvm.cutpoint("Q")

The function can receive more arguments than just the signal name so don't
forget to check the function documentation:
:py:func:`fvmframework.FvmFramework.cutpoint`

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
:py:func:`fvmframework.FvmFramework.blackbox` and pass to it the entity name.

.. code-block:: python

   from fvmframework import FvmFramework

   fvm = FvmFramework()
   fvm.add_vhdl_sources("concepts/blackbox_instance/*.vhd")
   fvm.set_toplevel('dualcounter')
   fvm.blackbox('counter')

If you want to blackbox a specific instance of an entity, you need to use the
function :py:func:`fvmframework.FvmFramework.blackbox_instance`, providing the entity
name as argument.

.. code-block:: python

   from fvmframework import FvmFramework

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

   from fvmframework import FvmFramework

   fvm.add_vhdl_source("concepts/cutpoint_example/counter.vhd")
   fvm = FvmFramework()
   fvm.cutpoint("Q")

In your PSL properties:

.. code-block:: VHDL

   signal cnt: integer range 0 to 3;

   assume_initial_cnt: assume cnt = 0;
   assume_cnt_rst: assume always (         {rst = '1'} |=> {cnt = 0} );
   assume_cnt_increasing: assume always (  {cnt /= 3 and rst = '0'} |=> {cnt-prev(cnt) = 1} );
   assume_cnt_overflow: assume always (    {cnt=3}     |=> {cnt=0} ) abort rst;

   assume_Q_zero: assume always            ( {cnt=0} |-> {Q = 0} );
   assume_Q_inbetween: assume always       ( {cnt=1} |-> {Q > 0 and Q < MAX_COUNT-1} );
   assume_Q_max_minus_one: assume always   ( {cnt=2} |-> {Q = MAX_COUNT-1} );
   assume_Q_max_minus: assume always       ( {cnt=3} |-> {Q = MAX_COUNT} );

.. todo::

   Hay que separar el example de cutpoint del de counter abstraction!

Example
-------


Memory abstraction
==================

Definition
----------

The formal tool uses an abstract model that captures only the essential
behavior of the memory. We can **blackbox** a memory or **cutpoint** some of
the memory outputs to abstract the necessary memory.

When to use it
--------------

When memory is very large and cannot be reduced, memory abstraction is a good
option. There are several use cases:

- Sometimes, we don't care about the data itself and only need to focus on
  the control logic. In this case, **blackboxing memory** is recommended to
  reduce state space.

- If we want to verify data integrity but this is impractical due to memory
  size, we can check only a randomly selected memory location and **cutpoint
  the rest of memory locations**.

- We can blackbox the entire memory and create an **abstract model** to
  recreate the expected functionality of the memory (or some of its locations).

How to do it
------------

We can use cutpoint and blackboxes as seen in the previous sections.

Example
-------


Structural reduction
====================

Definition
----------

**Reduce the design size** whenever possible without affecting the
functionalities we want to verify. This can be achieved using assumptions or
parameters/generics.

When to use it
--------------

There are many use cases for this: the design is very large and can be **reduced
without affecting functionality** (for example, a FIFO of depth 1024 vs. a FIFO
of depth 16), **reducing waiting times** in designs that cause cycles where nothing
happens, **reducing the values that signals can take** with assumes to reduce the
state space... It is a basic, but fundamental technique.

How to do it
------------

From `formal.py` we can add different configurations with
:py:func:`fvmframework.FvmFramework.add_config`:

.. code-block:: python

   from fvmframework import FvmFramework

   fvm = FvmFramework()
   fvm.add_vhdl_sources("open-logic/src/base/vhdl/*.vhd")
   fvm.add_vhdl_sources("examples/fifo_sync/*.vhd")
   fvm.add_psl_sources("examples/fifo_sync/*.psl")

   fvm.set_toplevel("olo_base_fifo_sync")
   fvm.add_config("olo_base_fifo_sync", "config_width_8_depth_8", {"Width_g": 8, "Depth_g": 8})

From the PSL file we can add the `assumes`.

Example
-------

There are examples of symbolic constants in `<examples/fifo_sync>`,
`<examples/fifo_async>`, and `<examples/div32>`.

Data independence
=================

Definition
----------

The correctness of a design does not depend on the actual data values. So it
doesn't matter to us whether the data bus is 128-bit, 32-bit, or 8-bit.

When to use it
--------------

When we don't care about the value of the data and all we want to check is,
for example, if the transport of that data is correct, the control logic is
correct... For example, reducing the data width of a FIFO, the actual
operation of the FIFO will not change at all if the data is 64 bits or 3 bits.

How to do it
------------

From `formal.py` we can add different configurations with
:py:func:`fvmframework.FvmFramework.add_config`:

.. code-block:: python

   from fvmframework import FvmFramework

   fvm = FvmFramework()
   fvm.add_vhdl_sources("open-logic/src/base/vhdl/*.vhd")
   fvm.add_vhdl_sources("examples/fifo_sync/*.vhd")
   fvm.add_psl_sources("examples/fifo_sync/*.psl")

   fvm.set_toplevel("olo_base_fifo_sync")
   fvm.add_config("olo_base_fifo_sync", "config_width_8_depth_8", {"Width_g": 8, "Depth_g": 8})

Example
-------

There are examples of symbolic constants in `<examples/fifo_sync>` and
`<examples/fifo_async>`.

.. _symbolic-constants:

Symbolic constants
==================

Definition
----------

Force the tool to make some data signal constant in time, but let it choose
any value it wants. Using this, we can prove a property for all possible data
values without taking a lot of time.

When to use it
--------------

There are two main use cases: 

- It allows us to check **all possible data values**. For example, in the case of a
  buffer, instead of saying that if the data input equals 1, the data output will
  equal 1, we can say that if the input equals the symbolic constant ``data``, the
  output will equal ``data``. This way, we'll be covering all possible cases, and
  it won't take much time.

- The second use case is that it serves as a reference within properties.
  That is, when the time reference between two parts of the property is
  undefined, operators like ``prev`` cannot be used to reference previous points in
  time, but we can use the symbolic constant to reference the first point in time and
  use it in the second point in time. This is better understood in the example below.

How to do it
------------

Symbolic constants in PSL are defined with an assumption, where it starts with
`true` so that at time 0, ``last_grant = prev(last_grant)`` is not evaluated,
which would cause problems in some formal solvers. With this, we have a
constant that can take any possible value.

As seen in the example, the sequence ``last_valid_grant`` has an indefinite
duration; it can last 2 cycles, 100 cycles, or infinitely many cycles. If we
knew it lasted 2 cycles, instead of using the symbolic constant ``last_grant``,
we could write ``Out_Grant = round_robin_arbiter(In_Req, prev(Out_Grant))``, but
since there is no fixed time reference, the symbolic constant ``last_grant`` is
also being used for that purpose.

.. code-block:: vhdl


   signal last_grant : std_logic_vector(Width_g-1 downto 0);
   assume always ( {true} |=> {last_grant = prev(last_grant)} );

   sequence last_valid_grant (
      hdltype std_logic_vector(63 downto 0) last_grant
   ) is {
      ((Out_Ready = '1') and (Out_Valid = '1') and (Out_Grant = last_grant))[*1];  -- 1 cycle
      ((Out_Ready = '0') or (Out_Valid = '0'))[*];  -- 0 or more cycles
      ((Out_Ready = '1') and (Out_Valid = '1'))[*1]  -- 1 cycle
   };

   assert always ( {last_valid_grant(last_grant)} |->
                   {Out_Grant = round_robin_arbiter(In_Req, last_grant) } ) abort Rst;

Example
-------

There are examples of symbolic constants in `<examples/arbiter_rr>`,
`<examples/fifo_sync>`, `<examples/fifo_async>`, and `<examples/ipv6>`.

Assertion decomposition / property simplification
=================================================

Definition
----------

**Simplify a property** so that the formal tool can solve it more easily. The
most common way is to divide it into several properties.

When to use it
--------------

When you see that **a property is taking a long time** and doesn't seem to be
progressing over time, the best thing to do is reread the property and simplify
it if possible.

How to do it
------------

The usual approach is to divide it into several properties. An academic but
clear example is instead of writing:

.. code-block:: vhdl

   assert always ( {a; b} |-> {c and d} );

We can write:

.. code-block:: vhdl

   assert always ( {a; b} |-> {c} );
   assert always ( {a; b} |-> {d} );

That doesn't mean that the properties are always separated, since it can be
more readable when compacted into one property; it means that if the first
property is intractable for formal tools, one of the possible solutions is to
separate it.

Example
-------

There is an example in `<concepts/assertion_decomposition>`.

Hierarchical verification
=========================

Definition
----------

When the toplevel or higher levels of hierarchy are unfeasible for formal
verification tools, verify the necessary submodules separately.

When to use it
--------------

When, at the toplevel, the result of the ``friendliness`` step is very negative
and the ``reachability`` result leaves many **inconclusives**, it's a sign that
the toplevel is too complex to verify everything, though some things might be
verifiable.

This isn't a very serious problem because submodules are **underconstrained**;
that is, their inputs are unrestricted because they aren't connected at the
toplevel. Underconstraining ensures that if a property is met, it will also be
met at the toplevel. The problem is that counterexamples can be erroneous
because they might be due to an invalid input. Therefore, **bugs will never
escape**, although some time might be lost due to false alarms.

How to do it
------------

With :py:func:`fvmframework.FvmFramework.set_toplevel` we can change the module
we are working on.

Example
-------

