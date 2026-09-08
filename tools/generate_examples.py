"""Generate current synthetic fixtures without overwriting an existing directory."""
from pathlib import Path
import argparse
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from lucidecon.samples import cases, market, settlement
from lucidecon.common import write

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    out = Path(p.parse_args().output)
    if out.exists() and any(out.iterdir()):
        p.error('Use an empty directory to preserve earlier fixtures.')
    out.mkdir(parents=True, exist_ok=True)
    for name, case in cases().items():
        write(out / (name + '.json'), case)
    write(out / 'market.json', market())
    linear = market(); linear['reinforcement_power'] = 1
    write(out / 'market-linear-counterexample.json', linear)
    write(out / 'settlement.json', settlement())
    print(out)
