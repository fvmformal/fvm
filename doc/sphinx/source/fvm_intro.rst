What is FVM?
======================================

FVM is a **Formal Verification Methodology** for *digital microelectronics*. Its
main objective is to **lower the adoption barriers for Formal Verification for
the European Space Sector**, although it can be used in many other contexts where
digital design and/or verification is performed, such as teaching, research,
avionics, automotive, etc.

Its development is funded by the European Space Agency, through its Open Space
Innovation Program, specifically the activity *"Lowering the adoption barriers
for Formal Verification of ASIC and FPGA designs in the space sector"*. The
activity is being implemented by Universidad de Sevilla (Spain), through its
affiliated Technology Centre AICIA (Asociación de Investicación y Cooperación
Industrial de Andalucía).

The FVM is available under the permissive/free? license **LICENSE**

.. todo::

   Update the license when we have decided it

Components
----------------------------

The different parts of the FVM are...

.. todo::
  Describe

The methodology steps
~~~~~~~~~~~~~~~~~~~~~

As FVM is a methodology, it starts by defining a number of steps to perform:

The steps are:

1. Leverage any available automated tools
2. Create properties for the design under verification
3. Run a model checking / property checking tool
4. Generate coverage metrics, including simulation metrics for traces generated
   in the previous step

.. todo::

   Improve diagram

.. mermaid::
  :caption: A graphical summary of the FVM methodology

  graph TB

    subgraph ToolLint[ ]
      direction LR
      BoxLint[Lint] -.- DescLint[Statically check for possible issues in the design]
    end

    subgraph ToolFriendliness[ ]
      direction LR
      BoxFriendliness[AutoCheck] -.- DescFriendliness[Check for formal-friendliness]
    end

    subgraph ToolRulecheck[ ]
      direction LR
      BoxRulecheck[AutoCheck] -.- DescRulecheck[Detect other possible issues in the design]
    end

    subgraph ToolXverify[ ]
      direction LR
      BoxXverify[X-Check] -.- DescXverify[Check propagation of unknown values]
    end

    subgraph ToolCoverCheck[ ]
      direction LR
      BoxCoverCheck[CoverCheck] -.- DescCoverCheck[Detect uncoverable elements]
    end

    subgraph ToolCDC[ ]
      direction LR
      BoxCDC[CDC] -.- DescCDC[Identify potential issues with Clock Domain Crossing]
    end

    subgraph ToolRDC[ ]
      direction LR
      BoxRDC[RDC] -.- DescRDC[Identify potential issues with Reset Domain Crossing]
    end

    subgraph Tool4[ ]
      direction LR
      Box4[FVM Helper Tools] -.- Desc4[Help the user write the formal properties]
    end

    subgraph Tool5[ ]
      direction LR
      Box5[PropCheck] -.- Desc5[Demonstrate whether the formal properties hold or not]
    end

    subgraph ToolPropCheckCoverage[ ]
      direction LR
      BoxPropCheckCoverage[PropCheck] -.- DescPropCheckCoverage[Generate formal coverage metrics]
    end

    subgraph ToolQuestaSim[ ]
      direction LR
      BoxQuestaSim[QuestaSim] -.- DescQuestaSim[Simulate reached cover statements]
    end

    subgraph AutoTools[Automated Formal Tools]
      direction TB
      ToolLint --> ToolFriendliness
      ToolFriendliness --> ToolRulecheck
      ToolRulecheck --> ToolXverify
      ToolXverify --> ToolCoverCheck
      ToolCoverCheck --> ToolRDC
      ToolRDC --> ToolCDC
    end

    subgraph ModelCheck[Property Checking]
      direction TB
      Tool4 --> Tool5
      Tool5 --> ToolPropCheckCoverage
      ToolPropCheckCoverage --> ToolQuestaSim
    end

    subgraph Tool6[Formal Verification Methodology]
      direction LR
      Box6[FVM build & test framework] -.- Desc6a[Simplify tool execution]
      Box6 -.- Desc6b[Generate Reports]
      AutoTools --> ModelCheck
    end

    style Tool6 fill:#e0f7fa, stroke:#333, stroke-width:2px, color:#000
    style AutoTools fill:#add8e6, stroke:#333, stroke-width:2px, color:#000
    style ModelCheck fill:#add8e6, stroke:#333, stroke-width:2px, color:#000


The build and test framework
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *FVM framework* acts as an abstraction layer that interfaces with the
formal tools. Each formal tool may require different configurations and
commands, and FVM manages that for you, while also providing sensible defaults
for tool options.

The user just writes a simple ``formal.py`` script like the following one:

.. literalinclude:: ../../../examples/countervunit/formal.py
   :language: python

When running the script (``python3 formal.py``), the framework
automatically calls the different formal tools, collects the relevant metrics,
and generates the reports.

Supported toolchains
^^^^^^^^^^^^^^^^^^^^

Currently, just the Questa Formal Tools (and Questa Simulator, for the
`simcover` step) are supported

.. list-table:: FVM and the Questa toolchain
   :widths: 25 25
   :header-rows: 1

   * - FVM step
     - Questa tool
   * - ``lint``
     - Lint
   * - ``friendliness``
     - AutoCheck
   * - ``ruleCheck``
     - AutoCheck
   * - ``xverify``
     - X-Check
   * - ``reachability``
     - CoverCheck
   * - ``resets``
     - RDC
   * - ``clocks``
     - CDC
   * - ``prove``
     - PropCheck
   * - ``prove.formalcover``
     - PropCheck
   * - ``prove.simcover``
     - QuestaSim


Drom2psl
~~~~~~~~

``drom2psl`` is a package provided with FVM that aims to reduce...

.. todo::
  Describe


Repository of examples
~~~~~~~~~~~~~~~~~~~~~~

To ease the learning curve, Formal Verification of multiple designs are
provided. These designs are ordered so the FVM can be learn by working through
them. See :ref:`examples` for more information.

