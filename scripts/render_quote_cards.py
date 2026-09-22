#!/usr/bin/env python3
"""Render verified quote JSON into the canonical vertical quote-card HTML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_SIZES = {"auto", "xl", "normal", "sm"}


def fail(message: str) -> None:
    raise ValueError(message)


def validate(data: Any) -> None:
    if not isinstance(data, dict):
        fail("顶层 JSON 必须是对象")
    book = data.get("book")
    if not isinstance(book, dict):
        fail("缺少 book 对象")
    for field in ("title", "author"):
        if not isinstance(book.get(field), str) or not book[field].strip():
            fail(f"book.{field} 为必填非空文本")
    quotes = data.get("quotes")
    if not isinstance(quotes, list) or not quotes:
        fail("quotes 必须是非空数组，不要为了达到固定数量补写摘录")
    seen: set[str] = set()
    for index, quote in enumerate(quotes):
        location = f"quotes[{index}]"
        if not isinstance(quote, dict):
            fail(f"{location} 必须是对象")
        for field in ("text", "source", "locator"):
            if not isinstance(quote.get(field), str) or not quote[field].strip():
                fail(f"{location}.{field} 为必填非空文本")
        normalized = "".join(quote["text"].split())
        if normalized in seen:
            fail(f"{location}.text 与前面的摘录重复")
        seen.add(normalized)
        if len(quote["text"]) > 160:
            fail(f"{location}.text 超过 160 个字符，请按连续完整片段拆页")
        size = quote.get("size", "auto")
        if size not in ALLOWED_SIZES:
            fail(f"{location}.size 必须是：{', '.join(sorted(ALLOWED_SIZES))}")
        url = quote.get("url")
        if url is not None and (not isinstance(url, str) or not url.startswith(("http://", "https://"))):
            fail(f"{location}.url 必须是 http(s) URL")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="符合 quote-card-schema.md 的 JSON")
    parser.add_argument("output", type=Path, help="输出的自包含 HTML")
    args = parser.parse_args()

    input_path = args.input.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    data = json.loads(input_path.read_text(encoding="utf-8"))
    validate(data)

    template_path = Path(__file__).resolve().parent.parent / "references" / "reading-quote-cards-template.html"
    template = template_path.read_text(encoding="utf-8")
    placeholder = "__QUOTE_DATA__"
    if template.count(placeholder) != 1:
        fail(f"模板必须且只能包含一个 {placeholder} 占位符")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template.replace(placeholder, payload), encoding="utf-8")
    print(f"rendered {len(data['quotes'])} quote cards to {output_path}")


if __name__ == "__main__":
    main()
