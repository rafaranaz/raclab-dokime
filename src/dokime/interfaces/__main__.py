"""Lets the commands run as `python -m dokime.interfaces`."""

from dokime.interfaces.cli import main

raise SystemExit(main())
