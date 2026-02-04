# Copyright 2024-2026 Universidad de Sevilla
# SPDX-License-Identifier: Apache-2.0

.PHONY: all install fvm lint list-tests test test-verbose concepts examples pycoverage venv clean realclean

# Everything is managed by uv. "uv run" automatically creates a venv and
# populates it with the required dependencies and our fvm module. If the --dev
# flag is passed to it, it includes also the development dependencies.
UV_RUN ?= uv run $(UVFLAGS)

# Which is our python executable
PYTHON ?= python3

# Where to install Allure Report, and which version to install
ALLURE_VERSION=2.32.0
ALLURE_INSTALL_DIR ?= ~/.cache/fvm

all:
	@echo usage:
	@echo   "make lint         -> pass pylint over the python code"
	@echo   "make list-tests   -> list all the tests"
	@echo   "make test         -> run the tests"
	@echo   "make test-verbose -> run the tests with full stdout/stderr output"
	@echo   "make concepts     -> run the concepts"
	@echo   "make examples     -> run the examples"
	@echo   "make pycoverage   -> generate code coverage report for the python code"
	@echo   "make testall      -> run the tests, concepts and examples"
	@echo   "make report       -> create a dashboard with reports after execution"
	@echo   "make show         -> open dashboard"
	@echo   "make todo         -> count TODOs in code and generate badge for gitlab"
	@echo   "make docs         -> generate documentation using sphinx"
	@echo   "make clean        -> remove temporary files"
	@echo   "make realclean    -> remove temporary files and python venv"

# Lint the python code
lint:
	$(UV_RUN) --dev pylint --output-format=colorized --recursive=y test/ src/ || $(UV_RUN) --dev pylint-exit $$?

# List the tests
list-tests:
	$(UV_RUN) --dev pytest --collect-only

# Run the tests
test:
	$(UV_RUN) coverage run -m pytest -v --junit-xml="results.xml"

# Run the tests in verbose mode
test-verbose:
	$(UV_RUN) coverage run -m pytest -v -s --junit-xml="results.xml"

# List with all the examples
examplelist += counter
examplelist += linearinterpolator
examplelist += dualcounter
examplelist += uart_tx
examplelist += arbiter_prior
examplelist += arbiter_prior
examplelist += arbiter_rr
examplelist += fifo_sync
examplelist += fifo_async
examplelist += axi_lite_slave
examplelist += sdram
examplelist += ipv6

# If we only want to calculate friendliness
friendlinesslist = $(addsuffix .friendliness, $(examplelist))

# List with all the concepts
conceptlist += adding_drom_sources
conceptlist += assert_to_assume
conceptlist += assertion_decomposition
conceptlist += blackbox_example
conceptlist += blackbox_instance
conceptlist += cutpoint_example
conceptlist += defining_clocks_and_resets
conceptlist += design_configurations
conceptlist += hooks
conceptlist += inheriting_multiple_vunits
conceptlist += inheriting_vunits
conceptlist += multiple_designs
conceptlist += parameterized_properties
conceptlist += parameterized_sequences
conceptlist += reachability_example
conceptlist += symbolic_constants
conceptlist += transactions_deprecated
conceptlist += user_defined_hdltypes
conceptlist += user_defined_hdltypes_in_external_package
conceptlist += user_defined_hdltypes_in_package

# examples target runs all the examples
# concept target runs all the concepts
examples: $(examplelist)
concepts: $(conceptlist)
friendliness: $(friendlinesslist)

# Print the lists, in case this is needed for debugging
list-examples:
	@echo $(examplelist)

list-concepts:
	@echo $(conceptlist)

# Generic rules to run examples and concepts
%: examples/%
	$(UV_RUN) $(PYTHON) examples/$@/formal.py

%.friendliness: examples/%
	$(UV_RUN) $(PYTHON) examples/$*/formal.py -s friendliness

%: concepts/%
	$(UV_RUN) $(PYTHON) concepts/$@/formal.py

%: test/examples/%
	$(UV_RUN) $(PYTHON) test/examples/$@/formal.py

# Calculate python code coverage
pycoverage:
	$(UV_RUN) coverage combine
	$(UV_RUN) coverage report -m
	$(UV_RUN) coverage html
	$(UV_RUN) coverage xml

# Run everything
testall: test concepts examples

# We already do this in the python code, but sometimes something fails and
# still we want to generate reports, so let's have a manual option here
newreport:
	$(UV_RUN) python3 src/fvm/manage_allure.py --allure_version $(ALLURE_VERSION) --install_dir $(ALLURE_INSTALL_DIR)
	$(ALLURE_INSTALL_DIR)/allure-$(ALLURE_VERSION)/bin/allure generate fvm_out/fvm_results --clean -o fvm_out/fvm_report

report:
	$(UV_RUN) python3 src/fvm/manage_allure.py --allure_version $(ALLURE_VERSION) --install_dir $(ALLURE_INSTALL_DIR)
	$(ALLURE_INSTALL_DIR)/allure-$(ALLURE_VERSION)/bin/allure generate fvm_out/fvm_results -o fvm_out/fvm_report

updated_report:
	$(UV_RUN) python3 src/fvm/manage_allure.py --allure_version $(ALLURE_VERSION) --install_dir $(ALLURE_INSTALL_DIR)
	$(ALLURE_INSTALL_DIR)/allure-$(ALLURE_VERSION)/bin/allure generate fvm_out/dashboard/allure-results -o fvm_out/dashboard/allure-report

show:
	$(UV_RUN) python3 src/fvm/manage_allure.py --allure_version $(ALLURE_VERSION) --install_dir $(ALLURE_INSTALL_DIR)
	$(ALLURE_INSTALL_DIR)/allure-$(ALLURE_VERSION)/bin/allure open fvm_out/fvm_report

# Count TODOs in code
# Since each line in the recipe is run in a separate shell, to define a
# variable and be able to read its value later we need to use GNU Make's $eval
# We substract 5 lines that are in the Makefile but are part of this target
# and not actually things that need to be done
TODOs := $(shell echo `grep -r TODO * | wc -l` - 5 | bc)
todo:
	mkdir -p badges
	rm -f badges/todo.svg
	@echo "TODOs=$(TODOs)"
	@$(UV_RUN) anybadge --value=$(TODOs) --label=TODOs --file=badges/todo.svg 1=green 10=yellow 20=orange 30=tomato 999=red

# Generate documentation, adding a warning to the internal API
define WARNING_INTERNAL_API
.. warning::\n\
\n\
   Callables that are not documented in the Public API are not intented to\n\
   be directly used and thus may change between minor versions.\n\
\n\
   Proceed with caution.\n\
\n\

endef

docs:
	$(UV_RUN) sphinx-apidoc -o doc/sphinx/source src/fvm
	echo "$(WARNING_INTERNAL_API)" > temp_modules.rst
	cat doc/sphinx/source/modules.rst >> temp_modules.rst
	mv temp_modules.rst doc/sphinx/source/modules.rst
	$(UV_RUN) make -C doc/sphinx/ html
	mkdir -p badges
	rm -f badges/undocumented.svg
	$(UV_RUN) anybadge --value=`cat doc/sphinx/undocumented_count.txt` --label=undocumented --file=badges/undocumented.svg 1=green 10=yellow 20=orange 30=tomato 999=red

multidocs:
	$(UV_RUN) sphinx-apidoc -o doc/sphinx/source src/fvm
	echo "$(WARNING_INTERNAL_API)" > temp_modules.rst
	cat doc/sphinx/source/modules.rst >> temp_modules.rst
	mv temp_modules.rst doc/sphinx/source/modules.rst
	$(UV_RUN) make -C doc/sphinx/ multidocs

# Remove generated files
clean:
	rm -f results.xml flex*.log vish_stacktrace.vstf modelsim.ini
	rm -rf ./*/__pycache__ ./*/*/__pycache__ .pytest_cache
	rm -rf work fvm_out
	rm -rf .coverage coverage.xml htmlcov
	rm -f modelsim.ini qverify.log qverify_cmds.tcl
	rm -f pylint.log pylint.txt
	rm -rf .qverify .visualizer qcache propcheck.db
	rm -f visualizer.log qverify_ui.log qverify_ui_cmds.tcl sysinfo.log
	rm -f viscom.vstf viscom_*.log viscom_*.logerr
	rm -rf badges
	rm -rf pylint
	rm -rf test/testlib
	rm -f test/test.vhd test/test2.vhd test/test3.vhd
	rm -f test/test.psl test/test2.psl test/test3.psl
	rm -f test/drom2psl/test/multiplesignals.psl test/drom2psl/test/multiplesignals.svg
	rm -f test/drom2psl/tutorial/*.psl test/drom2psl/tutorial/*.svg
	rm -f test/drom2psl/*.psl
	rm -f drom/*.psl drom/*.svg
	rm -rf dist
	rm -rf doc/sphinx/source/fvm.drom2psl.rst doc/sphinx/source/fvm.rst doc/sphinx/source/modules.rst
	rm -rf doc/sphinx/build/* doc/sphinx/undocumented_count.txt

# Remove venv and generated files
realclean: clean
	rm -rf .venv
	rm -rf PoC grlib-gpl-2024.4-b4295 grlib-gpl-2024.4-b4295.tar.gz
