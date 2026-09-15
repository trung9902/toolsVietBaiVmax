"""CoreVMax Publishing API client (media + posts + categories). DRY_RUN returns fakes.

CoreVMax is the user's own Laravel CMS (see `routes/api.php` /
`app/Http/Controllers/Api/PublishController.php` in the corevmax2 repo) — a token-authed
REST API purpose-built for this pipeline, not a general-purpose plugin ecosystem like
WordPress. Mirrors the subset of `wordpress_client`'s public surface that `publisher.py`
needs, so `publisher.py` can pick either module interchangeably.
"""
from __future__ import annotations

import logging
import mimetypes
import os
import random
import time

import requests

from ..env import get_env, is_dry_run, require_env
from .wordpress_client import vietnamese_slug  # noqa: F401 - re-exported for publisher.py

logger = logging.getLogger(__name__)

_TIMEOUT = 60
_MAX_RETRIES = 4
_BACKOFF_BASE = 5  # seconds: 5, 10, 20, 40...

_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update({"Accept": "application/json"})
        _session = s
    return _session


def _request(method: str, url: str, **kwargs) -> requests.Response:
    """Issue a request, retrying transient connection resets with backoff."""
    kwargs.setdefault("timeout", _TIMEOUT)
    kwargs.setdefault("headers", {})
    kwargs["headers"].setdefault("Authorization", f"Bearer {_token()}")
    session = _get_session()
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return session.request(method, url, **kwargs)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            last_exc = exc
            wait = _BACKOFF_BASE * (2 ** (attempt - 1))
            logger.warning(
                "CoreVMax connection reset (attempt %d/%d) on %s — retrying in %ds.",
                attempt, _MAX_RETRIES, url, wait,
            )
            if attempt < _MAX_RETRIES:
                time.sleep(wait)
    raise RuntimeError(f"CoreVMax unreachable after {_MAX_RETRIES} attempts ({url}). Last error: {last_exc}")


def _base_url() -> str:
    return require_env("CVX_BASE_URL").rstrip("/")


def _token() -> str:
    return require_env("CVX_API_TOKEN")


def upload_media(local_path: str) -> dict:
    """Upload an image to the CoreVMax media library. Returns {'id', 'source_url'}."""
    filename = os.path.basename(local_path)
    if is_dry_run():
        fake_id = random.randint(10000, 99999)
        base = get_env("CVX_BASE_URL", "https://example.com").rstrip("/")
        url = f"{base}/storage/dryrun/{filename}"
        logger.info("[DRY_RUN] Pretend-uploaded %s -> %s", filename, url)
        return {"id": fake_id, "source_url": url}

    mime = mimetypes.guess_type(local_path)[0] or "image/webp"
    with open(local_path, "rb") as fh:
        resp = _request(
            "POST",
            f"{_base_url()}/api/publish/media",
            files={"file": (filename, fh, mime)},
        )
    resp.raise_for_status()
    body = resp.json()
    return {"id": body["id"], "source_url": body["url"]}


def resolve_category_id(category_name: str) -> int | None:
    """Find a category id by name; returns None if not found (or dry-run)."""
    if is_dry_run() or not category_name:
        return None
    resp = _request(
        "GET", f"{_base_url()}/api/publish/categories", params={"search": category_name}
    )
    resp.raise_for_status()
    return resp.json().get("id")


def _fake_link_candidates(keyword: str, count: int) -> list[dict]:
    base = get_env("CVX_BASE_URL", "https://example.com").rstrip("/")
    slug = vietnamese_slug(keyword) or "bai-viet"
    return [
        {"title": f"Bài viết liên quan {i}", "url": f"{base}/vi/bai-viet/{slug}-{i}", "kind": "post"}
        for i in range(1, count + 1)
    ]


def fetch_internal_link_candidates(
    keyword: str,
    category_id: int | None = None,
    config: dict | None = None,
) -> list[dict]:
    """Internal-link candidates for the article. Returns [{'title','url','kind':'post'}].

    v1 scope: published posts only (matched by category, else recent) — no product/page
    candidates yet, unlike the WordPress client's WooCommerce-aware version.
    """
    config = config or {}
    il_cfg = (config.get("corevmax", {}) or {}).get("internal_links", {}) or {}
    max_candidates = int(il_cfg.get("max_candidates", 10))

    if is_dry_run():
        return _fake_link_candidates(keyword, max_candidates)

    params: dict = {"limit": max_candidates}
    if category_id:
        params["category_id"] = category_id
    try:
        resp = _request("GET", f"{_base_url()}/api/publish/posts", params=params)
        resp.raise_for_status()
        return [{**it, "kind": "post"} for it in resp.json()][:max_candidates]
    except Exception as exc:  # noqa: BLE001 - internal links are optional
        logger.warning("Could not fetch CoreVMax posts for internal links: %s", exc)
        return []


def fetch_product_reference(keyword: str) -> dict | None:
    """Best-match real product photo for `keyword` — used as AI-image reference material
    (see openai_image_client.generate_image) so generated images stay accurate to what's
    actually sold. Returns {'name','image_url','url'} or None (dry-run, no match, or error).
    """
    if is_dry_run() or not keyword:
        return None
    try:
        resp = _request("GET", f"{_base_url()}/api/publish/products", params={"search": keyword, "limit": 3})
        resp.raise_for_status()
        items = resp.json()
        return items[0] if items else None
    except Exception as exc:  # noqa: BLE001 - reference photo is optional
        logger.warning("Could not fetch CoreVMax product reference for %r: %s", keyword, exc)
        return None


def create_post(
    title: str,
    content: str,
    excerpt: str = "",
    status: str = "draft",
    featured_media: int | None = None,
    category_id: int | None = None,
    meta: dict | None = None,
    slug: str | None = None,
) -> dict:
    """Create a post. Returns {'id', 'link'}.

    `meta` (seo_title/meta_description/focus_keyword) is sent as native Post columns
    directly — CoreVMax has no plugin-meta shim to go through, unlike WordPress.
    """
    if is_dry_run():
        fake_id = random.randint(1000, 9999)
        base = get_env("CVX_BASE_URL", "https://example.com").rstrip("/")
        link = f"{base}/vi/bai-viet/{slug or fake_id}"
        logger.info("[DRY_RUN] Pretend-created %s post '%s' -> %s", status, title, link)
        return {"id": fake_id, "link": link}

    payload: dict = {
        "title": title,
        "body": content,
        "excerpt": excerpt,
        "status": status,
    }
    if slug:
        payload["slug"] = slug
    if featured_media:
        payload["featured_media_id"] = featured_media
    if category_id:
        payload["category_id"] = category_id
    if meta:
        payload["seo_title"] = meta.get("seo_title", "")
        payload["meta_description"] = meta.get("meta_description", "")
        payload["focus_keyword"] = meta.get("focus_keyword", "")

    resp = _request("POST", f"{_base_url()}/api/publish/posts", json=payload)
    resp.raise_for_status()
    body = resp.json()
    return {"id": body["id"], "link": body["url"]}
