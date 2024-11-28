.PHONY: all install lint list-tests test test-verbose concepts examples pycoverage venv clean realclean

# Everything runs inside a python venv, since it is the recommended way of
# managing python dependencies.
# The default VENV_DIR can be changed by passing a different value to Makefile,
# for example: make VENV_DIR=my_venv examples
# If VENV_DIR is unset, no venv will be used: make VENV_DIR= examples
VENV_DIR ?= .venv
VENV_ACTIVATE ?= . $(VENV_DIR)/bin/activate &&
PYTHON ?= python3

# If VENV_DIR is unset, set REQS_DIR to . so the files "reqs_installed" and
# "dev-reqs_installed" can be created
REQS_DIR := $(if $(VENV_DIR), $(VENV_DIR), .)

# If VENV_DIR is unset, unset also VENV_ACTIVATE
VENV_ACTIVATE := $(if $(VENV_DIR), $(VENV_ACTIVATE), )

all:
	@echo usage:
	@echo   "make venv         -> create python virtual environment"
	@echo   "make reqs         -> install dependencies"
	@echo   "make dev-reqs     -> install development dependencies"
	@echo   "make install      -> install the FVM"
	@echo   "make lint         -> pass pylint over the python code"
	@echo   "make list-tests   -> list all the tests"
	@echo   "make test         -> run the tests"
	@echo   "make test-verbose -> run the tests with full stdout/stderr output"
	@echo   "make concepts     -> run the concepts"
	@echo   "make examples     -> run the examples"
	@echo   "make pycoverage   -> generate code coverage report for the python code"
	@echo   "make testall      -> run the tests, concepts and examples"
	@echo   "make clean        -> remove temporary files"
	@echo   "make realclean    -> remove temporary files and python venv"

# reqs and dev-reqs depend on a file we create inside the venv, so we can avoid
# calling "pip3 install ..." if the requirements have already been installed
reqs: $(REQS_DIR)/reqs_installed

dev-reqs: $(REQS_DIR)/dev-reqs_installed

install: $(REQS_DIR)/fvm-installed

fvm: $(REQS_DIR)/fvm-installed

$(REQS_DIR)/reqs_installed: .venv
	$(VENV_ACTIVATE) pip3 install -r requirements.txt -q
	touch $(REQS_DIR)/reqs_installed

$(REQS_DIR)/dev-reqs_installed: .venv
	$(VENV_ACTIVATE) pip3 install -r dev-requirements.txt -q
	touch $(REQS_DIR)/dev-reqs_installed

# Install the FVM
$(REQS_DIR)/fvm-installed: .venv
	$(VENV_ACTIVATE) pip3 install -e .

# Lint the python code
lint: reqs
	$(VENV_ACTIVATE) pylint --output-format=colorized test/*.py src/*/*.py || pylint-exit $$?

# List the tests
list-tests: reqs dev-reqs
	$(VENV_ACTIVATE) pytest --collect-only

# Run the tests
test: fvm dev-reqs
	$(VENV_ACTIVATE) coverage run -m pytest -v --junit-xml="results.xml"

# Run the tests in verbose mode
test-verbose: fvm dev-reqs
	$(VENV_ACTIVATE) coverage run -m pytest -v -s --junit-xml="results.xml"

# List with all the examples
examplelist += 00-counter
examplelist += 01-countervunit
examplelist += 02-linearinterpolator
examplelist += 04-dualcounter
examplelist += 05-uart_tx

# List with all the concepts
conceptlist += transactions_deprecated
conceptlist += parameterized_sequences
conceptlist += inheriting_vunits
conceptlist += inheriting_multiple_vunits
conceptlist += parameterized_properties
conceptlist += multiple_designs
conceptlist += symbolic_constants
conceptlist += user_defined_hdltypes
conceptlist += user_defined_hdltypes_in_package
conceptlist += user_defined_hdltypes_in_external_package
conceptlist += assert_to_assume
conceptlist += defining_clocks_and_resets
conceptlist += hooks
conceptlist += design_configurations
#conceptlist += design_configurations_2

# examples target runs all the examples
# concept target runs all the concepts
examples: $(examplelist)
concepts: $(conceptlist)

# Print the lists, in case this is needed for debugging
list-examples:
	@echo $(examplelist)

list-concepts:
	@echo $(conceptlist)

# Generic rules to run examples and concepts
%: examples/% fvm
	$(VENV_ACTIVATE) $(PYTHON) -m examples.$@.formal

%: concepts/% fvm
	$(VENV_ACTIVATE) $(PYTHON) -m concepts.$@.formal

# Calculate python code coverage
pycoverage: dev-reqs
	$(VENV_ACTIVATE) coverage combine
	$(VENV_ACTIVATE) coverage report -m
	$(VENV_ACTIVATE) coverage html
	$(VENV_ACTIVATE) coverage xml

# Run everything
testall: test concepts examples

# Create python venv if it doesn't exist
venv: $(VENV_DIR)

# When creating the venv, we use the system's python (we can't use the venv's
# python because it doesn't exist yet)
$(VENV_DIR):
	python3 -m venv $(VENV_DIR)

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
	rm -rf test/testlib
	rm -f test/test/test.vhd test/test/test2.vhd test/test/test3.vhd
	rm -f test/test/test.psl test/test/test2.psl test/test/test3.psl

# Remove venv and generated files
realclean: clean
	rm -rf .venv
