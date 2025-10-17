Command-line options
====================

  -h, --help            show this help message and exit
  -v, --verbose         Show full tool outputs. (default: False)
  -l, --list            Only list available methodology steps, but do not execute them. (default: False)
  -o OUTDIR, --outdir OUTDIR
                        Output directory. (default: fvm_out)
  -d DESIGN, --design DESIGN
                        If set, run the specified design. If unset, run all designs. (default: None)
  -s STEP, --step STEP  If set, run the specified step. If unset, run all steps. (default: None)
  -c, --cont            Continue with next steps even if errors are detected. (default: False)
  -g, --gui             Show tool results with GUI after tool execution. (default: False)
  -n, --guinorun        Show already existing tool results with GUI, without running the tools again. (default: False)

.. note::

   To see the available command-line options, you can always run your
   :file:`formal.py` script with the :code:`-h`/:code:`--help` flag:

   .. code-block:: console

      python3 formal.py -h

