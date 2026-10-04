"""One final line, one exit code, for every tool the orchestrator gates on.

A gate ends with `GATE <tool>: PASS` (exit 0) or `GATE <tool>: FAIL (<n> problem(s))` (exit 1), so
nobody needs a pipe (`| tail`) or a shell-specific exit-status variable (`PIPESTATUS`) to judge
it. The other ways out of a gate (a `sys.exit("message")`, a crash) print
`GATE <tool>: FAIL (error)` and exit non-zero. **No GATE line at all means FAIL.**

    import gate
    def main():
        a = ap.parse_args()
        gate.arm("manifest_check")      # from here on, every way out ends with a GATE line
        ...
        gate.finish(len(errors))        # prints the verdict and exits 0 / 1
    if __name__ == "__main__":
        gate.guard(main)

Set TRANSLATE_WORK_NESTED_GATE=1 in the environment of a gate run inside another gate (as
check_base runs manifest_check): the inner tool then prints no GATE line, so the output has one.
"""

import os
import sys
import traceback

_tool = None
_done = False


def arm(tool):
    """From now on, every way out of the process prints a GATE line for `tool`."""
    global _tool
    _tool = tool


def _line(text):
    if os.environ.get("TRANSLATE_WORK_NESTED_GATE") != "1":
        print(text, flush=True)


def finish(problems):
    """Print the verdict and exit: 0 problems = PASS (exit 0), else FAIL (exit 1)."""
    global _done
    _done = True
    if problems:
        _line(f"GATE {_tool}: FAIL ({problems} problem(s))")
        sys.exit(1)
    _line(f"GATE {_tool}: PASS")
    sys.exit(0)


def guard(main):
    """Run main(); if a gate was armed and ends without finish(), print a FAIL line."""
    try:
        main()
    except SystemExit as e:
        if _done or _tool is None:
            raise
        code = e.code
        if code is not None and not isinstance(code, int):
            print(code, file=sys.stderr)  # what sys.exit("message") would have printed
            code = 1
        _line(f"GATE {_tool}: FAIL (error)")
        sys.exit(code or 1)
    except Exception:
        if _tool is None:
            raise
        traceback.print_exc()
        _line(f"GATE {_tool}: FAIL (error)")
        sys.exit(1)
    if _tool is not None and not _done:
        _line(f"GATE {_tool}: FAIL (no verdict)")
        sys.exit(1)
