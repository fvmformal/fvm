.. _examples:

Repository of Examples
======================================

The repository of examples is really nice

Suggested order
---------------

Easy examples
-------------

Example 1
~~~~~~~~~

Let's verify a simple counter!

Please find the code of the design in INSERT LINK

Bla bla bla. Please note that ble ble ble

Priority Arbiter
~~~~~~~~~~~~~~~~

This example shows a simple priority arbiter from the Open Logic library:
https://github.com/open-logic/open-logic. In this example, many things can
be checked simply with assertions, for example, that the output always has 0
or 1 bit asserted; that if there is no request, the output is 0; that if there
is a request, the output is onehot... Additionally, to fully test the
functionality, we can create a function that checks if the arbiter result is
correct (this can be done either in the PSL file or in a VHDL package, although
the latter is more recommended).

Round Robin Arbiter
~~~~~~~~~~~~~~~~~~~

This example also belongs to the OpenLogic library. Again, it's a simple
example, and some of the priority arbiter's priorities can be reused. However,
this case is more complicated due to the round-robin algorithm and the control
logic, which requires a handshake. We can define a sequence for the handshake
since it will be reused quite a bit.

Again, it's very convenient to define a function with round-robin behavior,
since it's very simple. Let's try creating a sequence with `drom2psl`.
We want to ensure that if there has been a valid grant before, the next grant
(whenever it happens) will be successful. The function that predicts the round
robin needs the request and the last grant.

.. image:: _static/examples/rr_arbiter.svg

This is the generated PSL:

.. code-block:: vhdl

   vunit last_valid_grant {

   sequence last_valid_grant (
      hdltype std_logic_vector(63 downto 0) last_grant
   ) is {
      ((Out_Ready = '1') and (Out_Valid = '1') and (Out_Grant = last_grant))[*1];  -- 1 cycle
      ((Out_Ready = '0') and (Out_Valid = '0'))[*];  -- 0 or more cycles
      ((Out_Ready = '1') and (Out_Valid = '1'))[*1]  -- 1 cycle
   };

   }

.. attention::
   The second line of the sequence: `((Out_Ready = '0') and (Out_Valid = '0'))[*]`
   is more convenient to express with an ``or``, because it also includes the case
   where either of the two is equal to 1. However, that cannot be represented
   with `drom2psl`, so it must be added manually.

With this, we can ensure that if we have a grant and then we have another (it
can happen in any possible cycle), the grant will be equal to the function
that predicts it.

.. code-block:: vhdl

   assert always ( {last_valid_grant(last_grant)} |->
                   {Out_Grant = round_robin_arbiter(In_Req, last_grant) } ) abort Rst;

OK examples
-----------

Example 3
~~~~~~~~~

Medium examples
---------------

Example 4
~~~~~~~~~

Difficult examples
------------------

Example 5
~~~~~~~~~

Whatever

.. attention::
   This is an Attention message

.. caution::
   This is a caution message

.. danger::
   This is a danger message

.. error::
   This is an error message

.. hint::
   This is a hint message

.. important::
   This is an important message

.. note::
   This is a note message

.. tip::
   This is a tip message

.. warning::
   This is a warning message

.. admonition:: This is a title

   This is the content of the admonition.

.. seealso::
   This is a seealso message, see also: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-warning 
