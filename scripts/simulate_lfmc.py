"""scripts/simulate_lfmc.py

P6f, step 1: the training set for the simulation-trained LFMC retrieval
(E-29, E-64). Radiative transfer only (rule 2), no training here.

For each fuel group in the prior set: Sobol-sample the parameters, run
PROSPECT-D + 4SAIL at 1 nm, convolve to the Sentinel-2 bands, and draw one
seeded noisy copy with the sensor model plus the atmospheric-correction
residual (rule 6). Noise-free values are kept beside the noisy ones.

    python scripts/simulate_lfmc.py                      # config/priors/lfmc_v1.yaml
    python scripts/simulate_lfmc.py --priors lfmc_v1 --limit 512   # smoke test

Writes (git-ignored) data/sim/<name>/:
    params.parquet   one row per spectrum: group, parameters, cw, lfmc
    spectra.npy      (N, 2101) float16 reflectance, 400-2500 nm
    s2_pack.npz      x_clean, x_noisy (N, bands), sigma (N, bands), names,
                     lfmc, cw, cm, group: what Fire_Risk_FW run_lfmc.py trains on
    manifest.json    counts, seeds, band names, sha256 of each file
and runs/<YYYYMMDD-HHMM>_sim_<name>/ with the resolved config and provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

from safari_bands import forward as F
from safari_bands.config.loader import (
    load_band_set,
    load_priors,
    load_study_config,
    project_root,
)
from safari_bands.provenance import start_run
from safari_bands.sensor import noise_model


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--priors", default="lfmc_v1")
    ap.add_argument("--limit", type=int, default=0, help="points per group (smoke test)")
    ap.add_argument("--out", type=Path, default=None, help="default data/sim/<priors name>")
    args = ap.parse_args(argv)

    pr = load_priors(args.priors)
    bs = load_band_set(pr.band_set)
    study = load_study_config()
    nm = noise_model(bs, study.detectors, study.optics, study.orbit)
    names = [b.name for b in bs.bands]
    n = args.limit or pr.samples_per_group
    out = args.out or project_root() / "data" / "sim" / (pr.name + ("_smoke" if args.limit else ""))
    out.mkdir(parents=True, exist_ok=True)
    run = start_run(f"sim_{pr.name}" + ("_smoke" if args.limit else ""), seed=pr.seed,
                    priors=pr.name, placeholder=bool(pr.placeholder or nm.placeholder))
    run.write_resolved_config(priors=pr, band_set=bs, optics=study.optics, orbit=study.orbit,
                              detectors=study.detectors)

    model = F.Prosail()
    tables, spectra, groups = [], [], []
    for g in pr.groups:
        t0 = time.time()
        p = F.sample(pr, g, n=n)
        s = F.simulate(model, p)
        print(f"  {g}: {n} spectra in {time.time() - t0:.0f} s", flush=True)
        tables.append(p)
        spectra.append(s)
        groups += [g] * n
    params = {k: np.concatenate([t[k] for t in tables]) for k in tables[0]}
    spec = np.concatenate(spectra)
    _, x = F.band_reflectance(spec, bs, names)

    # One seeded noisy draw: sensor noise (placeholder instrument, A-37) and
    # the atmospheric-correction residual, independent per band.
    rng = np.random.default_rng(pr.seed)
    sig_sensor = np.stack([nm.sigma(b, x[:, i]) for i, b in enumerate(names)], 1)
    ar = pr.atmospheric_residual
    sig_atm = F.atmospheric_sigma(x, ar.absolute, ar.relative)
    sigma = np.sqrt(sig_sensor**2 + sig_atm**2).astype(np.float32)
    x_noisy = (x + rng.standard_normal(x.shape) * sigma).astype(np.float32)

    import pandas as pd
    df = pd.DataFrame({"group": groups, **{k: v.astype(np.float32) for k, v in params.items()}})
    df.to_parquet(out / "params.parquet", index=False)
    np.save(out / "spectra.npy", spec.astype(np.float16))
    np.savez_compressed(out / "s2_pack.npz", x_clean=x, x_noisy=x_noisy, sigma=sigma,
                        names=np.array(names), lfmc=params["lfmc"].astype(np.float32),
                        cw=params["cw"].astype(np.float32), cm=params["cm"].astype(np.float32),
                        group=np.array(groups), retrieval_bands=np.array(pr.retrieval_bands))
    files = ("params.parquet", "spectra.npy", "s2_pack.npz")
    manifest = {"priors": pr.name, "placeholder": bool(pr.placeholder or nm.placeholder),
                "seed": pr.seed, "rows": len(df), "per_group": n, "groups": list(pr.groups),
                "canopy_model": model.name, "band_set": bs.name, "bands": names,
                "retrieval_bands": pr.retrieval_bands,
                "noise": {"sensor": "safari_bands.sensor, placeholder instrument (A-37)",
                          "sza_deg": nm.sza_deg, "t_atm": nm.t_atm,
                          "atmospheric_residual": ar.model_dump()},
                "sha256": {f: _sha(out / f) for f in files}, "run": run.directory.name}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    run.write_json("manifest.json", manifest)
    run.finalise(rows=len(df), out=str(out))
    print(f"wrote {out} ({len(df)} rows) and {run.directory}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
