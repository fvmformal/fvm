.PHONY: all install fvm lint list-tests test test-verbose concepts examples pycoverage venv clean realclean

# Everything runs inside a python venv, since it is the recommended way of
# managing python dependencies.
# The default VENV_DIR can be changed by passing a different value to Makefile,
# for example: make VENV_DIR=my_venv examples
# If VENV_DIR is unset, no venv will be used: make VENV_DIR= examples
VENV_DIR ?= .venv
VENV_ACTIVATE ?= . $(VENV_DIR)/bin/activate &&
PYTHON ?= python3
POETRY_VERSION ?= 1.8.5

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
	@echo   "make report       -> create a dashboard with reports after execution"
	@echo   "make show         -> open dashboard"
	@echo   "make todo         -> count TODOs in code and generate badge for gitlab"
	@echo   "make clean        -> remove temporary files"
	@echo   "make realclean    -> remove temporary files and python venv"

# reqs and dev-reqs depend on a file we create inside the venv, so we can avoid
# calling "pip3 install ..." or "poetry install..." if the requirements have
# already been installed
reqs: $(REQS_DIR)/reqs_installed

dev-reqs: $(REQS_DIR)/dev-reqs_installed

install: $(REQS_DIR)/fvm_installed

fvm: install

# Instead of $(VENV_ACTIVATE) pip3 install -r requirements.txt -q,
#   we are managing our dependencies with python poetry
# We must specify --no-root to poetry install: if we don't, it will install the
# fvm too, and we want to do that separately
$(REQS_DIR)/reqs_installed: $(VENV_DIR)/venv_created
	$(VENV_ACTIVATE) poetry install --no-root
	$(VENV_ACTIVATE) python3 install_allure.py $(VENV_DIR)
	echo "export PATH=\$$PATH:$(realpath $(VENV_DIR))/allure/bin" >> $(VENV_DIR)/bin/activate
	touch $@

# Instead of $(VENV_ACTIVATE) pip3 install -r dev-requirements.txt -q,
#   we are managing our dependencies with python poetry
$(REQS_DIR)/dev-reqs_installed: $(VENV_DIR)/venv_created
	$(VENV_ACTIVATE) poetry install --with dev
	touch $@

# Install the FVM. For now we use python poetry to install it (poetry install)
# instead of just pip, since we don't have yet a setup.py
# It is also good for development to manage our dependencies with poetry
$(REQS_DIR)/fvm_installed: $(VENV_DIR)/venv_created reqs
	$(VENV_ACTIVATE) poetry install
	touch $@

# Lint the python code
lint: dev-reqs
	$(VENV_ACTIVATE) pylint --output-format=colorized test/*.py fvm/*.py fvm/*/*.py || pylint-exit $$?

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
examplelist += counter
examplelist += countervunit
examplelist += linearinterpolator
examplelist += dualcounter
examplelist += uart_tx
examplelist += uart_rx

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
	$(VENV_ACTIVATE) $(PYTHON) examples/$@/formal.py

%: concepts/% fvm
	$(VENV_ACTIVATE) $(PYTHON) concepts/$@/formal.py

# Calculate python code coverage
pycoverage: dev-reqs
	$(VENV_ACTIVATE) coverage combine
	$(VENV_ACTIVATE) coverage report -m
	$(VENV_ACTIVATE) coverage html
	$(VENV_ACTIVATE) coverage xml

# Run everything
testall: test concepts examples

# Create python venv if it doesn't exist
venv: $(VENV_DIR)/venv_created

# When creating the venv, we use the system's python (we can't use the venv's
# python because it doesn't exist yet)
# Some linux distros don't automatically add pip inside new venvs (Rocky Linux
# 8, I'm looking at you), so let's also tell python that we want to have pipa
#
# $(realpath PATH) converts a relative path into an absolute one
$(VENV_DIR)/venv_created:
	python3 -m venv $(VENV_DIR)
	$(VENV_ACTIVATE) python3 -m ensurepip --upgrade
	$(VENV_ACTIVATE) pip3 install poetry==$(POETRY_VERSION)
	$(VENV_ACTIVATE) poetry config keyring.enabled false
	touch $@

# We already do this in the python code, but sometimes something fails and
# still we want to generate reports, so let's have a manual option here
newreport: reqs
	$(VENV_ACTIVATE) allure generate fvm_out/fvm_results --clean -o fvm_out/fvm_report

report: reqs
	$(VENV_ACTIVATE) allure generate fvm_out/fvm_results -o fvm_out/fvm_report
	
updated_report: reqs
	$(VENV_ACTIVATE) allure generate fvm_out/dashboard/allure-results -o fvm_out/dashboard/allure-report2

# TODO : probably we should do this in the python code, for example providing
# an executable python file called fvm_show or similar
show: reqs
	$(VENV_ACTIVATE) allure open fvm_out/fvm_report

# Count TODOs in code
# Since each line in the recipe is run in a separate shell, to define a
# variable and be able to read its value later we need to use GNU Make's $eval
TODOs := $(shell grep -r TODO * | grep -v grep | wc -l)
todo: $(VENV_DIR)/venv_created
	$(VENV_ACTIVATE) pip3 install anybadge
	mkdir -p badges
	rm -f badges/todo.svg
	@echo "TODOs=$(TODOs)"
	@$(VENV_ACTIVATE) anybadge --value=$(TODOs) --label=TODOs --file=badges/todo.svg 1=green 10=yellow 20=orange 30=tomato 999=red

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
	rm -rf dist

# Remove venv and generated files
realclean: clean
	rm -rf .venv
