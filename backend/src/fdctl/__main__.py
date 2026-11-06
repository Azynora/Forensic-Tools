import sys

if (len(sys.argv) == 1 and getattr(sys, "frozen", False)) or (len(sys.argv) > 1 and sys.argv[1] in {"--gui", "--gui-elevated"}):
    try:
        from fdctl.gui import main
    except ImportError:
        print("[Forensics Suite] The GUI edition is distributed as an official release package.")
        print("[Forensics Suite] Download ForensicsSuite_Setup.exe from: https://github.com/Azynora/Forensic-Tools/releases\n")
        from fdctl.cli import main
else:
    from fdctl.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
