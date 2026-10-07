"""Command line interface: ``safari-bands``.

Phase 0 exposes three commands:

* ``validate``  -- load every config and run the methodological-rule checks
* ``indices``   -- print the index feasibility matrix across band sets
* ``bands``     -- print one band set in detail
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from safari_bands import __version__
from safari_bands import indices as indices_mod
from safari_bands.config.loader import ConfigError, load_study_config
from safari_bands.config.schemas import BandPurpose
from safari_bands.config.validators import (
    Severity,
    check_placeholders,
    validate_band_set,
)
from safari_bands.provenance import start_run


def _cmd_validate(args: argparse.Namespace) -> int:
    config = load_study_config()

    findings = list(check_placeholders(config.placeholder_configs))
    for band_set in config.band_sets.values():
        findings.extend(validate_band_set(band_set, config.windows, config.detectors))

    by_severity = {s: [f for f in findings if f.severity is s] for s in Severity}

    print(f"Loaded {len(config.band_sets)} band sets, {len(config.detectors)} detectors, "
          f"{len(config.indices.indices)} indices.")
    print()

    for severity in (Severity.ERROR, Severity.WARNING, Severity.INFO):
        group = by_severity[severity]
        if not group:
            continue
        print(f"{severity.value.upper()} ({len(group)})")
        for finding in group:
            print(f"  {finding}")
        print()

    n_errors = len(by_severity[Severity.ERROR])

    if args.run:
        run = start_run("validate", seed=0, command="validate")
        run.write_resolved_config(
            band_sets=config.band_sets,
            detectors=config.detectors,
            atmospheric_windows=config.windows,
            indices=config.indices,
            optics=config.optics,
            orbit=config.orbit,
        )
        run.write_text("findings.txt", "\n".join(str(f) for f in findings) + "\n")
        run.finalise(n_errors=n_errors, n_findings=len(findings))
        print(f"Run written to {run.directory}")
        print()

    if n_errors:
        print(f"FAILED: {n_errors} error(s).")
        return 1

    print("OK: no errors. Warnings above are expected where noted "
          "(placeholders pending Q2-Q6; the negative control is meant to look bad).")
    return 0


def _cmd_indices(args: argparse.Namespace) -> int:
    config = load_study_config()
    catalogue = config.indices

    if args.band_set:
        band_set = config.band_sets.get(args.band_set)
        if band_set is None:
            print(
                f"unknown band set {args.band_set!r}. "
                f"Available: {', '.join(sorted(config.band_sets))}",
                file=sys.stderr,
            )
            return 2

        print(f"Band set: {band_set.name} ({band_set.role_in_study})")
        print(f"  {band_set.description}")
        print()

        feasible = indices_mod.feasible_indices(catalogue, band_set)
        infeasible = indices_mod.infeasible_indices(catalogue, band_set)

        print(f"Can form ({len(feasible)}):")
        for index in feasible:
            print(f"  {index.name:<10s} {index.formula}")
        print()
        print(f"Cannot form ({len(infeasible)}):")
        for index in infeasible:
            print(f"  {index.name:<10s} {indices_mod.resolve_index(index, band_set).explain()}")
        print()
        print("Index coverage by target (feasible / total):")
        for target, (n, total) in indices_mod.coverage_by_target(catalogue, band_set).items():
            print(f"  {target:<12s} {n}/{total}")
        return 0

    print(indices_mod.render_matrix(catalogue, config.band_sets))
    print()
    print("Indices are baselines and interpretability aids only (CLAUDE.md rules 3 and 4).")
    print("Band selection targets the physical variables, not index values.")
    return 0


def _cmd_bands(args: argparse.Namespace) -> int:
    config = load_study_config()
    band_set = config.band_sets.get(args.band_set)
    if band_set is None:
        print(
            f"unknown band set {args.band_set!r}. "
            f"Available: {', '.join(sorted(config.band_sets))}",
            file=sys.stderr,
        )
        return 2

    print(f"{band_set.name} ({band_set.role_in_study})")
    print(f"  {band_set.description}")
    if band_set.swir_content:
        print(f"  SWIR content: {band_set.swir_content}")
    print()
    header = f"{'band':<12s} {'role':<12s} {'centre':>8s} {'FWHM':>7s}  {'detector':<14s} purpose"
    print(header)
    print("-" * len(header))
    for band in band_set.sorted_bands():
        purpose = "" if band.purpose is BandPurpose.SURFACE else band.purpose.value
        print(
            f"{band.name:<12s} {band.role:<12s} {band.centre_nm:>7.1f}  "
            f"{band.fwhm_nm:>6.1f}  {band.detector or '-':<14s} {purpose}"
        )
    print()

    findings = validate_band_set(band_set, config.windows, config.detectors)
    if findings:
        print("Findings:")
        for finding in findings:
            print(f"  {finding}")
    else:
        print("No findings.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="safari-bands",
        description="SAFARI Stage 1 band design study (Phase 0: config and validation).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser(
        "validate", help="load every config and run the methodological-rule checks"
    )
    p_validate.add_argument(
        "--run",
        action="store_true",
        help="write a run directory with the resolved config, findings and provenance",
    )
    p_validate.set_defaults(func=_cmd_validate)

    p_indices = sub.add_parser("indices", help="index feasibility across band sets")
    p_indices.add_argument(
        "--band-set", help="show one band set in detail instead of the whole matrix"
    )
    p_indices.set_defaults(func=_cmd_indices)

    p_bands = sub.add_parser("bands", help="print one band set in detail")
    p_bands.add_argument("band_set", help="band set name, e.g. config_b")
    p_bands.set_defaults(func=_cmd_bands)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
