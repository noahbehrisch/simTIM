from dataclasses import dataclass

import matplotlib.pyplot as plt


@dataclass(frozen=True)
class ColorPalette:
    BLUE: str = "#0072B2"
    ORANGE: str = "#E69F00"
    GREEN: str = "#009E73"
    VERMILLION: str = "#D55E00"
    PURPLE: str = "#CC79A7"
    SKY_BLUE: str = "#56B4E9"
    YELLOW: str = "#F0E442"
    BLACK: str = "#000000"
    GRAY: str = "#999999"
    DARK_BLUE: str = "#004D80"
    LIGHT_ORANGE: str = "#FFD180"
    LIGHT_GREEN: str = "#66D9B8"
    DARK_GRAY: str = "#666666"
    LIGHT_GRAY: str = "#CCCCCC"


PALETTE = ColorPalette()


class VisualizationTheme:
    def __init__(self):
        self.palette = PALETTE
        self._init_semantic_colors()
        self._init_matplotlib_style()

    def _init_semantic_colors(self):
        self.colors: dict[str, str] = {
            "attacker": self.palette.VERMILLION,
            "defender": self.palette.BLUE,
            "start_action": self.palette.SKY_BLUE,
            "action_succeeded": self.palette.GREEN,
            "action_failed": self.palette.ORANGE,
            "action_interrupted": self.palette.PURPLE,
            "action_aborted": self.palette.GRAY,
            "attack_detected": self.palette.PURPLE,
            "damage": self.palette.VERMILLION,
            "gain": self.palette.ORANGE,
            "cost": self.palette.BLUE,
            "admin": self.palette.VERMILLION,
            "user": self.palette.ORANGE,
            "visible": self.palette.YELLOW,
            "none": self.palette.GREEN,
            "safe": self.palette.GREEN,
            "node_exposed": self.palette.VERMILLION,
            "node_internal": self.palette.BLUE,
            "node_compromised": self.palette.ORANGE,
            "node_safe": self.palette.GREEN,
            "link": self.palette.GRAY,
            "link_attack_path": self.palette.VERMILLION,
            "success": self.palette.GREEN,
            "failure": self.palette.VERMILLION,
            "warning": self.palette.ORANGE,
            "info": self.palette.SKY_BLUE,
            "neutral": self.palette.GRAY,
            "primary": self.palette.BLUE,
            "secondary": self.palette.ORANGE,
            "tertiary": self.palette.GREEN,
        }

        self.event_types: list[tuple[str, str, str]] = [
            ("start_action", "Action Started", "o"),
            ("action_succeeded", "Success", "^"),
            ("action_failed", "Failed", "x"),
            ("action_interrupted", "Interrupted", "s"),
            ("attack_detected", "Detected", "d"),
        ]

    def _init_matplotlib_style(self):
        plt.style.use("default")
        self.color_cycle = [
            self.palette.BLUE,
            self.palette.ORANGE,
            self.palette.GREEN,
            self.palette.VERMILLION,
            self.palette.PURPLE,
            self.palette.SKY_BLUE,
        ]

    def get_color(self, key: str) -> str:
        if key not in self.colors:
            raise KeyError(f"Unknown color key: {key}. Available: {list(self.colors.keys())}")
        return self.colors[key]

    def get_color_safe(self, key: str, default: str | None = None) -> str:
        return self.colors.get(key, default or self.palette.GRAY)

    def get_colormap(self, n_colors: int, palette_type: str = "categorical") -> list[str]:
        if palette_type == "categorical":
            base_colors = [
                self.palette.BLUE,
                self.palette.ORANGE,
                self.palette.GREEN,
                self.palette.VERMILLION,
                self.palette.PURPLE,
                self.palette.SKY_BLUE,
                self.palette.YELLOW,
                self.palette.DARK_BLUE,
            ]
            if n_colors <= len(base_colors):
                return base_colors[:n_colors]
            return [base_colors[i % len(base_colors)] for i in range(n_colors)]

        elif palette_type == "sequential":
            cmap = plt.colormaps["viridis"]
            return [self._rgb_to_hex(cmap(i / (n_colors - 1))[:3]) for i in range(n_colors)]

        elif palette_type == "diverging":
            cmap = plt.colormaps["RdYlBu_r"]
            return [self._rgb_to_hex(cmap(i / (n_colors - 1))[:3]) for i in range(n_colors)]

        else:
            return self.get_colormap(n_colors, "categorical")

    def get_scenario_colors(self, n_scenarios: int) -> list[str]:
        cmap = plt.colormaps["viridis"]
        return [self._rgb_to_hex(cmap(i / max(n_scenarios - 1, 1))[:3]) for i in range(n_scenarios)]

    def get_access_level_colors(self) -> dict[str, str]:
        return {
            "admin": self.colors["admin"],
            "user": self.colors["user"],
            "visible": self.colors["visible"],
            "none": self.colors["none"],
            "safe": self.colors["safe"],
        }

    def get_economic_colors(self) -> dict[str, str]:
        return {
            "damage": self.colors["damage"],
            "gain": self.colors["gain"],
            "cost": self.colors["cost"],
        }

    def get_actor_colors(self) -> dict[str, str]:
        return {
            "attacker": self.colors["attacker"],
            "defender": self.colors["defender"],
        }

    def get_network_colors(self) -> dict[str, str]:
        return {
            "exposed": self.colors["node_exposed"],
            "internal": self.colors["node_internal"],
            "compromised": self.colors["node_compromised"],
            "safe": self.colors["node_safe"],
            "link": self.colors["link"],
            "attack_path": self.colors["link_attack_path"],
        }

    def apply_to_figure(self, fig: plt.Figure) -> None:
        fig.patch.set_facecolor("white")
        for ax in fig.get_axes():
            ax.set_facecolor("white")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(True, alpha=0.3, linestyle="-", linewidth=0.5)

    @staticmethod
    def _rgb_to_hex(rgb: tuple[float, ...]) -> str:
        r, g, b = int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        return f"#{r:02x}{g:02x}{b:02x}"


_theme_instance: VisualizationTheme | None = None


def get_theme() -> VisualizationTheme:
    global _theme_instance
    if _theme_instance is None:
        _theme_instance = VisualizationTheme()
    return _theme_instance


def get_color(key: str) -> str:
    return get_theme().get_color(key)


def get_colors() -> dict[str, str]:
    return get_theme().colors.copy()


def get_palette() -> ColorPalette:
    return PALETTE
