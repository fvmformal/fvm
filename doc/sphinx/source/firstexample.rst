.. _firstexample:

Your first example
==================

Talk about the counter, for example

The design
----------

This is the design

.. code-block:: vhdl

   ADD CODE HERE
   more code
   etc

Writing the `formal.py` script
------------------------------

Now, let's write the `formal.py` script for the FVM framework!

We write the first version of the script before having the properties, this way
we can start leveraging the automatic formal tools even when we haven't written
a single PSL line.

.. code-block:: python

   ADD CODE HERE
   etc

Writing the properties
----------------------

Let's write the properties!

.. code-block:: vhdl

   ADD CODE HERE, but in multiple code blocks. ADD IT LITTLE BY LITTLE, EXPLAINING WHAT IS ADDED AND WHY IT IS ADDED between the code blocks

Adding the properties to `formal.py`
------------------------------------

Explain that we just have to add a single line to our script

.. code-block:: python
   :emphasize-lines: 3

   ADD THE FULL SCRIPT BUT HIGHLIGHT THE NEWLY ADDED LINE putting the correct
   number after the :emphasize-lines: above
   add_psl_sources("*.psl")
   other code

Running the tools
-----------------

Finally, let's run our `formal.py` script!

.. code-block:: zsh
   python3 formal.py
