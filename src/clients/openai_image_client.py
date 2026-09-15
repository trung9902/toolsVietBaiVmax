"""OpenAI image generation (gpt-image-1). DRY_RUN returns a fake placeholder.

Two modes:
  - Reference-based (`reference_bytes` given): `images.edit` with `input_fidelity="high"`
    so the output stays visually close to a real product photo — used when a genuine photo
    of the product is available (see corevmax_client.fetch_product_reference), for sites
    where the image must look like the actual product, not a generic illustration.
  - Text-only: `images.generate` with a photorealistic prompt — fallback when no reference
    photo exists.
"""
from __future__ import annotations

import io
import logging

import requests
from PIL import Image

from ..env import is_dry_run, require_env
from .replicate_client import _fake_background

logger = logging.getLogger(__name__)

_client = None

_MODEL = "gpt-image-1"


def _real_client():
    global _client
    if _client is None:
        from openai import OpenAI

        _client = OpenAI(api_key=require_env("OPENAI_API_KEY"))
    return _client


def download_reference(image_url: str) -> bytes | None:
    """Fetch a reference photo (e.g. a real product photo URL). None on any failure."""
    try:
        resp = requests.get(image_url, timeout=60)
        resp.raise_for_status()
        return resp.content
    except Exception as exc:  # noqa: BLE001 - reference photo is optional
        logger.warning("Could not download reference image %s: %s", image_url, exc)
        return None


def generate_image(prompt: str, size: int = 1024, reference_bytes: bytes | None = None) -> Image.Image:
    """Return a Pillow RGB image of `size` x `size` for the given prompt.

    `reference_bytes` (if given) anchors the output to a real product photo so the result
    stays accurate to what's actually sold, instead of a generic AI illustration.
    """
    if is_dry_run():
        logger.info(
            "[DRY_RUN] Fabricating placeholder gpt-image-1 %s for prompt: %.60s",
            "edit" if reference_bytes else "generation", prompt,
        )
        return _fake_background(size, prompt)

    client = _real_client()
    size_str = f"{size}x{size}"

    if reference_bytes:
        resp = client.images.edit(
            image=("reference.png", reference_bytes, "image/png"),
            prompt=prompt,
            model=_MODEL,
            size=size_str,
            input_fidelity="high",
            quality="high",
        )
    else:
        resp = client.images.generate(
            model=_MODEL,
            prompt=prompt,
            size=size_str,
            quality="high",
        )

    b64 = resp.data[0].b64_json
    import base64

    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
