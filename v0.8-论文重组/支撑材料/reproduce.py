"""Run the retained numerical entrypoints from any working directory."""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / '改进模型'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('results', 'p2', 'verify', 'all'))
    parser.add_argument('--workers', type=int, default=3,
                        help='Worker count for the P2 study (default: 3).')
    args = parser.parse_args()
    if args.workers < 1:
        parser.error('--workers must be positive')

    commands = []
    if args.stage in ('results', 'all'):
        commands.extend([['run_all.py'], ['build_outputs.py']])
    if args.stage in ('p2', 'all'):
        commands.extend([
            ['p2_study.py', '--group', 'all', '--workers', str(args.workers)],
            ['p2_report.py'],
            ['audit_assumptions.py', '--output', str(ROOT / '科学假设诊断.json')],
        ])
    if args.stage in ('verify', 'all'):
        commands.extend([['tests.py'], ['verify_outputs.py']])

    for command in commands:
        print('Running:', sys.executable, *command, flush=True)
        subprocess.run([sys.executable, *command], cwd=MODEL, check=True)


if __name__ == '__main__':
    main()
