"""Module 5: Publisher — dispatches to whichever backend PUBLISH_TARGET selects."""
from __future__ import annotations

import logging

from .clients import corevmax_client, wordpress_client

logger = logging.getLogger(__name__)


def _client():
    from .env import get_publish_target

    return corevmax_client if get_publish_target() == "corevmax" else wordpress_client


def resolve_category_id(category_name: str) -> int | None:
    return _client().resolve_category_id(category_name)


def fetch_internal_link_candidates(
    keyword: str,
    category_id: int | None = None,
    config: dict | None = None,
) -> list[dict]:
    return _client().fetch_internal_link_candidates(keyword, category_id=category_id, config=config)


def upload_featured_media(local_image_path: str) -> dict:
    """Returns {'attachment_id', 'source_url'}."""
    media = _client().upload_media(local_image_path)
    return {"attachment_id": media["id"], "source_url": media["source_url"]}


def publish_post(
    title: str,
    content: str,
    meta_description: str,
    featured_image_id: int | None,
    category_name: str,
    config: dict,
    seo_title: str = "",
    focus_keyword: str = "",
    slug: str | None = None,
    category_id: int | None = None,
) -> str:
    """Publish a post on the active target; returns the post URL.

    `title` becomes the post H1. `seo_title` is the SEO/meta title (kept separate so the
    H1 can differ). `slug` sets the URL.
    """
    client = _client()
    target = "corevmax" if client is corevmax_client else "wordpress"
    target_cfg = config.get(target, {})
    status = target_cfg.get("default_post_status", "draft")
    if category_id is None:
        category_id = client.resolve_category_id(category_name)

    meta = _build_meta(target, meta_description, target_cfg, seo_title, focus_keyword)
    result = client.create_post(
        title=title,
        content=content,
        excerpt=meta_description,
        status=status,
        featured_media=featured_image_id,
        category_id=category_id,
        meta=meta,
        slug=slug,
    )
    return result["link"]


def _build_meta(
    target: str,
    meta_description: str,
    target_cfg: dict,
    seo_title: str = "",
    focus_keyword: str = "",
) -> dict | None:
    if target == "corevmax":
        # Native Post columns — no plugin-meta shim needed (see corevmax_client.create_post).
        return {
            "seo_title": seo_title,
            "meta_description": meta_description,
            "focus_keyword": focus_keyword,
        }
    return _seo_meta(
        meta_description,
        target_cfg.get("seo_plugin", "none"),
        seo_title=seo_title,
        focus_keyword=focus_keyword,
    )


def _seo_meta(
    meta_description: str,
    plugin: str,
    seo_title: str = "",
    focus_keyword: str = "",
) -> dict | None:
    """Build WordPress SEO-plugin meta fields (title + description + focus keyword).

    NOTE for RankMath: these `rank_math_*` keys are only accepted over the REST API if
    they are registered with `show_in_rest` on the WordPress side (see the mu-plugin in
    README). Without that registration WordPress silently drops them.
    """
    plugin = (plugin or "none").lower()
    if plugin == "yoast":
        meta: dict = {}
        if meta_description:
            meta["_yoast_wpseo_metadesc"] = meta_description
        if seo_title:
            meta["_yoast_wpseo_title"] = seo_title
        if focus_keyword:
            meta["_yoast_wpseo_focuskw"] = focus_keyword
        return meta or None
    if plugin == "rankmath":
        meta = {}
        if meta_description:
            meta["rank_math_description"] = meta_description
        if seo_title:
            meta["rank_math_title"] = seo_title
        if focus_keyword:
            meta["rank_math_focus_keyword"] = focus_keyword
        return meta or None
    return None  # 'none' -> rely on excerpt only
