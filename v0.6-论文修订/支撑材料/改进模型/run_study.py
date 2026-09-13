"""Cached, reproducible v0.4 runner with input/template provenance."""
from pathlib import Path
from dataclasses import asdict
import argparse
import gzip
import hashlib
import json
try:
    from .model import Config, Solver
except ImportError:  # direct execution from 改进模型/ remains supported
    from model import Config, Solver

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / 'runs'
CACHE.mkdir(exist_ok=True)


def provenance(paths):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def template_provenance():
    return provenance(sorted((ROOT.parent / '附件' / '附件3').glob('result*.xlsx')))


def run_case(name, cfg):
    path = CACHE / (name + '.json.gz')
    source_hash = hashlib.sha256((ROOT / 'model.py').read_bytes()).hexdigest()
    inputs = provenance([ROOT.parent / '附件' / n for n in ('附件1.xlsx', '附件2.xlsx')])
    templates = template_provenance()
    if path.exists():
        with gzip.open(path, 'rt', encoding='utf8') as f:
            result = json.load(f)
        if (result.get('source_hash') == source_hash
                and result.get('config') == asdict(cfg)
                and result.get('input_sha256') == inputs
                and result.get('template_sha256') == templates):
            print('CACHED', name, round(result['final']['t'] / 3600, 6), flush=True)
            return result
    print('RUN', name, asdict(cfg), flush=True)
    result = Solver(cfg).run()
    result['source_hash'] = source_hash
    result['input_sha256'] = inputs
    result['template_sha256'] = templates
    result['scenario_id'] = cfg.environment
    with gzip.open(path, 'wt', encoding='utf8') as f:
        json.dump(result, f, ensure_ascii=False, separators=(',', ':'))
    print('DONE', name, 'h=', result['final']['t'] / 3600,
          'stats=', result['stats'], flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--material', type=int, default=3)
    parser.add_argument('--shrink', action='store_true')
    parser.add_argument('--n', type=int, default=80)
    parser.add_argument('--power', type=float, default=2.0)
    parser.add_argument('--early', type=float, default=1.0)
    parser.add_argument('--late', type=float, default=15.0)
    parser.add_argument('--max-time', type=float, default=7 * 86400.0)
    parser.add_argument('--output-stride', type=int, default=60)
    parser.add_argument('--keep-short', action='store_true')
    parser.add_argument('--compact', action='store_true')
    parser.add_argument('--environment', default='last')
    args = parser.parse_args()
    cfg = Config(material=args.material, shrink=args.shrink, n=args.n,
                 grid_power=args.power, early_dt=args.early, late_dt=args.late,
                 max_time=args.max_time, output_stride=args.output_stride,
                 keep_short=args.keep_short, compact_output=args.compact,
                 environment=args.environment)
    run_case(args.name, cfg)
