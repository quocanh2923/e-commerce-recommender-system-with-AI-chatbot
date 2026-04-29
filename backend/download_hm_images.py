r"""
download_hm_images.py
=====================
Tai chon loc anh san pham H&M tu Kaggle competition (~150KB/anh) sao cho
moi category co du PER_CATEGORY anh, thay vi tai images.zip 25GB.

Yeu cau:
  - kaggle.json da dat trong %USERPROFILE%\.kaggle\
  - Da accept rules competition tren web Kaggle
  - articles.csv da co trong backend/data/

Chay: python download_hm_images.py
"""

import csv
import sys
import zipfile
from pathlib import Path

# Windows console default cp1252 khong in duoc tieng Viet -> ep utf-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data_utils import (
    ARTICLES_CSV, IMG_DIR,
    CATEGORIES, PER_CATEGORY,
    categorize_article, article_image_path,
)

COMPETITION = "h-and-m-personalized-fashion-recommendations"


def main() -> None:
    if not ARTICLES_CSV.exists():
        print(f"[ERROR] Khong tim thay {ARTICLES_CSV}")
        sys.exit(1)

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("[ERROR] Chua cai kaggle. Chay: pip install kaggle")
        sys.exit(1)

    # ── Phase 1: dem so anh da co cho moi category ──────────
    needed: dict[str, int] = {c: PER_CATEGORY for c in CATEGORIES}

    with open(ARTICLES_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = categorize_article(row)
            if cat is None or needed.get(cat, 0) <= 0:
                continue
            aid = row.get("article_id", "").strip()
            if not aid:
                continue
            local = article_image_path(aid)
            if local.exists() and local.stat().st_size > 0:
                needed[cat] -= 1

    print("=== Trang thai hien tai (so anh CON THIEU moi category) ===")
    for cat in CATEGORIES:
        have = PER_CATEGORY - needed[cat]
        flag = "OK" if needed[cat] <= 0 else f"thieu {needed[cat]}"
        print(f"  {cat:12s}: da co {have:3d}/{PER_CATEGORY}  [{flag}]")
    print()

    if all(n <= 0 for n in needed.values()):
        print("Tat ca category da du anh. Khong can tai them.")
        return

    # ── Phase 2: tai bo sung ────────────────────────────────
    api = KaggleApi()
    api.authenticate()
    print("[OK] Kaggle API authenticated. Bat dau tai bo sung...\n")

    success = 0
    failed: list[tuple[str, str]] = []

    with open(ARTICLES_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if all(n <= 0 for n in needed.values()):
                break

            cat = categorize_article(row)
            if cat is None or needed.get(cat, 0) <= 0:
                continue

            aid = row.get("article_id", "").strip()
            if not aid:
                continue

            dest_file = article_image_path(aid)
            if dest_file.exists() and dest_file.stat().st_size > 0:
                continue  # Phase 1 da dem

            dest_dir = dest_file.parent
            dest_dir.mkdir(parents=True, exist_ok=True)

            kaggle_file = f"images/{aid[:3]}/{aid}.jpg"
            try:
                api.competition_download_file(
                    competition=COMPETITION,
                    file_name=kaggle_file,
                    path=str(dest_dir),
                    quiet=True,
                )
                # Kaggle co the wrap thanh .jpg.zip - giai nen
                zipped = dest_dir / f"{aid}.jpg.zip"
                if zipped.exists():
                    with zipfile.ZipFile(zipped) as zf:
                        zf.extractall(dest_dir)
                    zipped.unlink()
                if dest_file.exists() and dest_file.stat().st_size > 0:
                    success += 1
                    needed[cat] -= 1
                else:
                    failed.append((aid, "no file after download"))
            except Exception as e:
                failed.append((aid, f"{type(e).__name__}: {str(e)[:60]}"))

            total_done = success + len(failed)
            if total_done % 25 == 0 and total_done > 0:
                still_need = sum(max(0, n) for n in needed.values())
                print(f"  ...da xu ly {total_done}: success={success} fail={len(failed)} con thieu={still_need}")

    # ── Bao cao ─────────────────────────────────────────────
    print("\n======= HOAN THANH =======")
    print(f"  Tai moi: {success}")
    print(f"  Loi:     {len(failed)}")
    print()
    print("=== Phan bo cuoi cung ===")
    for cat in CATEGORIES:
        have = PER_CATEGORY - needed[cat]
        flag = "OK" if needed[cat] <= 0 else f"VAN THIEU {needed[cat]}"
        print(f"  {cat:12s}: {have:3d}/{PER_CATEGORY}  [{flag}]")

    total = sum(f.stat().st_size for f in IMG_DIR.rglob("*.jpg") if f.is_file())
    print(f"\n  Tong dung luong images/: {total / 1024 / 1024:.1f} MB")
    print(f"  Vi tri: {IMG_DIR}\n")
    print("Buoc tiep theo: python seed.py")


if __name__ == "__main__":
    main()
