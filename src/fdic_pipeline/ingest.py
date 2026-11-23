from __future__ import annotations
import argparse, json, hashlib, time
from datetime import date
from pathlib import Path
import requests
import pandas as pd
from .config import BASE_URL, PAGE_SIZE, FIN_FIELDS, FAIL_FIELDS, INST_FIELDS


SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "BFT65B-FDIC-Research/1.0 (academic; resumable)"})

def get_json(endpoint: str, params: dict, retries: int = 6) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    for attempt in range(retries):
        try:
            response = SESSION.get(url, params=params, timeout=180)
            if response.status_code == 200:
                time.sleep(0.25)
                return response.json()
            response.raise_for_status()
        except (requests.RequestException, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(min(60, 2 ** (attempt + 1)))
    raise RuntimeError(f"Failed API request: {url}")


def fetch_pages(endpoint: str, fields: list[str], filters: str | None = None, sort_by: str = "CERT") -> tuple[pd.DataFrame, int]:
    records, offset, api_total = [], 0, None
    while True:
        params = {"fields": ",".join(fields), "limit": PAGE_SIZE, "offset": offset,
                  "sort_by": sort_by, "sort_order": "ASC", "format": "json"}
        if filters: params["filters"] = filters
        payload = get_json(endpoint, params)
        api_total = int(payload["meta"]["total"])
        page = [r["data"] for r in payload.get("data", [])]
        records.extend(page)
        offset += len(page)
        if not page or offset >= api_total: break
    df = pd.DataFrame(records).drop(columns=["ID"], errors="ignore")
    return df, api_total


def quarter_ends(start: date, end: date) -> list[str]:
    out = []
    for year in range(start.year, end.year + 1):
        for month, day in ((3, 31), (6, 30), (9, 30), (12, 31)):
            dt = date(year, month, day)
            if start <= dt <= end: out.append(dt.strftime("%Y%m%d"))
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""): h.update(block)
    return h.hexdigest()


def download_financials(out: Path, quarters: list[str], compression: str = "zstd") -> None:
    folder = out / "financials"; folder.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest_financials.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for idx, q in enumerate(quarters, 1):
        year, month = q[:4], int(q[4:6])
        quarter = (month - 1) // 3 + 1
        target = folder / f"YEAR={year}" / f"QUARTER=Q{quarter}" / f"REPDTE={q}.parquet"
        target.parent.mkdir(parents=True, exist_ok=True)
        entry = manifest.get(q, {})
        if target.exists() and entry.get("complete") and entry.get("sha256") == sha256_file(target):
            print(f"[{idx}/{len(quarters)}] {q}: verified existing file; skip")
            continue
        df, total = fetch_pages("financials", FIN_FIELDS, filters=f"REPDTE:{q}", sort_by="CERT")
        if df.empty:
            print(f"[{idx}/{len(quarters)}] {q}: empty result")
            continue
        df.to_parquet(target, index=False, engine="pyarrow", compression=compression)
        duplicates = int(df.duplicated(["CERT", "REPDTE"]).sum())
        complete = len(df) == total and duplicates == 0
        manifest[q] = {"rows": len(df), "api_total": total, "duplicate_keys": duplicates,
                       "complete": complete, "sha256": sha256_file(target), "compression": compression}
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"[{idx}/{len(quarters)}] {q}: rows={len(df):,}, API={total:,}, dup={duplicates}, complete={complete}")


def download_reference_tables(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, fields, sort_by in [("failures", FAIL_FIELDS, "FAILDATE"), ("institutions", INST_FIELDS, "CERT")]:
        df, total = fetch_pages(name, fields, sort_by=sort_by)
        path = out / f"{name}.parquet"
        df.to_parquet(path, index=False, engine="pyarrow", compression="zstd")
        print(f"{name}: {len(df):,} rows (API total {total:,}), SHA256={sha256_file(path)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="1984-03-31")
    ap.add_argument("--end", default="2026-06-30")
    ap.add_argument("--out", default="data_raw/fdic")
    ap.add_argument("--compression", choices=["zstd", "snappy", "gzip"], default="zstd")
    args = ap.parse_args()
    out = Path(args.out)
    qs = quarter_ends(date.fromisoformat(args.start), date.fromisoformat(args.end))
    print(f"Quarters: {len(qs)} | {qs[0]} -> {qs[-1]} | output={out.resolve()}")
    download_financials(out, qs, args.compression)
    download_reference_tables(out)

if __name__ == "__main__": main()
