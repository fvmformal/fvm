import pytest

from src.drom2psl.generator import generator

# Return values are:
#   False when no errors detected (return 0),
#   True when error detected (return != 0)
examples_and_retvals = [
    (["test/drom2psl/tutorial/step1_basic.json"], False),
    (["test/drom2psl/tutorial/step2_clocks.json"], False),
    (["test/drom2psl/tutorial/step3_signals_and_clock.json"], False),
    (["test/drom2psl/tutorial/step4_spacers.json"], False),
    (["test/drom2psl/tutorial/step5_groups.json"], False),
    (["test/drom2psl/tutorial/step6_period_phase.json"], False),
    (["test/drom2psl/tutorial/step7_config.json"], False),
    (["test/drom2psl/tutorial/step7_head_foot_fixed.json"], False),
    (["test/drom2psl/tutorial/step7_head_foot.json"], True),
    (["test/drom2psl/tutorial/step8_sharplines.json"], True),
    (["test/drom2psl/tutorial/step8_splines.json"], False),
    (["test/drom2psl/tutorial/step9_code.json"], True),
    (["test/drom2psl/test/empty.json"], True),
    (["test/drom2psl/test/multiplesignals.json"], False),
    (["test/drom2psl/test/nosignals.json"], True)
  ]

@pytest.mark.parametrize("file,expected", examples_and_retvals)

def test_retval(file, expected):
    retval = generator(file)
    assert retval == expected
