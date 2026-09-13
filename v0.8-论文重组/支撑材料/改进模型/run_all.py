"""Canonical v0.4 runs.

The q2_full trajectory is also the q3 fixed-radius trajectory: one run provides
both the required 1-second q2 output and the 60-second q3 summaries.
"""
try:
    from .model import Config
    from .run_study import run_case
except ImportError:  # direct execution from 改进模型/ remains supported
    from model import Config
    from run_study import run_case


def configurations():
    return {
        'q1_final': Config(material=1, n=160, grid_power=2.0,
                           early_dt=1.0, late_dt=1.0, max_time=1800.0,
                           stop_dry=False, keep_short=True,
                           compact_output=False, output_stride=1),
        'q2_full': Config(material=3, n=160, grid_power=2.0,
                           early_dt=1.0, late_dt=1.0,
                           stop_dry=True, keep_short=True,
                           compact_output=True, output_stride=1,
                           environment='last'),
        'q4_final': Config(material=4, shrink=True, n=160, grid_power=2.0,
                           early_dt=1.0, late_dt=15.0,
                           stop_dry=True, keep_short=False,
                           compact_output=False, output_stride=60,
                           environment='last'),
        'q3_coarse': Config(material=3, n=40, grid_power=2.0,
                            early_dt=1.0, late_dt=30.0, stop_dry=True),
        'q4_coarse': Config(material=4, shrink=True, n=40, grid_power=2.0,
                            early_dt=1.0, late_dt=30.0, stop_dry=True),
    }


if __name__ == '__main__':
    for name, cfg in configurations().items():
        run_case(name, cfg)
