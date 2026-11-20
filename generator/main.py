"""Entry point for the Galaxy Profile README generator."""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests
import yaml

from generator.config import ConfigError, validate_config
from generator.github_api import GitHubAPI
from generator.svg_builder import SVGBuilder

logger = logging.getLogger(__name__)

DEMO_STATS = {"commits": 1847, "stars": 342, "prs": 156, "issues": 89, "repos": 42}
DEMO_LANGUAGES = {
    "Python": 450000,
    "TypeScript": 380000,
    "JavaScript": 120000,
    "Go": 95000,
    "Rust": 45000,
    "Shell": 30000,
    "Dockerfile": 15000,
    "CSS": 10000,
}


CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "generated", "cache.json")


def _load_cache() -> dict:
    """Last good stats/languages, so a failed or token-less run never shows zeros."""
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def generate(args):
    """Generate SVGs from config (existing behavior extracted into a function)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    demo = getattr(args, "demo", False)

    # Load config
    if demo:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.example.yml")
    else:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yml")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        if demo:
            logger.error("config.example.yml not found.")
        else:
            logger.error("config.yml not found. Copy config.example.yml to config.yml and edit it.")
        sys.exit(1)

    try:
        config = validate_config(config)
    except ConfigError as e:
        logger.error("Invalid config: %s", e)
        sys.exit(1)

    username = config["username"]

    logger.info("Generating profile SVGs for @%s...", username)

    stats_date = None
    if demo:
        logger.info("Demo mode: using hardcoded stats and languages.")
        stats = DEMO_STATS
        languages = DEMO_LANGUAGES
    else:
        api = GitHubAPI(username, orgs=config.get("organizations", []))
        cache = _load_cache()
        today = datetime.now(timezone.utc).date().isoformat()

        logger.info("Fetching stats...")
        stats = None
        try:
            stats = api.fetch_stats()
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            logger.warning("Could not fetch stats (%s).", e)

        # The REST fallback (no token) undercounts commits and issues, so only
        # trust it when there is nothing better cached.
        if stats is not None and (api.stats_source == "graphql" or not cache.get("stats")):
            cache["stats"] = stats
            cache["stats_updated"] = today
            stats_date = today
        elif cache.get("stats"):
            logger.warning("Using cached stats (last good fetch: %s).", cache.get("stats_updated", "unknown"))
            stats = cache["stats"]
            stats_date = cache.get("stats_updated")
        else:
            stats = {"commits": 0, "stars": 0, "prs": 0, "issues": 0, "repos": 0}

        logger.info("Fetching languages...")
        languages = None
        try:
            languages = api.fetch_languages()
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            logger.warning("Could not fetch languages (%s).", e)

        if languages and api.language_errors == 0:
            cache["languages"] = languages
        elif cache.get("languages"):
            logger.warning("Languages incomplete (%d errors); using cached languages.", api.language_errors)
            languages = cache["languages"]
        else:
            languages = languages or {}

        _save_cache(cache)

    logger.info("Stats: %s", stats)
    logger.info("Languages: %d found", len(languages))

    # Build SVGs
    builder = SVGBuilder(config, stats, languages, stats_updated=stats_date)
    output_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "generated")
    os.makedirs(output_dir, exist_ok=True)

    svgs = {
        "galaxy-header.svg": builder.render_galaxy_header(),
        "stats-card.svg": builder.render_stats_card(),
        "tech-stack.svg": builder.render_tech_stack(),
        "projects-constellation.svg": builder.render_projects_constellation(),
        "mission-log.svg": builder.render_mission_log(),
        "bug-hunt.svg": builder.render_bug_hunt(),
    }

    for filename, content in svgs.items():
        path = os.path.join(output_dir, filename)
        with open(path, "w") as f:
            f.write(content)
        logger.info("Wrote %s", path)

    logger.info("Done! %d SVGs generated.", len(svgs))


def main():
    parser = argparse.ArgumentParser(description="Generate Galaxy Profile SVGs")
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand: init
    subparsers.add_parser("init", help="Interactive setup wizard to create config.yml")

    # Subcommand: generate
    gen_parser = subparsers.add_parser("generate", help="Generate SVGs from config")
    gen_parser.add_argument(
        "--demo",
        action="store_true",
        help="Generate SVGs with demo data (no API calls, uses config.example.yml)",
    )

    # Top-level --demo for backward compatibility (python -m generator.main --demo)
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Generate SVGs with demo data (no API calls, uses config.example.yml)",
    )

    args = parser.parse_args()

    if args.command == "init":
        from generator.cli_init import run_init
        run_init()
    else:
        # Default behavior: generate (supports both `generate --demo` and `--demo`)
        generate(args)


if __name__ == "__main__":
    main()
