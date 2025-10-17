FvmFramework
============

the FvmFramework class is the intended interface for users.

.. note::

   Callables (classes, functions and methods) that are not documented in the Public API are not intented to be directly used and thus may change between minor versions.

   At the moment, only the FvmFramework class is documented in the Public API

.. autoclass:: fvm.FvmFramework
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: 
        __init__,
        init_results,
        generics_to_args,
        set_loglevel,
        set_logformat,
        get_log_counts,
        check_errors,
        list_design,
        run_design,
        list_configuration,
        list_step,
        run_configuration,
        is_skipped,
        is_failure_allowed,
        is_disabled,
        exit_if_required,
        run_cmd,
        run_pre_hook,
        run_post_hook,
        run_hook_if_defined,
        run_hook,
        generate_psl_from_drom_sources,
        setup_design,
        logcheck,
        linecheck,
        run_step,
        run_post_step
