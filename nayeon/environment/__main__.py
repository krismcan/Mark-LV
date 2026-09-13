"""Run Nayeon environment diagnostics."""

from .diagnostics import run_basic_diagnostics


def main() -> int:
    results = run_basic_diagnostics()

    print("Nayeon Environment Diagnostics")
    print("-" * 32)

    failed = False

    for result in results:
        status = "OK" if result.ok else "FAIL"
        print(f"[{status}] {result.name}: {result.message}")

        if not result.ok:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())