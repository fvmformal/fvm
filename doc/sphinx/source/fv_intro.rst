.. _fv_intro:

An introduction to Formal Verification
======================================

This is a quick introduction to Formal Verification.

.. note::
   If you are already familiar with the concept, you can skip this section and
   go directly to :ref:`fvm_intro`

What is Formal Verification?
----------------------------

A good definition is the following one:

    “The use of tools that mathematically analyze the space of possible behaviors of a design, rather than computing results for particular values”
        -- Erik Seligman, Tom Schubert, M V Achutha Kiran Kumar, “Formal Verification: An Essential Toolkit for Modern VLSI Design”

This implies a change of mindset with respect to the traditional
simulation-based verification: instead of generating the input values, and
checking what does our design output, we are analyzing all possible cases.

This has the potential to be extremely powerful, if used correctly. While the
space of possible behaviors of a design may grow really big, the tooling has
fortunately improved a lot during the last years, and currently we can tackle very
interesting designs.

What is Formal Verification good for?
-------------------------------------

Formal Verification is (among other things) good for:

- Triggering hard-to-find bugs
- Reaching hard-to-find cases
- Performing breadth-first searches, instead of depth-first searches

.. todo::
  add more...

What does Formal Verfication struggle with?
-------------------------------------------

Formal Verification may struggle with:

- Wide multiplicators
- Designs that have big latencies

.. todo::
  add more...

Fortunately, there are techniques that can be used to help with these cases,
see section :ref:`reduceproofcomplexity`

Can't I just simulate?
--------------------------

Well yes, you can (and should!) simulate, but simulation doesn't catch
everything. You may miss anything you are not specifically triggering with
your chosen inputs.

Will Formal Verification replace the need for simulation?
---------------------------------------------------------

Most probably no. Even the tool vendors state that formal verification should
be used *as a complement* to simulation.

Currently, the best approach would be to do exactly that: complementing
simulation efforts with formal verification.

What kind of formal tools are out there?
----------------------------------------

While there are many tools out there, a useful categorization is to distinguish
between *automated* formal tools and *non-automated* formal tools.

The first kind of tools don't require the user to do a lot of work. Many
automated formal tools work without any user input, although some of them may
require specifying reset and/o clock domains.

The second set of tools require the user to specify the *properties* of their
design.

What is typically happening is that, at the core of all this, is a Property
Checker tool (which also can be known as a Model Checker). This tool converts
your design and your properties into *theorems*, and tries to prove or disprove
them.

With FVM, it is less difficult that it sounds
---------------------------------------------

Well, historically Formal Verification has been a topic for experts (further
support this statement), but not anymore, with the FVM.

Keep reading to see how the FVM can help you make the confidence in your
designs, without a huge amount of effort, and with a smooth learning curve.
