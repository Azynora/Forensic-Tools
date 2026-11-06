import sys

if (len(sys.argv) == 1 and getattr(sys, "frozen", False)) or (len(sys.argv) > 1 and sys.argv[1] in {"--gui", "--gui-elevated"}):
    from fdctl.gui import main
else:
    from fdctl.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
