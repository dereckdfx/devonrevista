"""Shared locations for the daily publishing pipeline."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ARTDIR = os.path.join(ROOT, "articulos")
CONTENT = os.path.join(HERE, "content")
TEMPLATE = os.path.join(HERE, "article.tpl")
IMGCACHE = os.path.join(HERE, "imgcache.json")
POOLS = os.path.join(HERE, "pools.json")
MANIFEST = os.path.join(HERE, "manifest.json")
NEWSLETTER = os.path.join(ROOT, "newsletter", "latest.html")


def latest_content():
    """The newest dated article set in content/, e.g. content/2026-10-26.json."""
    files = sorted(f for f in os.listdir(CONTENT) if f.endswith(".json"))
    if not files:
        raise SystemExit(f"no article set in {CONTENT}")
    return os.path.join(CONTENT, files[-1])
