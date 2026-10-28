"""The CLI runs and reports honestly."""

from __future__ import annotations

import pytest

from safari_bands.cli import main


def test_validate_succeeds_on_the_shipped_configs(capsys):
    assert main(["validate"]) == 0
    out = capsys.readouterr().out
    assert "OK: no errors" in out


def test_validate_surfaces_placeholder_warnings(capsys):
    """Unanswered Q2-Q6 must be visible every time, not buried."""
    main(["validate"])
    out = capsys.readouterr().out
    assert "placeholder_values" in out
    assert "WARNING" in out


def test_indices_matrix_renders(capsys):
    assert main(["indices"]) == 0
    out = capsys.readouterr().out
    assert "NDTI" in out
    assert "config_c" in out
    # The scope caveat must travel with the output.
    assert "baselines and interpretability aids only" in out


def test_indices_for_one_band_set(capsys):
    assert main(["indices", "--band-set", "config_b"]) == 0
    out = capsys.readouterr().out
    assert "NDWI_Gao" in out
    assert "Cannot form" in out


def test_indices_rejects_an_unknown_band_set(capsys):
    assert main(["indices", "--band-set", "nope"]) == 2
    assert "unknown band set" in capsys.readouterr().err


def test_bands_prints_the_set(capsys):
    assert main(["bands", "config_c"]) == 0
    out = capsys.readouterr().out
    assert "2190" in out
    assert "ingaas_ext" in out


def test_bands_shows_the_cirrus_exemption(capsys):
    assert main(["bands", "config_b"]) == 0
    out = capsys.readouterr().out
    assert "atmospheric" in out


def test_validate_run_writes_a_run_directory(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("safari_bands.cli.start_run", _capture_run(tmp_path))
    assert main(["validate", "--run"]) == 0

    runs = list(tmp_path.iterdir())
    assert len(runs) == 1
    assert (runs[0] / "resolved_config.yaml").is_file()
    assert (runs[0] / "provenance.json").is_file()
    assert (runs[0] / "findings.txt").is_file()


def _capture_run(root):
    from safari_bands.provenance import start_run as real_start_run

    def wrapper(name, seed=0, runs_root=None, **metadata):
        return real_start_run(name, seed=seed, runs_root=root, **metadata)

    return wrapper


def test_no_command_exits_with_usage_error():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_snr_reports_every_band_and_the_placeholder_label(capsys):
    assert main(["snr", "sentinel2_msi"]) == 0
    out = capsys.readouterr().out
    assert "PLACEHOLDER" in out
    for b in ("B2", "B8A", "B11", "B12"):
        assert b in out


def test_snr_rejects_an_unknown_band_set(capsys):
    assert main(["snr", "no_such_set"]) == 2


def test_snr_json_export_carries_every_band_and_the_placeholder_flag(tmp_path, capsys):
    import json
    out = tmp_path / "noise.json"
    assert main(["snr", "sentinel2_p6_12band", "--json", str(out)]) == 0
    t = json.loads(out.read_text())
    assert t["placeholder"] is True
    assert list(t["bands"])[-1] == "B12" and len(t["bands"]) == 12
    assert all(b["gain_e_per_rho"] > 0 for b in t["bands"].values())
