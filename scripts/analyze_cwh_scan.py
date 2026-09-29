#!/usr/bin/env python3
"""Audit presisi CWH 3Y — statistik body/handle, klaster, dan sampel penilaian.

Pemakaian:
    python analyze_cwh_scan.py research-cwh-3y.json [--out out_dir] [--per-stratum 4] [--seed 33]

Keluaran (di --out):
    bodies.csv            satu baris per cup body unik (ticker, LR, LOW, RR)
    handles.csv           satu baris per assessment (body + handle low)
    ticker_summary.csv    body, klaster, dan handle per ticker
    review_sample.csv     sampel acak berstrata untuk penilaian manual (kolom verdict kosong)
    summary.txt           ringkasan angka

Skrip ini hanya MEMBACA artifact. Tidak mengubah engine.
Sesi dihitung dengan hari kerja (numpy.busday_count) karena artifact tidak memuat kalender bursa.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


OPTIONAL_FIELDS = [
    "lr_price", "lo_price", "rr_price", "hl_price", "rr_to_lr_ratio", "rr_over_lr_pct",
    "decline_sessions", "recovery_sessions", "cup_sessions", "rr_to_hl_sessions",
    "max_high_lr_to_rr_over_lr", "first_reclaim_lr_frac", "frac_closes_ge_lr",
    "handle_depth_recomputed", "max_high_rr_to_hl_over_pivot", "max_high_after_hl_over_pivot",
    "price_check", "ev_handle_duration_sessions", "ev_handle_depth_pct",
]


def load(path: str) -> pd.DataFrame:
    data = json.load(open(path))
    rows = []
    for x in data["results"]:
        sig = dict(item.split(":", 1) for item in x["structural_signature"])
        extra = {k: x[k] for k in OPTIONAL_FIELDS if k in x}
        rows.append(
            dict(extra,
                ticker=x["ticker"],
                security_id=x["security_id"],
                base_id=x["base_id"],
                lr=sig["LEFT_RIM"],
                lo=sig["CUP_LOW"],
                rr=sig["RIGHT_RIM"],
                hl=sig["HANDLE_LOW"],
                end=x["structural_end"],
                asof=x["asof_date"],
                semantics=x["candidate_semantics"].split(":")[0],
                cup_depth=x["depth_pct"],
                pivot=x["pivot_level"],
                pivot_date=x["pivot_source_date"],
                faults="|".join(x["detector_faults"]),
            )
        )
    df = pd.DataFrame(rows)
    for c in ["lr", "lo", "rr", "hl", "end", "asof", "pivot_date"]:
        df[c] = pd.to_datetime(df[c])
    return df, data


def sessions(a: pd.Series, b: pd.Series) -> np.ndarray:
    return np.busday_count(a.values.astype("datetime64[D]"), b.values.astype("datetime64[D]"))


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "decline_sessions" not in df.columns:  # artifact lama: hitung dengan hari kerja
        df["decline_sessions"] = sessions(df.lr, df.lo)
        df["recovery_sessions"] = sessions(df.lo, df.rr)
        df["cup_sessions"] = sessions(df.lr, df.rr)
        df["rr_to_handle_low_sessions"] = sessions(df.rr, df.hl)
    else:  # scan baru: jumlah sesi eksak dari OHLCV
        df["rr_to_handle_low_sessions"] = df["rr_to_hl_sessions"]
    df["decline_fraction"] = df.decline_sessions / df.cup_sessions
    df["pivot_is_right_rim"] = df.pivot_date == df.rr
    return df


def cluster_bodies(bodies: pd.DataFrame, iou_min: float = 0.5) -> pd.Series:
    """Klaster body per ticker: dua body sejenis jika interval [LR, RR] beririsan IoU >= iou_min."""
    labels = pd.Series(-1, index=bodies.index, dtype=int)
    next_label = 0
    for _, grp in bodies.groupby("security_id"):
        idx = grp.index.to_list()
        start = grp.lr.values.astype("datetime64[D]").astype(int)
        stop = grp.rr.values.astype("datetime64[D]").astype(int)
        parent = list(range(len(idx)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i in range(len(idx)):
            for j in range(i + 1, len(idx)):
                inter = min(stop[i], stop[j]) - max(start[i], start[j])
                if inter <= 0:
                    continue
                union = max(stop[i], stop[j]) - min(start[i], start[j])
                if inter / union >= iou_min:
                    parent[find(i)] = find(j)
        roots = {}
        for i, ix in enumerate(idx):
            r = find(i)
            if r not in roots:
                roots[r] = next_label
                next_label += 1
            labels[ix] = roots[r]
    return labels


def stratified_sample(bodies: pd.DataFrame, handles: pd.DataFrame, per_stratum: int, seed: int) -> pd.DataFrame:
    b = bodies.copy()
    b["cup_bin"] = pd.cut(b.cup_sessions, [0, 60, 150, 300, 10_000], labels=["<60", "60-150", "150-300", ">300"])
    b["decl_bin"] = pd.cut(b.decline_fraction, [0, 0.05, 0.15, 1.01], labels=["<5%", "5-15%", ">15%"])
    rng = np.random.default_rng(seed)
    picks = []
    for _, grp in b.groupby(["cup_bin", "decl_bin"], observed=True):
        n = min(per_stratum, len(grp))
        picks.append(grp.iloc[rng.choice(len(grp), size=n, replace=False)])
    sample = pd.concat(picks)
    # satu varian handle acak per body terpilih
    key = ["security_id", "lr", "lo", "rr"]
    h = handles.merge(sample[key + ["cup_bin", "decl_bin"]], on=key)
    h = h.sample(frac=1, random_state=seed).drop_duplicates(key)
    out = h[
        ["ticker", "lr", "lo", "rr", "hl", "cup_depth", "pivot", "cup_sessions", "decline_sessions",
         "recovery_sessions", "rr_to_handle_low_sessions", "cup_bin", "decl_bin", "cluster"]
    ].sort_values(["cup_bin", "decl_bin", "ticker"])
    for col in ["cup_ok (Y/N)", "handle_ok (Y/N)", "alasan"]:
        out[col] = ""
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path")
    ap.add_argument("--out", default="cwh_audit_out")
    ap.add_argument("--per-stratum", type=int, default=4)
    ap.add_argument("--seed", type=int, default=33)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    df, raw = load(args.json_path)
    handles = add_features(df)
    key = ["security_id", "lr", "lo", "rr"]
    body_cols = key + ["ticker", "cup_depth", "pivot", "decline_sessions", "recovery_sessions",
                       "cup_sessions", "decline_fraction"]
    body_cols += [c for c in ["lr_price", "lo_price", "rr_price", "rr_to_lr_ratio", "max_high_lr_to_rr_over_lr",
                              "first_reclaim_lr_frac", "frac_closes_ge_lr"] if c in handles.columns]
    bodies = handles[body_cols].drop_duplicates(key).reset_index(drop=True)
    n_handles = handles.groupby(key).size().rename("handle_variants").reset_index()
    bodies = bodies.merge(n_handles, on=key)
    bodies["cluster"] = cluster_bodies(bodies)
    handles = handles.merge(bodies[key + ["cluster"]], on=key)

    per_ticker = bodies.groupby("ticker").agg(
        bodies=("cluster", "size"), clusters=("cluster", "nunique"), handle_variants=("handle_variants", "sum")
    )
    per_ticker["bodies_per_cluster"] = (per_ticker.bodies / per_ticker.clusters).round(2)

    bodies.to_csv(out / "bodies.csv", index=False)
    handles.drop(columns=["faults"]).to_csv(out / "handles.csv", index=False)
    per_ticker.to_csv(out / "ticker_summary.csv")
    sample = stratified_sample(bodies, handles, args.per_stratum, args.seed)
    sample.to_csv(out / "review_sample.csv", index=False)

    q = [0.05, 0.25, 0.5, 0.75, 0.95]
    lines = [
        f"engine_sha            : {raw['engine_sha']}",
        f"assessments           : {len(handles)}",
        f"faults non-empty      : {(handles.faults != '').sum()}",
        f"tickers w/ CWH        : {handles.ticker.nunique()}",
        f"unique bodies (LR+LOW+RR, per security) : {len(bodies)}",
        f"clusters (IoU>=0.5)   : {bodies.cluster.nunique()}  -> {len(bodies)/bodies.cluster.nunique():.1f} body/klaster",
        f"clusters per ticker   : median {per_ticker.clusters.median():.0f}, max {per_ticker.clusters.max()}",
        f"handle variants/body  : mean {bodies.handle_variants.mean():.2f}, max {bodies.handle_variants.max()}",
        f"pivot == right rim    : {handles.pivot_is_right_rim.mean():.1%} dari assessment",
        f"asof terbaru          : {(handles["asof"] == handles["asof"].max()).mean():.1%} dari assessment",
        "",
        "Sebaran cup body (sesi / depth):",
        bodies[["decline_sessions", "recovery_sessions", "cup_sessions", "cup_depth", "decline_fraction"]]
        .quantile(q).round(3).to_string(),
        "",
        f"cup > 250 sesi        : {(bodies.cup_sessions > 250).mean():.1%}",
        f"decline <= 5 sesi     : {(bodies.decline_sessions <= 5).mean():.1%}",
        f"decline < 10% durasi  : {(bodies.decline_fraction < 0.10).mean():.1%}",
        f"cup depth < 12%       : {(bodies.cup_depth < 0.12).mean():.1%}",
        "",
        "Jarak right rim -> handle low (sesi):",
        handles.rr_to_handle_low_sessions.quantile(q + [0.9]).sort_index().round(1).to_string(),
        f"> 20 sesi : {(handles.rr_to_handle_low_sessions > 20).mean():.1%}",
        f"> 40 sesi : {(handles.rr_to_handle_low_sessions > 40).mean():.1%}",
        f"> 120 sesi: {(handles.rr_to_handle_low_sessions > 120).mean():.1%}",
    ]
    if "rr_to_lr_ratio" in bodies.columns:
        r = bodies.rr_to_lr_ratio
        lines += [
            "",
            "Rim relation (right rim / left rim; aturan engine hanya >= 0.90):",
            r.quantile(q).round(3).to_string(),
            f"RR > 1.05 x LR : {(r > 1.05).mean():.1%}",
            f"RR > 1.10 x LR : {(r > 1.10).mean():.1%}",
            f"RR > 1.25 x LR : {(r > 1.25).mean():.1%}",
            f"RR dalam +-5% LR : {((r - 1).abs() <= 0.05).mean():.1%}",
        ]
        if "first_reclaim_lr_frac" in bodies.columns:
            f = bodies.first_reclaim_lr_frac
            lines += [
                f"harga sudah close >= LR sebelum RR : {f.notna().mean():.1%}",
                f"  ...dan itu terjadi di paruh pertama pemulihan : {(f < 0.5).mean():.1%}",
            ]
    if "handle_depth_recomputed" in handles.columns:
        hd = handles.handle_depth_recomputed
        lines += [
            "",
            "Kedalaman handle (dihitung ulang dari OHLCV):",
            hd.quantile(q).round(3).to_string(),
            f"> 12% : {(hd > 0.12).mean():.1%}   > 20% : {(hd > 0.20).mean():.1%}",
        ]
    if "price_check" in handles.columns:
        lines.append(f"price_check MISMATCH : {(handles.price_check != 'OK').sum()}")
    text = "\n".join(lines)
    (out / "summary.txt").write_text(text + "\n")
    print(text)
    print(f"\nFile ditulis ke: {out.resolve()}")


if __name__ == "__main__":
    main()