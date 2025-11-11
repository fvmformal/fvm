.. _sequencesandproperties:

Sequences and properties
========================

In formal verification, and also in PSL (Property Specification Language), we
pass either sequences or properties to the verification directives ``assert``,
``assume`` and ``cover``.

This section gives *simplified* definitions of those, and how FVM helps to
create them with the use of its helper tool `drom2psl`.

Sequences
---------

We can think about a PSL **sequence** as a series of things that must be true
in consecutive clock cycles. Clock cycles are separated by ``;``, whereas ``:``
separates different conditions that must be true in the same clock cycle.

For example, the following sequence happens when both *M_Axi_WValid* and
*M_Axi_WReady* are true at the same time:

.. code-block:: vhdl

   sequence transmission is {
     M_Axi_WValid : M_Axi_WReady
   };

Whereas the following sequence happens if *a* is true on one clock cycle and
*b* is true on the next clock cycle:

.. code-block:: vhdl

   sequence a_then_b is {
      a ; b
   };  

Sequences can also receive parameters, for example the following sequence
receives a parameter of type *unsigned*:

.. code-block:: vhdl

  sequence overflow (
    hdltype unsigned count
  ) is {
    count = MAX_COUNT; count = 0
  };

Using drom2psl to generate sequences
------------------------------------

While PSL supports writing complex sequences using SEREs (Sequential Extended
Regular Expressions), the FVM proposes to use a helper tool, ``drom2psl``, to
generate sequences from `Wavedrom <wavedrom.com>`_ timing diagrams.

From a Wavedrom waveform that looks like this:

.. image:: _static/wishbone_classic_read.svg
   :alt: A graphical summary of the FVM
   :width: 50%
   :align: center


``drom2psl`` takes its JSON description:

.. code-block::

   {
   head: {text: 'wb_classic_read(addr, data)',
       tick:  0,
       every: 1,
       },
   foot: {text: 'Wishbone read, classic mode',
       },
   signal: [
       {name: 'clk',   wave: 'p|.|'},
     ['Master',
       {name: 'adr', wave: 'x3.x', data: 'addr', type: 'std_ulogic_vector(31 downto 0)'},
       {name: 'dat', wave: 'x...'},
       {name: 'cyc', wave: '01.0'},
       {name: 'stb', wave: '01.0'},
       {name: 'sel', wave: 'x...'},
       {name: 'we',  wave: 'x0.x'}
     ],
   {},
     ['Slave',
       {name: 'dat', wave: 'x.3x', data: 'data', type: 'std_ulogic_vector(31 downto 0)'},
       {name: 'ack', wave: '0.10'},
       {name: 'err', wave: '0...'}
     ],
   ],
   }

And converts it into a sequence, encapsulated into a PSL *vunit* (verification
unit):

.. code-block::

   vunit wishbone_classic_read {

     sequence wishbone_classic_read_Master (
       hdltype std_ulogic_vector(31 downto 0) addr
     ) is {
       ((Master.cyc = '0') and (Master.stb = '0'))[*1]  -- 1 cycle;
       ((Master.adr = addr) and (Master.cyc = '1') and (Master.stb = '1') and (Master.we = '0'))[+]  -- 1 or more cycles;
       ((Master.cyc = '0') and (Master.stb = '0'))[*]  -- 0 or more cycles
     };

     sequence wishbone_classic_read_Slave (
       hdltype std_ulogic_vector(31 downto 0) data
     ) is {
       ((Slave.ack = '0') and (Slave.err = '0'))[+]  -- 1 or more cycles;
       ((Slave.dat = data) and (Slave.ack = '1') and (Slave.err = '0'))[*1]  -- 1 cycle;
       ((Slave.ack = '0') and (Slave.err = '0'))[*]  -- 0 or more cycles
     };

   }

This *vunit* can be used from any user-defined *.psl* file just by using the
``inherit`` keyword:

.. code-block::

   inherit wishbone_classic_read;

Properties
----------

We can think about a **property** as a relation between two or more
**sequences**, for example the following property relates the sequences
*wishbone_classic_read_Master* and *wishbone_classic_read_Slave*:

.. code-block:: vhdl

   property wishbone_classic_read (
     hdltype std_ulogic_vector(31 downto 0) addr;
     hdltype std_ulogic_vector(31 downto 0) data
   ) is
     always { {wishbone_classic_read_Master(addr)} && {wishbone_classic_read_Slave(data)} };

When relating sequences to create properties, we can use the following
operators:

* ``&&`` : both must happen and last exactly the same number of cycles
* ``&`` : both must happen, without any requirement on their durations
* ``|->`` : implication: both must happen, with the first cycle of the second
  occurring during the last cycle of the first
* ``|=>`` : non-overlapping implication: both must happen, with the first cycle
  of the second occuring the cycle after the last cycle of the first

By naming the properties, we are able to reuse them independently of whether
they are intended to be asserted or assumed.

Usage with verification directives
----------------------------------

We must keep in mind that the different verification directives can only
receive either a sequence or a property:

* ``assert``: receives a ``property``
* ``assume``: receives a ``property``
* ``cover``: receives a ``sequence``

Some examples follow:

.. code-block:: vhdl

   assume_correct_read_module_A:
      assume wishbone_classic_read(addr_A, data_A);

   assert_correct_read_module_B:
      assert wishbone_classic_read(addr_B, data_B) abort rst;

   cover_read_from_specific_address:
      cover wishbone_classic_read_Master(x"90000000");

The *abort rst* in the assertion indicated that the property doesn't need to
hold true if the *rst* signal is asserted

