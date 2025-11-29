from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

from .models import ProductConfig, ProductURL


def load_products_config(path: Path) -> Dict[str, ProductConfig]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    items: List[ProductConfig] = []

    for item in data.get("items", []):
        urls = [ProductURL(**entry) for entry in item.get("urls", [])]
        alternatives = item.get("alternatives") or []

        config = ProductConfig(
            id=item["id"],
            name=item["name"],
            category=item.get("category", "misc"),
            urls=urls,
            desired_price=item.get("desired_price"),
            alternatives=alternatives,
        )
        items.append(config)

    return {item.id: item for item in items}


