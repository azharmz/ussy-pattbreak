#!/usr/bin/env python3
"""Research-only CWH scan dengan field diagnostik tambahan (tidak mengubah detektor).

Menjalankan extractor kanonik yang sama dengan production
(`extract_core_morphology_predictions`) pada tiap file histori OHLCV, lalu
MENAMBAHKAN field ukur dari OHLCV yang sama. Keputusan detektor tidak disentuh:
status, fault, pivot, dan id identik dengan yang dihasilkan engine.

Letakkan di `scripts/research_cwh_scan.py`. Contoh:

    python scripts/research_cwh_scan.py --history-dir history/ohlcv \
        --window-years 3 --out-dir results/cwh-3y --workers 4

Input : satu file parquet per security. Kolom wajib: date, high, low, close.
        security_id / ticker diambil dari kolom bila ada, jika tidak dari nama file.
        (Di layout R2 nama file = security_id, mis. AN8068571086.parquet.)
Output: <out-dir>/research-cwh-3y.json  (bentuk sama dengan artifact lama + field baru)
        <out-dir>/research-cwh-3y.csv   (datar, siap dianalisis)

Field baru per assessment (semua dihitung dari OHLCV, bukan dari detektor):
    lr_price, lo_price, rr_price, hl_price       harga left rim / cup low / right rim / handle low
    rr_to_lr_ratio                               rr_price / lr_price  (aturan engine hanya >= 0.90)
    rr_over_lr_pct                               rr_to_lr_ratio - 1
    decline_sessions, recovery_sessions, cup_sessions, rr_to_hl_sessions
    max_high_lr_to_rr_over_lr                    high tertinggi di antara LR dan RR, relatif terhadap LR
    first_reclaim_lr_frac                        sesi (LO -> close pertama >= LR) / sesi (LO -> RR); kosong bila tak pernah
    frac_closes_ge_lr                            porsi close >= harga LR pada rentang LO..RR
    handle_depth_recomputed                      (rr_price - hl_price) / rr_price
    max_high_rr_to_hl_over_pivot                 high tertinggi RR..HL relatif terhadap pivot
    max_high_after_hl_over_pivot                 high tertinggi setelah HL sampai asof relatif terhadap pivot
    price_check                                  OK bila pivot == high(RR) dan depth == (LR-LO)/LR (asumsi landmark = high/low)
    ev_*                                         field `evidence` dari prediksi (durasi/kedalaman handle, dll.)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from oneil_patterns.production.output import ENGINE_VERSION, ProductionAssessmentRecord  # noqa: E402
from oneil_patterns.validation.canonical_predictions import extract_core_morphology_predictions  # noqa: E402

RECOGNIZED = "CUP_WITH_HANDLE_RECOGNIZED"
PRICE_TOL = 1e-6


# --------------------------------------------------------------------------- data
def load_history(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df.columns = [str(c).lower() for c in df.columns]
    missing = {"date", "high", "low", "close"} - set(df.columns)
    if missing:
        raise ValueError(f"{path.name}: kolom wajib hilang: {sorted(missing)}")
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_convert("UTC").dt.tz_localize(None)
    df["date"] = df["date"].dt.normalize()
    df = df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    if "security_id" not in df.columns:
        df["security_id"] = path.stem
    if "ticker" not in df.columns:
        df["ticker"] = path.stem
    return df


def window_frame(df: pd.DataFrame, asof: pd.Timestamp | None, years: int) -> tuple[pd.DataFrame, date]:
    last = df["date"].iloc[-1]
    end = min(asof, last) if asof is not None else last
    start = end - pd.DateOffset(years=years)
    frame = df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)
    return frame, end.date()


# ------------------------------------------------------------------- measurement
def _ratio(num: float, den: float) -> float | None:
    return float(num / den) if den else None


def measure(prediction, frame: pd.DataFrame, pos: dict[date, int]) -> dict:
    """Hitung field ukur untuk satu prediksi CWH dari OHLCV. Tidak mengubah prediksi."""
    sig = dict(item.split(":", 1) for item in prediction.structural_signature)
    d_lr, d_lo, d_rr, d_hl = (date.fromisoformat(sig[k]) for k in ("LEFT_RIM", "CUP_LOW", "RIGHT_RIM", "HANDLE_LOW"))
    i_lr, i_lo, i_rr, i_hl = pos[d_lr], pos[d_lo], pos[d_rr], pos[d_hl]

    high = frame["high"].to_numpy(dtype=float)
    low = frame["low"].to_numpy(dtype=float)
    close = frame["close"].to_numpy(dtype=float)

    lr_p, lo_p, rr_p, hl_p = high[i_lr], low[i_lo], high[i_rr], low[i_hl]
    pivot = float(prediction.pivot_level)

    price_ok = abs(rr_p - pivot) <= PRICE_TOL * max(1.0, abs(pivot))
    if prediction.depth_pct is not None and lr_p:
        price_ok = price_ok and abs((lr_p - lo_p) / lr_p - float(prediction.depth_pct)) <= PRICE_TOL

    between = high[i_lr + 1 : i_rr]
    max_between = float(between.max()) if between.size else None

    reclaim_hits = np.nonzero(close[i_lo + 1 : i_rr] >= lr_p)[0]
    first_reclaim_frac = None
    if reclaim_hits.size and i_rr > i_lo:
        first_reclaim_frac = float((reclaim_hits[0] + 1) / (i_rr - i_lo))

    rr_to_hl = high[i_rr + 1 : i_hl + 1]
    after_hl = high[i_hl + 1 :]

    row = {
        "lr_date": d_lr.isoformat(),
        "lo_date": d_lo.isoformat(),
        "rr_date": d_rr.isoformat(),
        "hl_date": d_hl.isoformat(),
        "lr_price": float(lr_p),
        "lo_price": float(lo_p),
        "rr_price": float(rr_p),
        "hl_price": float(hl_p),
        "rr_to_lr_ratio": _ratio(rr_p, lr_p),
        "rr_over_lr_pct": (_ratio(rr_p, lr_p) - 1.0) if lr_p else None,
        "decline_sessions": int(i_lo - i_lr),
        "recovery_sessions": int(i_rr - i_lo),
        "cup_sessions": int(i_rr - i_lr),
        "rr_to_hl_sessions": int(i_hl - i_rr),
        "max_high_lr_to_rr_over_lr": _ratio(max_between, lr_p) if max_between is not None else None,
        "first_reclaim_lr_frac": first_reclaim_frac,
        "frac_closes_ge_lr": float((close[i_lo : i_rr + 1] >= lr_p).mean()),
        "handle_depth_recomputed": _ratio(rr_p - hl_p, rr_p),
        "max_high_rr_to_hl_over_pivot": _ratio(float(rr_to_hl.max()), pivot) if rr_to_hl.size else None,
        "max_high_after_hl_over_pivot": _ratio(float(after_hl.max()), pivot) if after_hl.size else None,
        "price_check": "OK" if price_ok else "MISMATCH",
    }
    for key, value in (prediction.evidence or {}).items():
        if isinstance(value, (int, float, str, bool)) or value is None:
            row[f"ev_{key}"] = value
    return row


def analyze_frame(frame: pd.DataFrame, asof: date, include_ambiguous: bool = False) -> list[dict]:
    """Jalankan extractor kanonik pada satu frame dan kembalikan baris CWH yang sudah diperkaya."""
    if frame.empty:
        return []
    security_id = str(frame["security_id"].iloc[0])
    ticker = str(frame["ticker"].iloc[0])
    pos = {d: i for i, d in enumerate(pd.to_datetime(frame["date"]).dt.date)}

    rows = []
    for prediction in extract_core_morphology_predictions(frame, asof_date=asof):
        if prediction.pattern != "CUP_WITH_HANDLE":
            continue
        if not include_ambiguous and prediction.detector_status != RECOGNIZED:
            continue
        record = ProductionAssessmentRecord.from_prediction(
            security_id=security_id, ticker=ticker, asof_date=asof, prediction=prediction
        )
        row = record.to_dict()
        row["structural_signature"] = list(row["structural_signature"])
        row["detector_faults"] = list(row["detector_faults"])
        row.update(measure(prediction, frame, pos))
        rows.append(row)
    return rows


# ----------------------------------------------------------------------- driver
def _worker(args: tuple) -> tuple[str, list[dict], str | None]:
    path, asof_iso, years, include_ambiguous = args
    name = Path(path).name
    try:
        df = load_history(Path(path))
        asof = pd.Timestamp(asof_iso) if asof_iso else None
        frame, asof_date = window_frame(df, asof, years)
        rows = analyze_frame(frame, asof_date, include_ambiguous)
        for row in rows:
            row["_history_key"] = name
            row["_window_start"] = frame["date"].iloc[0].date().isoformat()
            row["_window_end"] = frame["date"].iloc[-1].date().isoformat()
        return name, rows, None
    except Exception as exc:  # satu file rusak tidak boleh menghentikan scan
        return name, [], f"{type(exc).__name__}: {exc}"


def git_sha() -> str:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        return sha + ("+dirty" if dirty else "")
    except Exception:
        return "unknown"


def write_outputs(out_dir: Path, meta: dict, rows: list[dict]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(meta, recognized_cwh=len(rows), results=rows)
    (out_dir / "research-cwh-3y.json").write_text(json.dumps(payload, default=str))
    flat = pd.DataFrame(rows)
    if not flat.empty:
        flat["structural_signature"] = flat["structural_signature"].map("|".join)
        flat["detector_faults"] = flat["detector_faults"].map("|".join)
    flat.to_csv(out_dir / "research-cwh-3y.csv", index=False)


def main() -> None:
    ap = argparse.ArgumentParser(description="Research-only CWH scan dengan field diagnostik tambahan")
    ap.add_argument("--history-dir", required=True, help="folder berisi *.parquet OHLCV per security")
    ap.add_argument("--out-dir", default="results/cwh-3y")
    ap.add_argument("--window-years", type=int, default=3)
    ap.add_argument("--asof", help="YYYY-MM-DD; default: bar terakhir tiap file")
    ap.add_argument("--tickers", help="filter berdasarkan NAMA FILE tanpa .parquet (di layout R2 itu security_id, mis. AN8068571086), pisahkan koma")
    ap.add_argument("--limit", type=int, help="batasi jumlah file (untuk uji cepat)")
    ap.add_argument("--include-ambiguous", action="store_true", help="sertakan CWH non-RECOGNIZED")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()

    files = sorted(Path(args.history_dir).glob("*.parquet"))
    if args.tickers:
        wanted = {t.strip().upper() for t in args.tickers.split(",")}
        files = [f for f in files if f.stem.upper() in wanted]
    if args.limit:
        files = files[: args.limit]
    if not files:
        sys.exit("tidak ada file parquet yang cocok")

    jobs = [(str(f), args.asof, args.window_years, args.include_ambiguous) for f in files]
    rows: list[dict] = []
    errors: list[dict] = []
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = pool.map(_worker, jobs, chunksize=8)
            for n, (name, r, err) in enumerate(results, 1):
                rows.extend(r)
                if err:
                    errors.append({"file": name, "error": err})
                if n % 100 == 0:
                    print(f"{n}/{len(files)} file, {len(rows)} CWH", file=sys.stderr)
    else:
        for n, job in enumerate(jobs, 1):
            name, r, err = _worker(job)
            rows.extend(r)
            if err:
                errors.append({"file": name, "error": err})
            if n % 100 == 0:
                print(f"{n}/{len(files)} file, {len(rows)} CWH", file=sys.stderr)

    meta = {
        "engine_sha": git_sha(),
        "engine_version": ENGINE_VERSION,
        "scan_params": {"window_years": args.window_years, "asof": args.asof, "include_ambiguous": args.include_ambiguous},
        "history_files": len(files),
        "errors": errors,
    }
    write_outputs(Path(args.out_dir), meta, rows)

    mismatch = sum(1 for r in rows if r["price_check"] != "OK")
    print(f"selesai: {len(files)} file, {len(rows)} CWH, {len(errors)} error, price_check MISMATCH={mismatch}")
    if mismatch:
        print("PERINGATAN: asumsi landmark = high/low pada tanggalnya tidak berlaku untuk sebagian baris; "
              "field harga baris itu tidak boleh dipercaya.", file=sys.stderr)


if __name__ == "__main__":
    main()