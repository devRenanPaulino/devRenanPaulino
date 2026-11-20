"""SVG Builder — orchestrator connecting config, stats, and templates."""

from generator.templates import (
    galaxy_header,
    stats_card,
    tech_stack,
    projects_constellation,
    mission_log,
    bug_hunt,
)


class SVGBuilder:
    """Builds all SVG assets from config and GitHub data.

    Expects a config dict that has already been through validate_config(),
    which resolves theme defaults and applies missing optional fields.
    """

    def __init__(self, config: dict, stats: dict, languages: dict, stats_updated: str = None):
        self.config = config
        self.stats = stats
        self.languages = languages
        self.stats_updated = stats_updated
        self.theme = config["theme"]
        self.galaxy_arms = config.get("galaxy_arms", [])
        self.projects = config.get("projects", [])

    def render_galaxy_header(self) -> str:
        return galaxy_header.render(
            config=self.config,
            theme=self.theme,
            galaxy_arms=self.galaxy_arms,
            projects=self.projects,
        )

    def render_stats_card(self) -> str:
        metrics = self.config["stats"]["metrics"]
        return stats_card.render(
            stats=self.stats,
            metrics=metrics,
            theme=self.theme,
            updated=self.stats_updated,
        )

    def render_tech_stack(self) -> str:
        lang_config = self.config.get("languages", {})
        return tech_stack.render(
            languages=self.languages,
            galaxy_arms=self.galaxy_arms,
            theme=self.theme,
            exclude=lang_config.get("exclude", []),
            max_display=lang_config.get("max_display", 8),
        )

    def render_projects_constellation(self) -> str:
        return projects_constellation.render(
            projects=self.projects,
            galaxy_arms=self.galaxy_arms,
            theme=self.theme,
        )

    def render_mission_log(self) -> str:
        return mission_log.render(
            entries=self.config.get("mission_log", []),
            galaxy_arms=self.galaxy_arms,
            theme=self.theme,
        )

    def render_bug_hunt(self) -> str:
        return bug_hunt.render(
            bugs=self.config.get("bug_hunt", {}).get("bugs", []),
            theme=self.theme,
        )
