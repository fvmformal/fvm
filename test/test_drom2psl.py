"""Tests for the drom2psl generator"""
import os
from pathlib import Path

import pytest

from fvm.drom2psl.generator import generator

# Return values are:
#   False when no errors detected (return 0),
#   True when error detected (return != 0)
examples_and_retvals = [
    ("test/drom2psl/tutorial/step1_basic.json", False),
    ("test/drom2psl/tutorial/step2_clocks.json", False),
    ("test/drom2psl/tutorial/step3_signals_and_clock.json", False),
    ("test/drom2psl/tutorial/step4_spacers.json", False),
    ("test/drom2psl/tutorial/step5_groups.json", False),
    ("test/drom2psl/tutorial/step6_period_phase.json", True),
    ("test/drom2psl/tutorial/step7_config.json", False),
    ("test/drom2psl/tutorial/step7_head_foot_fixed.json", False),
    ("test/drom2psl/tutorial/step7_head_foot.json", True),
    ("test/drom2psl/tutorial/step8_sharplines.json", True),
    ("test/drom2psl/tutorial/step8_splines.json", False),
    ("test/drom2psl/tutorial/step9_code.json", True),
    ("test/drom2psl/test/empty.json", True),
    ("test/drom2psl/test/multiplesignals.json", False),
    ("test/drom2psl/test/nosignals.json", True),
    ("drom_sequences/wishbone_classic_read.json", False),
    ("drom_sequences/wishbone_classic_write.json", False),
    ("drom_sequences/wishbone_pipelined_read.json", False),
    ("drom_sequences/wishbone_pipelined_write.json", False),
    ("drom_sequences/spi_cpol_0_cpha_0.json", False),
    ("drom_sequences/spi_cpol_0_cpha_1.json", False),
    ("drom_sequences/spi_cpol_1_cpha_0.json", False),
    ("drom_sequences/spi_cpol_1_cpha_1.json", False),
    ("drom_sequences/uart_tx.json", False),
  ]

inputs_and_expected_outputs = [
    ("drom_sequences/spi_cpol_0_cpha_0.json", "test/drom2psl/expected/spi_cpol_0_cpha_0.psl"),
    ("drom_sequences/spi_cpol_0_cpha_1.json", "test/drom2psl/expected/spi_cpol_0_cpha_1.psl"),
    ("drom_sequences/spi_cpol_1_cpha_0.json", "test/drom2psl/expected/spi_cpol_1_cpha_0.psl"),
    ("drom_sequences/spi_cpol_1_cpha_1.json", "test/drom2psl/expected/spi_cpol_1_cpha_1.psl"),
    ("drom_sequences/uart_tx.json", "test/drom2psl/expected/uart_tx.psl"),
    ("drom_sequences/wishbone_classic_read.json", "concepts/wishbone_sequence/wishbone_classic_read.psl"),
    ("drom_sequences/wishbone_classic_read.json", "test/drom2psl/expected/wishbone_classic_read.psl"),
    ("drom_sequences/wishbone_classic_write.json", "test/drom2psl/expected/wishbone_classic_write.psl"),
    ("drom_sequences/wishbone_pipelined_read.json", "test/drom2psl/expected/wishbone_pipelined_read.psl"),
    ("drom_sequences/wishbone_pipelined_write.json", "test/drom2psl/expected/wishbone_pipelined_write.psl"),
  ]

@pytest.mark.parametrize("file,expected", examples_and_retvals)
def test_retval(file, expected):
    """Test return value of generator function."""
    retval = generator(file)
    assert retval == expected

def remove_comments(file, comment_string = "--"):
    """Remove lines starting with comment_string from a file and return
    the result as a list of lines."""
    comments_removed = []

    with open(file, 'r', encoding="utf-8") as f:
        for line in f:
            if not line.strip().startswith(comment_string):
                comments_removed.append(line)

    return comments_removed

def compare_files_ignoring_comments(file1, file2):
    """Compare two files ignoring lines starting with comment_string."""
    # We need this function because in the CI, the input path that appears in
    # the comment of generated .psl files will be in a subdirectory of /build,
    # which will not match our expected output files
    return remove_comments(file1) == remove_comments(file2)

@pytest.mark.parametrize("file,expected", inputs_and_expected_outputs)
def test_output_matches_expected(file, expected):
    """Test that the output of the generator matches the expected output,
    ignoring comments."""
    # retval should be False if the generator found no errors
    # filecmp.cmp should return True if actual and expected outputs are equal
    outdir = os.path.join(os.getcwd(), "test", "drom2psl")
    actual = os.path.join(outdir, os.path.basename(Path(file).with_suffix('.psl')))
    retval = generator(file, outdir = outdir)
    assert retval == False
    assert compare_files_ignoring_comments(actual, expected) == True
