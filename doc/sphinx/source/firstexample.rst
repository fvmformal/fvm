.. _firstexample:

Your first example
==================

Let's do our first example!

We will explain some things as we go, so let's dive in :)

The design: a simple VHDL counter
---------------------------------

We want to formally verify a simple VHDL counter, whose code is as follows:

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
      signal n_count: unsigned(7 downto 0);

   begin

      sinc: process(clk, rst)
      begin
         if (rst='1') then
           count <= (others=>'0');
         elsif (rising_edge(clk)) then
           count <= n_count;
         end if;
      end process;

      comb: process(count)
      begin
         if (count = MAX_COUNT) then
           n_count <= (others => '0');
         else
           n_count <= count + 1;
         end if;
      end process;

      Q <= count;

   end behavioral;

Save this file as ``counter.vhd``

Writing the ``formal.py`` script
--------------------------------

Now, let's write the ``formal.py`` script for the FVM framework!

We write the first version of the script before having the properties, this way
we can start leveraging the automatic formal tools even when we haven't written
a single PSL line.

.. code-block:: python

   from fvm import FvmFramework

   fvm = FvmFramework()
   fvm.add_vhdl_source("counter.vhd")
   fvm.set_toplevel("counter")
   fvm.run()

Running the formal tools
------------------------

Running the FVM steps using the FVM Framework is as easy as running the
``formal.py`` script:

.. code-block:: zsh

   python3 formal.py

.. note::

   Make sure you have the FVM installed and the ``venv``, if needed, activated.
   See the :ref:`installation` section for details.

Since we haven't written any properties, we will just see the results of
running the automated tools over our design. For each of the FVM steps you will
see any warnings and errors given by the relevant tool and a summary of the
step. After all the steps run you will see a final summary that will look like
this:

.. raw:: html
   :file: _static/counter_noproperties.html

Let's explain the results:

* ``lint``: Result is ``ok``, no issues detected.
* ``friendliness``: The design has a very high formal-friendliness score, which
  makes it very suitable for formal verification.
* ``rulecheck``: ``ok``, no issues detected.
* ``xverify``: Result is ``2I``. If we scroll up to see the summary of the
  step, we'll notice that ``I`` means `Incorruptible` in this case, which is
  equivalent to a warning and means that ``X`` values can appear in a signal,
  but they will not propagate. The user can always consult the documentation of
  the relevant tool (in this case Questa X-Check) for more detailed
  information.
* ``reachability``: 100% of the design is reachable, which is good news.
* ``resets``: ``ok``, no Reset Domain Crossing issues detected.
* ``clocks``: ``ok``, no Clock Domain Crossing issues detected.
* ``prove``: Since we haven't written any properties yet, there are no
  assumptions, no assertions and no cover statements.

  * ``prove.formalcover``: This post-step fails, since formal coverage cannot
    be computed if there are no properties. That is the reason why its result
    is also ``N/A``. If we scroll up to see the results of the post-step, we
    will see the following error message:

    .. code-block::

       ERROR detected in step='prove.formalcover', tool='propcheck', line='# Fatal   : No proven/inconclusive properties found for formal coverage computation.  [formal-414]'

  * ``prove.simcover``: This post-step doesn't run any simulation since there
    are neither falling assertions nor reached cover directives. Its result is
    also ``N/A``

So, everything seems to work fine but, as expected, we need some properties to
correctly run the ``prove`` steps and its sub-steps.

Writing the properties
----------------------

Now that we know how to run the FVM, let's write the properties for the
counter!

We will write the following to a file named ``counter_properties.psl``

.. seealso::

   In formal verification, we use three main keywords when writing properties:
   ``assume``, ``assert`` and ``cover``. See the :ref:`directives` section for
   more information.

In PSL, we write Verification Units, and we do that using the ``vunit`` keyword
(*not to be confused with the VUnit test framework*). These `vunits` are binded
to either an VHDL entity (if we only need to work with the ports of the entity)
or to an VHDL entity and architecture pair (when we also need to work with the
internal signals of the entity). In this case, we can just bind the ``vunit``
with the properties, named ``counter_properties``, to the entity ``counter``:

.. code-block:: vhdl

   vunit counter_properties (counter) {

The first step is to specify the default clock domain to use, to avoid having
to include the clock domain in every property. This is highly recommended for
designs with a single clock:

.. code-block:: vhdl

   -- Default clock for PSL assertions
   default clock is rising_edge(clk);

Now, let's write our first assumption. In formal verification, a reset is
usually required in the first cycle to limit the number of possible initial
states. Although many tools automatically infer this, it is good practice to
explicitly write it for portability between toolchains. So, we will ``assume``
that, on the first clock cycle, our counter is being reset:

.. code-block:: vhdl

   -- Force a reset in the first clock cycle
   -- Since we don't have an 'always', this assumption only applies to the
   -- first clock cycle
   assume_initial_reset: assume rst = '1';

Since no assumptions are needed for the rest of the counter inputs, we can
start writing assertions.

The following property will ``assert`` that the counter output will never
exceed the counter's maximum count, i.e. the property will fail if overflows
occur. This property is similar to `firewall assertions` in simulation: it is
not checking for the full expected correct functionality but is checking for
error conditions instead. These kind of properties are very useful for quickly
finding counterexamples when there is an error in the design:

.. code-block:: vhdl

   -- Assert we do not go over the maximum
   never_go_over_the_maximum: assert always (Q <= MAX_COUNT);

Now we'll write 3 properties that do actually check the functionality of the
design. The first one will ``assert`` that a reset clears the count, the
second one will ``assert`` that if the count has not reached the maximum, it
increases by 1 (provided there has not been a reset, due to ``abort rst``) and
the third one will ``assert`` that if it has reached the maximum, it returns to
0 (provided there has not been a reset).

.. code-block:: vhdl

   -- Assert the count is cleared on reset
   reset_clears_count: assert always ({rst = '1'} |=> {Q = 0});

   -- Assert the count increments when not at maximum
   -- Note that `abort rst` at the end of the assertion avoids checking
   -- the property when reset is active
   count_increments: assert always ({Q /= MAX_COUNT} |=> {Q = prev(Q) + 1}) abort rst;

   -- Assert the count overflows when at maximum
   count_overflow: assert always ({Q = MAX_COUNT} |=> {Q = 0}) abort rst;

To complement the assertions, it's always helpful to have ``cover`` directives:
each one will generate a trace of the design covering the specified scenario,
or will result in a proof that it cannot be covered. For this design, covering
the overflow to zero is enough; this way, we'll see how the counter reaches the
maximum count without having to write any simulation testbench.  Additionally,
we can also ``cover`` the case when the design is reset, to see its behavior
when suddenly reset:

.. code-block:: vhdl

   -- Cover the overflow -> zero case
   -- What we write here has to be a sequence inside curly braces {}, even if
   -- we only have one element, for example, { Q = MAX_COUNT }
   cover_overflow_to_zero: cover {Q = MAX_COUNT ; Q = 0};

   -- Same as above but adding reset behavior.
   cover_overflow_to_zero_and_reset: cover {Q = MAX_COUNT ; Q = 0; [*]; rst = '1'; [*]; Q = MAX_COUNT ; Q = 0};

Since we have finished writing the properties, we must just make sure that we
are closing the ``vunit``:

.. code-block:: vhdl

   }

The full ``counter_properties.psl`` should look like this:

.. code-block:: vhdl

   vunit counter_properties (counter) {

      -- Default clock for PSL assertions
      default clock is rising_edge(clk);

      -- Assert we do not go over the maximum
      never_go_over_the_maximum: assert always (Q <= MAX_COUNT);

      -- Assert the count is cleared on reset
      reset_clears_count: assert always ({rst = '1'} |=> {Q = 0});

      -- Assert the count increments when not at maximum
      -- Note that `abort rst` at the end of the assertion avoids checking
      -- the property when reset is active
      count_increments: assert always ({Q /= MAX_COUNT} |=> {Q = prev(Q) + 1}) abort rst;

      -- Assert the count overflows when at maximum
      count_overflow: assert always ({Q = MAX_COUNT} |=> {Q = 0}) abort rst;

      -- Cover the overflow -> zero case
      -- What we write here has to be a sequence inside curly braces {}, even if
      -- we only have one element (for example, { Q = MAX_COUNT }
      cover_overflow_to_zero: cover {Q = MAX_COUNT ; Q = 0};
      cover_overflow_to_zero_and_reset: cover {Q = MAX_COUNT ; Q = 0; [*]; rst = '1'; [*]; Q = MAX_COUNT ; Q = 0};

      -- Force a reset in the first clock cycle
      -- Since we don't have an 'always', this assumption only applies to the
      -- first clock cycle
      assume_initial_reset: assume rst = '1';

   }

Adding the properties to `formal.py`
------------------------------------

By just adding a line to `formal.py`, we can add the properties and start using the steps
with non-automated formal tools.

.. code-block:: python
   :emphasize-lines: 5

   from fvm import FvmFramework

   fvm = FvmFramework()
   fvm.add_vhdl_source("counter.vhd")
   fvm.add_psl_source("counter_properties.psl", flavor="vhdl")
   fvm.set_toplevel("counter")
   fvm.run()

Running the formal tools again
------------------------------

Finally, let's run our `formal.py` script again!

.. code-block:: zsh

   python3 formal.py

Now, our results are better:

.. raw:: html
   :file: _static/counter_properties.html

In the ``prove`` step we can see that, as we have written, we have 1
assumption, 4 assertions which have been proven, and 2 covers that have been
covered.

Also, our formal code coverage (code observed by our properties) and our
simulation code coverage (code executing by simulating the covered ``cover``
statements) are both 100%

With a small number of lines of code we have fully formally verified an 8-bit
counter, which testifies to how powerful formal verification is. Formal
verification can tackle even bigger designs, so continue reading to learn
more!

- Link to example in the FVM repository: https://gitlab.com/fvmformal/fvm/-/tree/main/examples/counter

Viewing reports
---------------

The FVM provides reports in different formats, apart from the step results and
summaries that are shown during command-line execution.

- **HTML report:** FVM generates beautiful HTML reports by leveraging the
  Allure Report tool. To see the HTML report, pass the ``--show`` or
  ``--shownorun`` option to the ``formal.py`` script. The first one runs the
  formal tools and opens the HTML report, and the second one opens the HTML
  report without running the formal tools, which is useful if you have already
  run them. Since we have already run the tools for the counter, we can execute
  the following command to open the HTML report without re-running the FVM
  steps:

  .. code-block:: zsh

     python3 formal.py --shownorun

  Also, when working with multiple designs, the ``--showall`` option can be
  used to generate a single HTML report for all designs in the output
  directory.

  .. seealso::

     See section :ref:`commandlineoptions` for more information about
     command-line options and report generation.

- **XML report:** FVM also can generate `JUnit XML
  <https://github.com/testmoapp/junitxml>`_ files for continuous integration
  systems such as gitlab CI or Jenkins. Go to the output directory (by default,
  ``fvm_out``), and the ``fvm_results`` directory inside it. An XML file will
  be generated in this directory for each design. In this example, if you open
  ``fvm_out/fvm_results/counter_results.xml`` with your favorite text editor,
  you will see the full execution results and logs in JUnit XML format.

- **Text report:** a plain text report, ``text_report.md``, is generated in the
  output directory (by default, ``fvm_out``). This is a plain text file in
  Markdown language, which means that it can be read as a normal plain text
  file, rendered by any Markdown renderers (such as gitlab/github issue
  trackers or VSCodium/VSCode Markdown preview), or even converted into PDF by
  using document conversion tools such as `pandoc <https://pandoc.org>`_.

  .. tip::

     An interesting idea is to create a latex template with your
     company/institution colors and logo and a cover page, and use pandoc to
     create a beautiful PDF from the text report. You could even use a hook
     (explained in section :ref:`hooks`) to automatically run, from within the
     FVM framework, a custom command that does this after the last FVM
     step.

- **HTML summary:** to see the FVM summary in HTML format, just go to the output
  directory (by default, ``fvm_out``) and open the ``summary.html`` file with
  your favorite browser.

- **Text summary:** a ``summary.txt`` file, which contains the FVM summary in
  plain text, is also generated in the output directory.

