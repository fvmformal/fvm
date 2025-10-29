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
robin needs the request and the last grant as inputs.

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

UART transmitter
~~~~~~~~~~~~~~~~

This example is still simple, but it already includes a state machine,
albeit one with very linear behavior. In this example, we can see how covers
can be very useful for several reasons: exploring the different states of
a state machine, validating functionality with a cover of the transmission,
or early design learning by making a cover with the final result.

.. code-block:: vhdl

   cover_start_of_transmission: 
      cover {state = b_start};

   sequence transmission is {
      TX=STARTBIT[*5];
      TX=databits(0)[*5]; TX=databits(1)[*5];
      TX=databits(2)[*5]; TX=databits(3)[*5];
      TX=databits(4)[*5]; TX=databits(5)[*5];
      TX=databits(6)[*5]; TX=databits(7)[*5];
      TX=paritybit[*5]; TX=STOPBIT[*5]
   };

   cover_one_transmission:
      cover transmission;

   cover_end_of_transmission: 
      cover {state = b_stop; state = reposo};

Axi-4 Lite Slave
~~~~~~~~~~~~~~~~~

This Axi Slave has a state machine that is no longer as linear (it has both
TX and RX) and also has quite a few interfaces. This makes writing sequences
for reuse more important, both in terms of speed and clarity. The code snippet
shows how code can be reused and made more readable for writing:

.. code-block:: vhdl

   sequence W_handshake is {                                                   
      S_AxiLite_WValid = '1' and S_AxiLite_WReady = '1'
   };

   sequence W_interface (
      hdltype std_logic Wr;
      hdltype std_logic_vector(AxiDataWidth_g - 1 downto 0) WrData;
      hdltype std_logic_vector((AxiDataWidth_g/8) - 1 downto 0) ByteEna
      ) is {                                                                        
      Rb_Wr = Wr and 
      Rb_WrData = WrData and 
      Rb_ByteEna = ByteEna 
   };

   assert_W_after_handshake: 
      assert always ( {W_handshake} |=> 
                      {W_interface('1', prev(S_AxiLite_WData), prev(S_AxiLite_WStrb))}
                     ) abort Rst;

Medium examples
---------------

SDRAM controller
~~~~~~~~~~~~~~~~

Linear interpolator
~~~~~~~~~~~~~~~~~~~~

Synchronous FIFO
~~~~~~~~~~~~~~~~~

Intermediate examples
----------------------

32-bit divider
~~~~~~~~~~~~~~~

Asynchronous FIFO
~~~~~~~~~~~~~~~~~

Difficult examples
------------------

IPv6 transceiver
~~~~~~~~~~~~~~~~~

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
