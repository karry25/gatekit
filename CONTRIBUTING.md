# Contributing to gatekit

Thanks for considering a contribution. gatekit stays small on purpose, so
the bar is usefulness, not volume.

## Adding a workflow

1. It must prevent a real, named failure mode - one you have actually seen.
2. Use the standard sections: Purpose, Inputs, Procedure (numbered),
   Evidence, Stop conditions. The test suite enforces this.
3. Evidence contracts and stop conditions are not optional decoration. A
   workflow without them is just a pep talk.
4. Keep it under ~120 lines. If it needs more, split it.

## Changing preflight

- Python 3.8+ standard library only. No dependencies, ever.
- New detections need a test in `tests/test_preflight.py` with a fixture.
- False positives are bugs. When in doubt, warn instead of block.
- It stays read-only by default.

## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

All tests must pass before you open a pull request. Run
`./bin/preflight --run-checks` at the repo root as well - gatekit gates
itself.

## License

By contributing, you agree your work is released under the MIT License.
