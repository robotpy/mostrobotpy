import pytest

from wpilib import SharpIR
from wpilib.simulation import SharpIRSim


def test_sim_devices(wpilib_state):
    s = SharpIR.gp_2_y_0_a_02_yk_0_f(1)
    sim = SharpIRSim(s)

    assert s.get_range() == pytest.approx(0.2)

    sim.set_range(0.3)
    assert s.get_range() == pytest.approx(0.3)

    # Clamped to max range of 1.5 m for GP2Y0A02YK0F
    sim.set_range(3.0)
    assert s.get_range() == pytest.approx(1.5)
