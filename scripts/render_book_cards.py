#!/usr/bin/env python3
"""Render validated book-card JSON into the canonical self-contained HTML."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
from pathlib import Path
from typing import Any


ALLOWED_TYPES = {"statement", "list", "steps", "quote"}


def fail(message: str) -> None:
    raise ValueError(message)


def strings_in(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings_in(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings_in(child)


def validate(data: Any) -> None:
    if not isinstance(data, dict):
        fail("顶层 JSON 必须是对象")
    book = data.get("book")
    if not isinstance(book, dict):
        fail("缺少 book 对象")
    for field in ("title", "overview"):
        if not isinstance(book.get(field), str) or not book[field].strip():
            fail(f"book.{field} 为必填非空文本")
    cover_points = book.get("cover_points")
    if not isinstance(cover_points, list) or len(cover_points) != 3:
        fail("book.cover_points 必须恰好包含 3 项阅读收获")
    if any(not isinstance(point, str) or not point.strip() for point in cover_points):
        fail("book.cover_points 的每一项都必须是非空文本")
    pages = data.get("pages")
    if not isinstance(pages, list) or not pages:
        fail("pages 必须是非空数组；第 1 页封面由模板自动生成")
    for index, page in enumerate(pages, start=2):
        location = f"pages[{index - 2}]（第 {index} 页）"
        if not isinstance(page, dict):
            fail(f"{location} 必须是对象")
        page_type = page.get("type")
        if page_type not in ALLOWED_TYPES:
            fail(f"{location}.type 不支持：{page_type!r}")
        if not page.get("title") or not page.get("section"):
            fail(f"{location} 必须包含 title 和 section")
        if page_type == "statement":
            body = page.get("body", [])
            if not isinstance(body, list) or len(body) > 3:
                fail(f"{location}.body 最多 3 段，超出请拆页")
        elif page_type in {"list", "steps"}:
            items = page.get("items")
            limit = 4 if page_type == "list" else 3
            if not isinstance(items, list) or not items:
                fail(f"{location}.items 必须是非空数组")
            if len(items) > limit:
                fail(f"{location}.items 最多 {limit} 项，超出请拆页")
            for item_index, item in enumerate(items):
                if not isinstance(item, dict) or not item.get("title"):
                    fail(f"{location}.items[{item_index}] 必须包含 title")
        elif page_type == "quote":
            if not page.get("quote"):
                fail(f"{location}.quote 不能为空")
    forbidden = [book["title"].strip()]
    if isinstance(book.get("author"), str) and book["author"].strip():
        forbidden.append(book["author"].strip())
    for text in strings_in(pages):
        for identity in forbidden:
            if identity and identity in text:
                fail(f"第 2 页以后的可见内容不得重复书名或作者：{identity!r}")


def strip_non_output_metadata(value: Any) -> Any:
    """Drop legacy evidence and source fields before embedding JSON in HTML."""
    if isinstance(value, dict):
        return {
            key: strip_non_output_metadata(child)
            for key, child in value.items()
            if key not in {"evidence", "sources", "boundary", "year"}
        }
    if isinstance(value, list):
        return [strip_non_output_metadata(child) for child in value]
    return value


def embed_cover_image(data: dict[str, Any], input_path: Path) -> None:
    cover = data["book"].get("cover_image")
    if not cover or cover.startswith("data:"):
        return
    if cover.startswith(("http://", "https://")):
        fail("cover_image 必须是本地文件或 data URI，确保最终 HTML 自包含")
    image_path = Path(cover).expanduser()
    if not image_path.is_absolute():
        image_path = input_path.parent / image_path
    if not image_path.is_file():
        fail(f"找不到封面图片：{image_path}")
    mime = mimetypes.guess_type(image_path.name)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    data["book"]["cover_image"] = f"data:{mime};base64,{encoded}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="符合 content-schema.md 的 JSON")
    parser.add_argument("output", type=Path, help="输出的自包含 HTML")
    args = parser.parse_args()

    input_path = args.input.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    data = json.loads(input_path.read_text(encoding="utf-8"))
    validate(data)
    embed_cover_image(data, input_path)
    data = strip_non_output_metadata(data)

    template_path = Path(__file__).resolve().parent.parent / "references" / "reading-card-template.html"
    template = template_path.read_text(encoding="utf-8")
    placeholder = "__BOOK_DATA__"
    if template.count(placeholder) != 1:
        fail(f"模板必须且只能包含一个 {placeholder} 占位符")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template.replace(placeholder, payload), encoding="utf-8")
    print(f"rendered {1 + len(data['pages'])} content pages to {output_path}")


if __name__ == "__main__":
    main()
