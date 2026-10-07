"""Which candidate band sets can form which vegetation indices.

This module answers a purely structural question -- does a band set contain the
roles an index needs -- and deliberately stops there. It does not evaluate
index formulas, because Phase 0 has no spectra to evaluate them on.

Why this is worth having before any physics exists: feasibility is already
decisive. Configuration A cannot form NDTI no matter how good its SNR is,
because NDTI needs a SWIR1/SWIR2 contrast and A has one SWIR band. That is
hypothesis H2 expressed as a fact about the hardware rather than a result to
be measured.

Reminder on scope (CLAUDE.md rules 3 and 4): indices are baselines and
interpretability aids. Band selection targets the physical variables, and band
sets are judged by training the provisional retrieval model on them. A band set
that wins the feasibility matrix has not been shown to be better at anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from safari_bands.config.schemas import BandSet, IndexCatalogue, IndexDef


@dataclass(frozen=True)
class Feasibility:
    """Whether one band set can form one index."""

    index: str
    band_set: str
    feasible: bool
    missing_roles: tuple[str, ...]
    hyperspectral_only: bool

    @property
    def status(self) -> str:
        if self.feasible:
            return "yes"
        if self.hyperspectral_only:
            return "n/a (hyperspectral)"
        return "no"

    def explain(self) -> str:
        if self.feasible:
            return f"{self.index} is available to {self.band_set}"
        missing = ", ".join(self.missing_roles)
        if self.hyperspectral_only:
            return (
                f"{self.index} needs hyperspectral sampling ({missing}); "
                "no multispectral configuration can form it"
            )
        return f"{self.index} needs {missing}, which {self.band_set} does not carry"


def resolve_index(index: IndexDef, band_set: BandSet) -> Feasibility:
    """Check one index against one band set."""
    available = band_set.roles
    missing = tuple(role for role in index.requires_roles if role not in available)
    return Feasibility(
        index=index.name,
        band_set=band_set.name,
        feasible=not missing,
        missing_roles=missing,
        hyperspectral_only=index.hyperspectral_only,
    )


def feasibility_matrix(
    catalogue: IndexCatalogue,
    band_sets: dict[str, BandSet],
) -> dict[str, dict[str, Feasibility]]:
    """Resolve every index against every band set.

    Returns ``{index_name: {band_set_key: Feasibility}}``.
    """
    return {
        index.name: {key: resolve_index(index, bs) for key, bs in band_sets.items()}
        for index in catalogue.indices
    }


def feasible_indices(catalogue: IndexCatalogue, band_set: BandSet) -> list[IndexDef]:
    """Every index ``band_set`` can form."""
    return [i for i in catalogue.indices if resolve_index(i, band_set).feasible]


def infeasible_indices(catalogue: IndexCatalogue, band_set: BandSet) -> list[IndexDef]:
    """Every index ``band_set`` cannot form."""
    return [i for i in catalogue.indices if not resolve_index(i, band_set).feasible]


def coverage_by_target(
    catalogue: IndexCatalogue,
    band_set: BandSet,
) -> dict[str, tuple[int, int]]:
    """Feasible / total index count per retrieval target.

    A coarse read on where a configuration is blind. A target with 0 feasible
    indices is not necessarily unretrievable -- the retrieval model works on
    bands, not indices -- but it is a signal worth explaining.
    """
    counts: dict[str, list[int]] = {}
    for index in catalogue.indices:
        target = index.target or "unassigned"
        tally = counts.setdefault(target, [0, 0])
        tally[1] += 1
        if resolve_index(index, band_set).feasible:
            tally[0] += 1
    return {target: (feasible, total) for target, (feasible, total) in sorted(counts.items())}


def render_matrix(
    catalogue: IndexCatalogue,
    band_sets: dict[str, BandSet],
) -> str:
    """Render the feasibility matrix as a fixed-width text table."""
    keys = sorted(band_sets)
    matrix = feasibility_matrix(catalogue, band_sets)

    index_width = max(len("index"), *(len(name) for name in matrix))
    col_widths = [max(len(key), 5) for key in keys]

    def row(label: str, cells: list[str]) -> str:
        padded = [c.center(w) for c, w in zip(cells, col_widths, strict=True)]
        return f"{label:<{index_width}}  " + "  ".join(padded)

    lines = [
        row("index", list(keys)),
        "-" * (index_width + 2 + sum(w + 2 for w in col_widths) - 2),
    ]

    for index in catalogue.indices:
        cells = []
        for key in keys:
            result = matrix[index.name][key]
            if result.feasible:
                cells.append("yes")
            elif result.hyperspectral_only:
                cells.append("n/a")
            else:
                cells.append("-")
        lines.append(row(index.name, cells))

    lines.append("")
    lines.append("yes = band set carries every required role   - = missing roles")
    lines.append("n/a = hyperspectral only; no multispectral configuration can form it")
    return "\n".join(lines)
