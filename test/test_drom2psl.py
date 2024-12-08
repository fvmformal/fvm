import pytest

from fvm.drom2psl.generator import generator

# Return values are:
#   False when no errors detected (return 0),
#   True when error detected (return != 0)
examples_and_retvals = [
    (["test/drom2psl/tutorial/step1_basic.json"], False),
    (["test/drom2psl/tutorial/step2_clocks.json"], False),
    (["test/drom2psl/tutorial/step3_signals_and_clock.json"], False),
    (["test/drom2psl/tutorial/step4_spacers.json"], False),
    (["test/drom2psl/tutorial/step5_groups.json"], False),
    (["test/drom2psl/tutorial/step6_period_phase.json"], True),
    (["test/drom2psl/tutorial/step7_config.json"], False),
    (["test/drom2psl/tutorial/step7_head_foot_fixed.json"], False),
    (["test/drom2psl/tutorial/step7_head_foot.json"], True),
    (["test/drom2psl/tutorial/step8_sharplines.json"], True),
    (["test/drom2psl/tutorial/step8_splines.json"], False),
    (["test/drom2psl/tutorial/step9_code.json"], True),
    (["test/drom2psl/test/empty.json"], True),
    (["test/drom2psl/test/multiplesignals.json"], False),
    (["test/drom2psl/test/nosignals.json"], True),
    (["drom/wishbone_classic_read.json"], False),
    (["drom/wishbone_classic_write.json"], False),
    (["drom/wishbone_pipelined_read.json"], False),
    (["drom/wishbone_pipelined_write.json"], False),
    (["drom/spi_cpol_0_cpha_0.json"], False),
    (["drom/spi_cpol_0_cpha_1.json"], False),
    (["drom/spi_cpol_1_cpha_0.json"], False),
    (["drom/spi_cpol_1_cpha_1.json"], False),
    (["drom/uart_tx.json"], False),
  ]


@pytest.mark.parametrize("file,expected", examples_and_retvals)

def test_retval(file, expected):
    retval = generator(file)
    assert retval == expected
