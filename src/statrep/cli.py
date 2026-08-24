"""statrep command-line interface: ``statrep build|profile|doctor``."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _find_setup_sh() -> Path | None:
    """Locate setup.sh: first relative to this installed package (the
    normal case — `pip install -e .` from inside the cloned repo), then by
    walking up from the current working directory."""
    candidate = Path(__file__).resolve().parent.parent.parent / "setup.sh"
    if candidate.is_file():
        return candidate
    for parent in [Path.cwd(), *Path.cwd().parents]:
        candidate = parent / "setup.sh"
        if candidate.is_file():
            return candidate
    return None


def cmd_build(args: argparse.Namespace) -> int:
    from statrep.report.build import build_report

    result = build_report(
        input_path=args.input,
        output_dir=args.output,
        lang=args.lang,
        title=args.title,
        subtitle=args.subtitle,
        author=args.author,
        template=args.template,
        dv=args.dv,
        group_var=args.group_var,
        predictors=args.predictors.split(",") if args.predictors else None,
    )
    print(f"Report written to: {result['docx']}")
    print(f"  HTML (no Office needed): {result['html']}")
    print(f"  Tables (Excel):          {result['tables_xlsx']}")
    print(f"  SPSS syntax:             {result['sps']}")
    print(f"  Manifest:                {result['manifest']}")
    print(
        f"  {result['n_analyses']} analyses, {result['n_tables']} tables, "
        f"{result['n_figures']} figures"
    )
    if result["loader_warnings"]:
        print("Data loading notes:")
        for warning in result["loader_warnings"]:
            print(f"  - {warning}")
    if result["profile_alerts"]:
        print("Data quality alerts:")
        for alert in result["profile_alerts"]:
            print(f"  - {alert}")
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    from statrep.io.loaders import load
    from statrep.io.profile import profile

    loaded = load(args.input)
    if loaded.warnings:
        print("Loading notes:")
        for warning in loaded.warnings:
            print(f"  - {warning}")
    data_profile = profile(loaded.df)
    print(f"\n{data_profile.n_rows} rows x {data_profile.n_columns} columns")
    for v in data_profile.variables:
        n_valid = v.n - v.n_missing
        print(f"  {v.name} [{v.kind}] n={n_valid} missing={v.missing_rate:.1%}")
    if data_profile.alerts:
        print("\nAlerts:")
        for alert in data_profile.alerts:
            print(f"  - {alert}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    setup_sh = _find_setup_sh()
    if setup_sh is None:
        print(
            "Could not locate setup.sh. Run `statrep doctor` from inside the "
            "statistical-reporting repo, or run ./setup.sh --check directly."
        )
        return 1
    return subprocess.run(["bash", str(setup_sh), "--check"]).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="statrep", description="Data in, Word statistical report out.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Build a Word report from Excel/CSV data")
    p_build.add_argument("--input", required=True, help="Path to .xlsx/.xls/.csv/.tsv")
    p_build.add_argument("--output", default="output", help="Output directory")
    p_build.add_argument("--lang", choices=["tr", "en"], default="tr")
    p_build.add_argument("--title", default=None, help="Report title (default: input filename)")
    p_build.add_argument("--subtitle", default=None, help="Report subtitle")
    p_build.add_argument("--author", default=None, help="Report author / prepared by")
    p_build.add_argument("--template", choices=["academic-apa7", "business"], default="academic-apa7")
    p_build.add_argument("--dv", default=None, help="Dependent variable (auto-selected if omitted)")
    p_build.add_argument("--group-var", default=None, help="Grouping variable for comparisons")
    p_build.add_argument("--predictors", default=None, help="Comma-separated predictor list for regression")
    p_build.set_defaults(func=cmd_build)

    p_profile = sub.add_parser("profile", help="Print a data profile without building a report")
    p_profile.add_argument("--input", required=True)
    p_profile.set_defaults(func=cmd_profile)

    p_doctor = sub.add_parser("doctor", help="Re-run the environment capability probe")
    p_doctor.set_defaults(func=cmd_doctor)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
