.. _firstexample:

Your first example
==================

Talk about the counter, for example

The design
----------

This is the design

.. code-block:: vhdl

   library IEEE;
   use ieee.std_logic_1164.all;
   use ieee.numeric_std.all;

   entity counter is
      generic ( MAX_COUNT : integer := 128 );
      port ( clk: in  std_logic;
            rst: in  std_logic;
            Q:   out unsigned(7 downto 0)
            );
   end counter;

   architecture behavioral of counter is

      signal count:   unsigned(7 downto 0);
      signal p_count: unsigned(7 downto 0);

   begin

      sinc: process(clk, rst)
      begin
         if (rst='1') then
         count <= (others=>'0');
         elsif (rising_edge(clk)) then
         count <= p_count;
         end if;
      end process;

      comb: process(count)
      begin
         if (count = MAX_COUNT) then
      p_count <= (others => '0');
         else
      p_count <= count + 1;
         end if;
      end process;

      Q <= count;

   end behavioral;

Writing the `formal.py` script
------------------------------

Now, let's write the `formal.py` script for the FVM framework!

We write the first version of the script before having the properties, this way
we can start leveraging the automatic formal tools even when we haven't written
a single PSL line.

.. code-block:: python

   from fvm import fvmframework

   fvm = fvmframework()
   fvm.add_vhdl_source("examples/countervunit/counter.vhd")
   fvm.set_toplevel("counter")
   fvm.run()

Writing the properties
----------------------

Let's write the properties!

.. code-block:: vhdl

   ADD CODE HERE, but in multiple code blocks. ADD IT LITTLE BY LITTLE, EXPLAINING WHAT IS ADDED AND WHY IT IS ADDED between the code blocks

Adding the properties to `formal.py`
------------------------------------

Explain that we just have to add a single line to our script

.. code-block:: python
   :emphasize-lines: 4
   from fvm import fvmframework

   fvm = fvmframework()
   fvm.add_vhdl_source("examples/countervunit/counter.vhd")
   fvm.add_psl_source("examples/countervunit/counter_properties.psl")
   fvm.set_toplevel("counter")
   fvm.run()

Running the tools
-----------------

Finally, let's run our `formal.py` script!

.. code-block:: zsh
   python3 formal.py
