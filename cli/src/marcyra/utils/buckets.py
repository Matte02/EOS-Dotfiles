from pathlib import Path
import os
import json
from typing import Optional, Union

import numpy as np
from PIL import Image
import colorsys
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score

from marcyra.utils.paths import pictures_dir, wallpaper_buckets_path, image_cache_dir
from marcyra.utils.material import get_score_for_image

CLUSTER_METHODS = ["kmeans", "gmm", "agglomerative", "dbscan", "spectral", "quantize"]


def mean_hsv(path: Path, n_clusters: int = 40, thumb_size=(128, 128)):
    from marcyra.utils.paths import get_thumb

    with Image.open(get_thumb(path)) as im:
        im = im.convert("RGB").resize(thumb_size)
        arr = np.asarray(im, dtype=np.float32).reshape(-1, 3) / 255.0

    km = KMeans(n_clusters=n_clusters, random_state=0).fit(arr)
    hsv = [colorsys.rgb_to_hsv(*c) for c in km.cluster_centers_]
    return np.mean(hsv, axis=0)


def sort_buckets(
    directory: Optional[Union[str, Path]] = None,
    update_symlinks: bool = True,
    min_size: int = 5,
):
    directory = Path(directory or pictures_dir)
    print("Sorting:", directory)

    images = collect_images(directory)
    if not images:
        print("No images found.")
        return

    # Extract HCT features
    data = []
    for p in images:
        cache_base = image_cache_dir(p)
        primary = get_score_for_image(p, cache_base)
        data.append([primary.hue, primary.chroma, primary.tone])

    X = np.array(data)
    from sklearn.mixture import GaussianMixture

    # Auto-select cluster count using BIC
    lowest_bic = np.inf
    best_k = 0
    for k in range(4, 15):
        gmm = GaussianMixture(n_components=k, random_state=42)
        gmm.fit(X)
        bic = gmm.bic(X)
        if bic < lowest_bic:
            lowest_bic = bic
            best_k = k

    model = GaussianMixture(n_components=best_k, random_state=42)
    labels = model.fit_predict(X)

    # Group wallpapers
    buckets = {}
    for lbl, p in zip(labels, images):
        buckets.setdefault(str(lbl), []).append(str(p.resolve()))

    # Merge small clusters
    buckets = merge_small_clusters(buckets, X, labels, min_size)

    # Save and refresh symlinks
    buckets = save_buckets(buckets, wallpaper_buckets_path)

    if update_symlinks:
        out_dir = pictures_dir / "bucket_out"
        refresh_symlinks(buckets, out_dir)


def collect_images(directory: Path) -> list[Path]:
    images = sorted([f for f in directory.rglob("*") if f.suffix.lower() in (".jpg", ".png", ".jpeg")])

    print(f"Found {len(images)} images")
    for img_path in images[:]:
        try:
            with Image.open(img_path) as im:
                print(img_path.name, im.size, im.mode)
        except Exception as e:
            print("Failed to open", img_path, e)
    return images


def save_buckets(buckets, out_json: Path) -> dict:
    with open(out_json, "w") as f:
        json.dump(buckets, f, indent=2)
    return buckets


def refresh_symlinks(buckets: dict, out_dir: Path):
    if out_dir.exists():
        for bucket in out_dir.iterdir():
            if bucket.is_dir():
                for link in bucket.iterdir():
                    if link.is_symlink():
                        link.unlink()
                bucket.rmdir()
    else:
        out_dir.mkdir(exist_ok=True)

    for bucket, files in buckets.items():
        d = out_dir / bucket
        d.mkdir(exist_ok=True)
        for f in files:
            target = Path(f).resolve()
            link = d / target.name
            if not link.exists():
                os.symlink(target, link)


def merge_small_clusters(buckets, data, labels, min_size):
    centroids = cluster_centroids(buckets, data, labels)
    merged = True

    while merged:
        merged = False
        small_clusters = [lbl for lbl, imgs in buckets.items() if len(imgs) < min_size]

        if not small_clusters:
            break

        for small_lbl in small_clusters:
            if small_lbl not in buckets:
                continue  # Might have been merged already

            # Find closest larger cluster
            target_lbl = None
            min_dist = float("inf")

            for lbl, imgs in buckets.items():
                if lbl == small_lbl or len(imgs) < min_size:
                    continue
                dist = hct_distance(centroids[small_lbl], centroids[lbl])
                if dist < min_dist:
                    target_lbl = lbl
                    min_dist = dist

            # If we found a merge target, move all images
            if target_lbl is not None:
                buckets[target_lbl].extend(buckets[small_lbl])
                del buckets[small_lbl]
                merged = True

        # Recompute centroids after each merge round
        centroids = cluster_centroids(buckets, data, labels)

    return buckets


def hct_distance(a, b):
    return np.linalg.norm(a - b)


def cluster_centroids(buckets, data, labels):
    centroids = {}
    for lbl in buckets:
        idxs = [i for i, l in enumerate(labels) if str(l) == lbl]
        cluster_data = data[idxs]
        centroids[lbl] = cluster_data.mean(axis=0)
    return centroids
