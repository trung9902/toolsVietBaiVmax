"""Pipeline orchestrator — implements execution_flow steps 3.1–3.12.

One `run_once()` call processes a single Pending keyword end-to-end, writing results (or an
error) back to the workbook, and always cleaning up temporary images afterwards.
"""
from __future__ import annotations

import logging

from . import content_generator, html_parser, publisher
from .clients.wordpress_client import vietnamese_slug
from .config_manager import ConfigManager, now_string
from .image_pipeline import ImagePipeline, cleanup_images, rate_limit_sleep

logger = logging.getLogger(__name__)


def run_once(keep_images: bool = False, settings_path: str = "settings.json") -> bool:
    """Process the next Pending row. Returns True if a row was processed, False if none."""
    cm = ConfigManager(settings_path=settings_path)
    config = cm.load_configurations()

    row = cm.fetch_next_pending_row()
    if row is None:
        logger.info("No Pending keyword found. Nothing to do this cycle.")
        return False

    row_index = row["row_index"]
    logger.info("Processing row %d — keyword: %s", row_index, row["keyword"])
    temp_paths: list[str] = []

    try:
        cm.set_status(row_index, "Processing")

        prompts = config["prompts"]
        banned = prompts.get("banned_words", [])
        model = config["openai"]["model"]

        # Resolve category + gather existing posts to use as internal links.
        category_id = publisher.resolve_category_id(row["category"])
        internal_links = publisher.fetch_internal_link_candidates(
            row["keyword"], category_id=category_id, config=config
        )
        logger.info("Found %d internal link candidate(s).", len(internal_links))

        # 3.4 — content
        post = content_generator.generate_seo_post(
            keyword=row["keyword"],
            audience=row["audience"],
            intent=row["intent"],
            category=row["category"],
            system_prompt_web_seo=prompts["system_prompt_web_seo"],
            banned_words=banned,
            model=model,
            internal_links=internal_links,
            all_keywords=row.get("all_keywords", ""),
        )
        rate_limit_sleep(config)

        image_pipeline = ImagePipeline(config)

        # 3.5 / 3.6 — featured image -> WP media
        featured_path = image_pipeline.build_image_for_text(post["title"])
        temp_paths.append(featured_path)
        featured = publisher.upload_featured_media(featured_path)
        featured_url = featured["source_url"]
        cm.update_row_data(row_index, {"featured_image_url": featured_url})
        rate_limit_sleep(config)

        # 3.7 — inject H2 images
        modified_html, content_urls = html_parser.process_and_inject_media(
            post["html_content"], image_pipeline, config, temp_paths=temp_paths
        )
        cm.update_row_data(row_index, {"content_image_urls": ", ".join(content_urls)})

        # 3.8 — publish post (H1 = post title; SEO title pinned separately)
        slug = vietnamese_slug(row["keyword"])
        post_url = publisher.publish_post(
            title=post["h1"],
            content=modified_html,
            meta_description=post["meta_description"],
            featured_image_id=featured["attachment_id"],
            category_name=row["category"],
            config=config,
            seo_title=post["seo_title"],
            focus_keyword=row["keyword"],
            slug=slug,
            category_id=category_id,
        )

        # 3.9 — record success. Write the AI outputs into their dedicated columns:
        # Title Website (seo_title) / Meta description / H1 / Nội dung website. The sapo is
        # kept only as the opening paragraph inside the body, so the standalone "Đoạn Sapo
        # website" column is intentionally left blank (redundant).
        # Intent + audience are user INPUT columns and are left untouched.
        cm.update_row_data(
            row_index,
            {
                "seo_title": post["seo_title"],
                "meta_description": post["meta_description"],
                "h1": post["h1"],
                "html_content": modified_html,
                "status": "Success",
                "link_website": post_url,
                "published_at": now_string(),
                "error_log": "",
            },
        )
        logger.info("Row %d SUCCESS — web: %s", row_index, post_url)
        return True

    except Exception as exc:  # noqa: BLE001 - 3.12 catch-all
        logger.exception("Row %d FAILED", row_index)
        try:
            cm.log_error_to_sheet(row_index, f"{type(exc).__name__}: {exc}")
        except Exception:  # noqa: BLE001
            logger.exception("Could not write error to sheet for row %d", row_index)
        return True

    finally:
        if not keep_images:
            cleanup_images(temp_paths)
        else:
            logger.info("Kept %d temp image(s) in output/ for inspection.", len(temp_paths))
