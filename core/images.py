"""Faithful, deterministic previews; never synthesize, remove, or move objects."""

from __future__ import annotations

import io
import warnings
from pathlib import Path

from PIL import Image, ImageChops, ImageCms, ImageDraw, ImageEnhance, ImageFilter, ImageOps, ImageStat

from core.contracts import validate_recipe

MAX_BYTES = 16 * 1024 * 1024
MAX_PIXELS = 30_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def read_photo(raw: bytes) -> tuple[Image.Image, str]:
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("照片需要小于 16 MB。")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(raw)) as image:
                extension = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}.get(image.format)
                if not extension or getattr(image, "n_frames", 1) != 1:
                    raise ValueError("请使用单帧 JPG、PNG 或 WebP；暂不支持 RAW、HEIC 和动画。")
                if image.width * image.height > MAX_PIXELS or min(image.size) < 32:
                    raise ValueError("照片短边至少 32 像素，总像素不超过 3000 万。")
                image.load()
                oriented = ImageOps.exif_transpose(image)
                if image.info.get("icc_profile"):
                    try:
                        oriented = ImageCms.profileToProfile(oriented, ImageCms.ImageCmsProfile(io.BytesIO(image.info["icc_profile"])), ImageCms.createProfile("sRGB"), outputMode="RGB")
                    except (OSError, ValueError, ImageCms.PyCMSError) as exc:
                        raise ValueError("无法可靠转换照片色彩配置，请先导出 sRGB JPG。") from exc
                if oriented.mode in ("RGBA", "LA", "P"):
                    rgba = oriented.convert("RGBA")
                    base = Image.new("RGBA", rgba.size, (245, 245, 245, 255))
                    oriented = Image.alpha_composite(base, rgba)
                return oriented.convert("RGB"), extension
        except (Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
            raise ValueError("照片解码尺寸过大，请先缩小。") from exc
        except (OSError, SyntaxError) as exc:
            raise ValueError("无法解码这张照片，请检查文件是否完整。") from exc


def preview_bytes(image: Image.Image, side: int = 2048) -> bytes:
    preview = image.copy()
    preview.thumbnail((side, side), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    preview.save(buffer, format="JPEG", quality=92)
    return buffer.getvalue()


def source_bytes(path: Path) -> bytes:
    with Image.open(path) as image:
        return preview_bytes(image.convert("RGB"))


def _adjust(image: Image.Image, edit: dict) -> Image.Image:
    result = image
    if edit["exposure"]:
        factor = 2 ** edit["exposure"]
        lut = [round(min(1, (i / 255) ** 2.2 * factor) ** (1 / 2.2) * 255) for i in range(256)]
        result = result.point(lut * 3)
    if edit["shadows"] or edit["highlights"]:
        shadow, highlight = edit["shadows"], edit["highlights"]
        lut = [round(255 * max(0, min(1, v + shadow * v * (1-v) ** 2 * 2 + highlight * v*v * (1-v) * 2))) for v in (i / 255 for i in range(256))]
        result = result.point(lut * 3)
    if edit["contrast"]:
        result = ImageEnhance.Contrast(result).enhance(1 + edit["contrast"])
    if edit["saturation"]:
        result = ImageEnhance.Color(result).enhance(1 + edit["saturation"])
    if edit["warmth"]:
        red, green, blue = result.split()
        warmth = edit["warmth"]
        result = Image.merge("RGB", (red.point([round(min(255, x * (1 + warmth))) for x in range(256)]), green,
                                     blue.point([round(min(255, x * (1 - warmth))) for x in range(256)])))
    return result


def make_treatment(source: Path, recipe: dict, target: Path) -> dict | None:
    validate_recipe(recipe)
    if not recipe or not recipe["adjustments"]:
        return None
    with Image.open(source) as image:
        original = image.convert("RGB")
    result = original.copy()
    for edit in recipe["adjustments"]:
        changed = _adjust(result, edit)
        rect = edit["region"]
        if rect is None:
            result = changed
        else:
            mask = Image.new("L", (512, 512), 0)
            box = (round(rect["x"] * 512), round(rect["y"] * 512), round((rect["x"] + rect["width"]) * 512), round((rect["y"] + rect["height"]) * 512))
            ImageDraw.Draw(mask).rectangle(box, fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(max(3, min(rect["width"], rect["height"]) * 512 * .16)))
            result = Image.composite(changed, result, mask.resize(original.size, Image.Resampling.BILINEAR))
    diff = ImageChops.difference(original.resize((256, 256)), result.resize((256, 256)))
    mean_change = sum(ImageStat.Stat(diff).mean) / 3
    if mean_change < .35:
        return None
    color = target.with_suffix(".color.jpg")
    result.save(color, quality=96, subsampling=0)
    treatment = None
    crop = recipe["crop"]
    if crop and crop["width"] * crop["height"] < .999:
        width, height = result.size
        box = (round(crop["x"] * width), round(crop["y"] * height), round((crop["x"] + crop["width"]) * width), round((crop["y"] + crop["height"]) * height))
        treatment = target.with_suffix(".treatment.jpg")
        result.crop(box).save(treatment, quality=96, subsampling=0)
    return {"color_image": str(color), "treatment_image": str(treatment) if treatment else None, "mean_pixel_change": round(mean_change, 3)}
