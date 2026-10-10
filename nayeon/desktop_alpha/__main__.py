"""Explicit Personal Alpha entry point. Offline is always the default."""
import sys

from nayeon.desktop_alpha.window import main


def cli() -> None:
    if len(sys.argv) == 1:
        main()
        return
    if sys.argv[1:] != ["--notepad"]:
        raise SystemExit("Only --notepad is supported for the optional local action mode.")
    import tkinter as tk
    from nayeon.desktop_alpha.notepad import build_notepad_controller
    from nayeon.desktop_alpha.window import NayeonWindow

    root = tk.Tk()
    NayeonWindow(root, controller=build_notepad_controller())
    root.mainloop()


if __name__ == "__main__":
    cli()
