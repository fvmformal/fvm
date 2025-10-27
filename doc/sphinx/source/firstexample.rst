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

   from fvmframework import FvmFramework

   fvm = FvmFramework()
   fvm.add_vhdl_source("examples/countervunit/counter.vhd")
   fvm.set_toplevel("counter")
   fvm.run()

Writing the properties
----------------------

Let's write the properties!

.. todo::
  Explain the vunit

.. code-block:: vhdl

   -- Default clock for PSL assertions
   default clock is rising_edge(clk);

The first step is to specify the default clock domain to use, to avoid having to 
include the clock domain in every property. This is highly recommended for designs 
with a single clock.

.. code-block:: vhdl

   -- Force a reset in the first clock cycle
   -- Since we don't have an 'always', this assumption only applies to the
   -- first clock cycle
   assume_initial_reset: assume rst = '1';

In formal verification, a reset is required in the first cycle to limit the number of 
possible states to start with. Although many tools infer this, it's good practice to 
maintain it for portability between toolchains.

.. code-block:: vhdl

   -- Assert we do not go over the maximum
   never_go_over_the_maximum: assert always (Q <= MAX_COUNT);

Since no assume is needed for the counter inputs, we can start directly with the assertions.
This property asserts that the counter output will never exceed the counter's maximum 
count, i.e. the property will fail if overflows occur and the counter does not go to 0.
Although these types of properties do not assert the functionality of the design, they are 
very useful for quickly finding counterexamples when there is an error in the design.

.. code-block:: vhdl

   -- Assert the counter is always counting up, but only:
   -- 1) If it's not the first clock cycle
   -- 2) If it hasn't just been reset
   -- 3) If last value wasn't MAX_COUNT
   always_count_up: assert always (not (rst = '1') and (not prev(rst) = '1') and (prev(Q) /= MAX_COUNT)) -> (Q-prev(Q) = 1);

This property does assert the functionality of the design. It asserts that if there hasn't 
been a reset in this or the previous cycle and the last counter output wasn't the maximum 
count, the counter output will have increased by 1.

.. code-block:: vhdl

   -- Cover the overflow -> zero case
   -- What we write here has to be a sequence inside curly braces {}, even if
   -- we only have one element, for example, { Q = MAX_COUNT }
   cover_overflow_to_zero: cover {Q = MAX_COUNT ; Q = 0};

   -- Same as above but adding reset behavior.
   cover_overflow_to_zero_and_reset: cover {Q = MAX_COUNT ; Q = 0; [*]; rst = '1'; [*]; Q = MAX_COUNT ; Q = 0};

To complement the assertions, it's always helpful to have covers that show us a trace 
validating the design's main use cases. In this case, covering the overflow to 0 is 
enough; this way, we'll see how the counter reaches the maximum count without having to write 
any testbench. Additionally, we can add how the design behaves when reset.

Adding the properties to `formal.py`
------------------------------------

Explain that we just have to add a single line to our script

.. code-block:: python
   :emphasize-lines: 5

   from fvmframework import FvmFramework

   fvm = FvmFramework()
   fvm.add_vhdl_source("examples/countervunit/counter.vhd")
   fvm.add_psl_source("examples/countervunit/counter_properties.psl")
   fvm.set_toplevel("counter")
   fvm.run()

Running the tools
-----------------

Finally, let's run our `formal.py` script!

.. code-block:: zsh

   python3 formal.py
