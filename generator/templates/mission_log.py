"""SVG template: Mission Log timeline (850x220). Pure SMIL, loops forever."""

from generator.utils import esc, wrap_text, resolve_arm_colors

WIDTH, HEIGHT = 850, 220
TRACK_Y = 112
LOOP = 12.0
X_MARGIN = 78


def _empty(theme):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" ry="12"
        fill="{theme['nebula']}" stroke="{theme['star_dust']}" stroke-width="1"/>
  <text x="{WIDTH / 2}" y="{HEIGHT / 2}" fill="{theme['text_faint']}" font-size="12"
        font-family="monospace" text-anchor="middle" dominant-baseline="middle">No mission log entries configured</text>
</svg>'''


def render(entries: list, galaxy_arms: list, theme: dict) -> str:
    """Render the timeline.

    Args:
        entries: list of dicts with when, title, detail and optional arm
        galaxy_arms: arm configs, used to color each checkpoint
        theme: color palette dict
    """
    entries = (entries or [])[:7]
    n = len(entries)
    if n == 0:
        return _empty(theme)

    arm_colors = resolve_arm_colors(galaxy_arms, theme)
    cyan = theme.get("synapse_cyan", "#00d4ff")
    x0, x1 = X_MARGIN, WIDTH - X_MARGIN
    step = (x1 - x0) / (n - 1) if n > 1 else 0

    nodes = []
    for i, entry in enumerate(entries):
        x = x0 + i * step
        arm_idx = entry.get("arm", i % len(arm_colors))
        color = arm_colors[arm_idx % len(arm_colors)]
        lit = 0.85 * i / (n - 1) + 0.005 if n > 1 else 0.005
        detail_lines = wrap_text(str(entry.get("detail", "")), 22)[:2]
        detail_svg = "\n".join(
            f'    <text x="{x:.1f}" y="{TRACK_Y + 54 + j * 14}" fill="{theme["text_dim"]}" '
            f'font-size="10" font-family="sans-serif" text-anchor="middle">{esc(line)}</text>'
            for j, line in enumerate(detail_lines)
        )
        live = ""
        if entry.get("current"):
            live = (
                f'    <circle cx="{x:.1f}" cy="{TRACK_Y}" r="6" fill="none" stroke="{color}" stroke-width="1.5">\n'
                f'      <animate attributeName="r" values="6;20;6" dur="2s" repeatCount="indefinite"/>\n'
                f'      <animate attributeName="opacity" values="0.9;0;0.9" dur="2s" repeatCount="indefinite"/>\n'
                f'    </circle>\n'
            )
        nodes.append(f'''  <g>
    <text x="{x:.1f}" y="{TRACK_Y - 28}" fill="{color}" font-size="11" font-family="monospace"
          letter-spacing="1" text-anchor="middle" opacity="0.9">{esc(str(entry.get("when", "")))}</text>
    <line x1="{x:.1f}" y1="{TRACK_Y - 20}" x2="{x:.1f}" y2="{TRACK_Y - 9}" stroke="{color}" stroke-width="1" opacity="0.35"/>
    <circle cx="{x:.1f}" cy="{TRACK_Y}" r="9" fill="none" stroke="{color}" stroke-width="1" opacity="0.4">
      <animate attributeName="r" values="8;13;8" dur="3.2s" begin="-{i * 0.5:.1f}s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.5;0.05;0.5" dur="3.2s" begin="-{i * 0.5:.1f}s" repeatCount="indefinite"/>
    </circle>
{live}    <circle cx="{x:.1f}" cy="{TRACK_Y}" r="5" fill="{color}" opacity="0.25">
      <animate attributeName="opacity" keyTimes="0;{lit:.4f};{lit + 0.02:.4f};0.97;1" values="0.25;0.25;1;1;0.25" dur="{LOOP}s" repeatCount="indefinite"/>
    </circle>
    <circle cx="{x:.1f}" cy="{TRACK_Y}" r="1.8" fill="#ffffff" opacity="0.9"/>
    <text x="{x:.1f}" y="{TRACK_Y + 36}" fill="{theme['text_bright']}" font-size="12" font-weight="bold"
          font-family="sans-serif" text-anchor="middle">{esc(str(entry.get("title", "")))}</text>
{detail_svg}
  </g>''')
    nodes_str = "\n".join(nodes)

    bl = 16
    bk = theme["text_faint"]
    brackets = (
        f'  <g opacity="0.4" fill="none" stroke="{bk}" stroke-width="1.5">'
        f'\n    <polyline points="5,{bl + 5} 5,5 {bl + 5},5"/>'
        f'\n    <polyline points="{WIDTH - bl - 5},5 {WIDTH - 5},5 {WIDTH - 5},{bl + 5}"/>'
        f'\n    <polyline points="5,{HEIGHT - bl - 5} 5,{HEIGHT - 5} {bl + 5},{HEIGHT - 5}"/>'
        f'\n    <polyline points="{WIDTH - bl - 5},{HEIGHT - 5} {WIDTH - 5},{HEIGHT - 5} {WIDTH - 5},{HEIGHT - bl - 5}"/>'
        f'\n  </g>'
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <filter id="ship-glow" x="-200%" y="-200%" width="500%" height="500%">
      <feGaussianBlur stdDeviation="4"/>
    </filter>
    <linearGradient id="track-grad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{cyan}" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="{cyan}" stop-opacity="0.9"/>
    </linearGradient>
  </defs>

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" ry="12"
        fill="{theme['nebula']}" stroke="{theme['star_dust']}" stroke-width="1"/>
{brackets}

  <text x="30" y="38" fill="{theme['text_faint']}" font-size="11" font-family="monospace" letter-spacing="3">MISSION LOG</text>
  <text x="{WIDTH - 30}" y="38" fill="{theme['text_faint']}" font-size="10" font-family="monospace"
        text-anchor="end" opacity="0.5">{n} CHECKPOINTS</text>

  <!-- Track -->
  <line x1="{x0}" y1="{TRACK_Y}" x2="{x1}" y2="{TRACK_Y}" stroke="{theme['star_dust']}" stroke-width="2" stroke-dasharray="2,6" stroke-linecap="round"/>
  <line x1="{x0}" y1="{TRACK_Y}" x2="{x0}" y2="{TRACK_Y}" stroke="url(#track-grad)" stroke-width="2" stroke-linecap="round">
    <animate attributeName="x2" keyTimes="0;0.85;0.97;1" values="{x0};{x1};{x1};{x0}" dur="{LOOP}s" repeatCount="indefinite"/>
  </line>

  <!-- Checkpoints -->
{nodes_str}

  <!-- Probe travelling along the log -->
  <g>
    <animateMotion path="M{x0},{TRACK_Y} L{x1},{TRACK_Y}" keyPoints="0;1;1" keyTimes="0;0.85;1" calcMode="linear" dur="{LOOP}s" repeatCount="indefinite"/>
    <circle r="8" fill="{cyan}" opacity="0.5" filter="url(#ship-glow)"/>
    <circle r="3" fill="#ffffff"/>
  </g>
</svg>'''
