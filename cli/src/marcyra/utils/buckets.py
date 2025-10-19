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

from marcyra.utils.paths import pictures_dir, wallpaper_buckets_path

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
    method: str = "gmm",
    update_symlinks: bool = True,
    min_size: int = 3,
):
    directory = Path(directory or pictures_dir)
    print("Sorting:", directory)

    images = collect_images(directory)
    if not images:
        print("No images found.")
        return

    features = extract_features(images)
    print(f"Extracted {features.shape[0]} feature vectors")

    k = estimate_best_k(features) if method in ("kmeans", "gmm", "agglomerative", "spectral") else None
    labels = cluster_images(features, method, k)
    labels = merge_small_clusters(features, labels, min_size=min_size)

    buckets = save_buckets(images, labels, wallpaper_buckets_path)

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


def extract_features(images: list[Path]) -> np.ndarray:
    features = []
    for img_path in images:
        features.append(mean_hsv(img_path))

    features = np.array(features)
    print("Feature shape:", features.shape)
    return features


def estimate_best_k(features: np.ndarray, k_min=4, k_max=15, metric="silhouette") -> int:
    if metric == "bic":
        best_score, best_k = np.inf, k_min
        for k in range(k_min, k_max + 1):
            gmm = GaussianMixture(n_components=k, random_state=0).fit(features)
            score = gmm.bic(features)
            if score < best_score:
                best_score, best_k = score, k
        return best_k

    # silhouette
    best_score, best_k = -1, k_min
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=0)
        lbls = km.fit_predict(features)
        score = silhouette_score(features, lbls)
        if score > best_score:
            best_score, best_k = score, k
    return best_k


def save_buckets(images: list[Path], labels: np.ndarray, out_json: Path) -> dict:
    buckets = {}
    for img_path, label in zip(images, labels):
        buckets.setdefault(f"bucket_{label}", []).append(str(img_path))

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


def cluster_images(features: np.ndarray, method="kmeans", k=5):
    if method == "kmeans":
        from sklearn.cluster import KMeans

        model = KMeans(n_clusters=k, random_state=0)
        return model.fit_predict(features)

    elif method == "gmm":
        from sklearn.mixture import GaussianMixture

        model = GaussianMixture(n_components=k, random_state=0)
        return model.fit_predict(features)

    elif method == "agglomerative":
        from sklearn.cluster import AgglomerativeClustering

        model = AgglomerativeClustering(n_clusters=k)
        return model.fit_predict(features)

    elif method == "dbscan":
        from sklearn.cluster import DBSCAN

        model = DBSCAN(eps=0.15, min_samples=2)
        return model.fit_predict(features)

    elif method == "spectral":
        from sklearn.cluster import SpectralClustering

        model = SpectralClustering(n_clusters=k, assign_labels="discretize", random_state=0)
        return model.fit_predict(features)

    elif method == "quantize":
        return quantize_colors(features)

    else:
        raise ValueError(f"Unknown method: {method}")


def quantize_colors(features: np.ndarray, bins=8):
    # Assume HSV in [0,1]; bucket by hue
    hues = (features[:, 0] * bins).astype(int)
    return hues


def merge_small_clusters(features, labels, min_size=3):
    unique_labels = np.unique(labels)
    cluster_sizes = {l: np.sum(labels == l) for l in unique_labels}
    cluster_means = {l: features[labels == l].mean(axis=0) for l in unique_labels}

    for label, size in cluster_sizes.items():
        if size < min_size:
            # find nearest larger cluster
            current_mean = cluster_means[label]
            candidates = [
                (l, np.linalg.norm(cluster_means[l] - current_mean))
                for l in unique_labels
                if cluster_sizes[l] >= min_size
            ]
            if not candidates:
                continue
            new_label = min(candidates, key=lambda x: x[1])[0]
            labels[labels == label] = new_label

    return labels
