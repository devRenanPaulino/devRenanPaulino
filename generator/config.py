"""Config validation and defaults for the Galaxy Profile generator."""

from generator.utils import resolve_theme, HEX_COLOR_RE


class ConfigError(ValueError):
    """Raised when config.yml has invalid or missing data."""


def validate_config(config: dict) -> dict:
    """Validate and apply defaults to a parsed config dict.

    Args:
        config: raw dict from yaml.safe_load()

    Returns:
        config dict with defaults applied for optional fields

    Raises:
        ConfigError: if required fields are missing or values are invalid
    """
    if not isinstance(config, dict):
        raise ConfigError("Config must be a YAML mapping (dict).")

    # username — required
    username = config.get("username")
    if not username or not isinstance(username, str) or not username.strip():
        raise ConfigError("'username' is required and must be a non-empty string.")

    # profile.name — required
    profile = config.get("profile", {})
    if not isinstance(profile, dict):
        raise ConfigError("'profile' must be a mapping.")
    if not profile.get("name"):
        raise ConfigError("'profile.name' is required.")

    # galaxy_arms — required, must be a list
    galaxy_arms = config.get("galaxy_arms", [])
    if not isinstance(galaxy_arms, list) or not galaxy_arms:
        raise ConfigError("'galaxy_arms' must be a non-empty list.")
    for i, arm in enumerate(galaxy_arms):
        if not isinstance(arm, dict):
            raise ConfigError(f"galaxy_arms[{i}] must be a mapping.")
        if not arm.get("name"):
            raise ConfigError(f"galaxy_arms[{i}].name is required.")
        if not arm.get("color"):
            raise ConfigError(f"galaxy_arms[{i}].color is required.")
        if not isinstance(arm.get("items", []), list):
            raise ConfigError(f"galaxy_arms[{i}].items must be a list.")

    # projects — optional, validate entries if present
    projects = config.get("projects", [])
    if not isinstance(projects, list):
        raise ConfigError("'projects' must be a list.")
    for i, proj in enumerate(projects):
        if not isinstance(proj, dict):
            raise ConfigError(f"projects[{i}] must be a mapping.")
        if not proj.get("repo"):
            raise ConfigError(f"projects[{i}].repo is required.")
        arm_idx = proj.get("arm", 0)
        if not isinstance(arm_idx, int) or arm_idx < 0 or arm_idx >= len(galaxy_arms):
            raise ConfigError(
                f"projects[{i}].arm must be an integer from 0 to {len(galaxy_arms) - 1}."
            )

    # organizations — optional list of org logins included in the language chart
    orgs = config.get("organizations", [])
    if not isinstance(orgs, list) or not all(isinstance(o, str) and o for o in orgs):
        raise ConfigError("'organizations' must be a list of organization logins.")
    config["organizations"] = orgs

    # mission_log — optional timeline of milestones
    log = config.get("mission_log", [])
    if not isinstance(log, list):
        raise ConfigError("'mission_log' must be a list.")
    for i, entry in enumerate(log):
        if not isinstance(entry, dict) or not entry.get("title"):
            raise ConfigError(f"mission_log[{i}] must be a mapping with a 'title'.")
    config["mission_log"] = log

    # bug_hunt — optional mini-game settings
    hunt = config.get("bug_hunt", {})
    if not isinstance(hunt, dict) or not isinstance(hunt.get("bugs", []), list):
        raise ConfigError("'bug_hunt.bugs' must be a list of labels.")
    config["bug_hunt"] = hunt

    # theme — optional, validate hex codes
    user_theme = config.get("theme", {})
    if not isinstance(user_theme, dict):
        raise ConfigError("'theme' must be a mapping.")
    for key, value in user_theme.items():
        if not isinstance(value, str) or not HEX_COLOR_RE.match(value):
            raise ConfigError(
                f"theme.{key} must be a valid hex color (e.g. #00d4ff), got '{value}'."
            )

    # Apply theme defaults
    config["theme"] = resolve_theme(user_theme)

    # Apply other defaults
    config["profile"].setdefault("tagline", "")
    config["profile"].setdefault("philosophy", "")
    config.setdefault("social", {})
    config.setdefault("projects", [])
    config.setdefault("stats", {}).setdefault(
        "metrics", ["commits", "stars", "prs", "issues", "repos"]
    )
    lang_cfg = config.setdefault("languages", {})
    lang_cfg.setdefault("exclude", [])
    lang_cfg.setdefault("max_display", 8)

    return config
