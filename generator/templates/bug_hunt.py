"""SVG template: Bug Hunt mini-game (850x220). Pure SMIL, loops forever."""

from generator.utils import esc, deterministic_random

WIDTH, HEIGHT = 850, 220
SHIP_Y = 180
BUG_Y = 96
FIRST_HIT = 1.8
HIT_GAP = 2.4
DEFAULT_BUGS = ["NullPointer", "undefined", "CORS", "404", "Merge Conflict"]


def _discrete(attr, steps, loop):
    """Step animation: steps is a list of (time_seconds, value), first time 0."""
    kts = ";".join(f"{min(t, loop) / loop:.4f}" for t, _ in steps)
    vals = ";".join(str(v) for _, v in steps)
    return (
        f'<animate attributeName="{attr}" calcMode="discrete" keyTimes="{kts}" '
        f'values="{vals}" dur="{loop:.2f}s" repeatCount="indefinite"/>'
    )


def _kill_order(n):
    """Zig-zag order (left, right, left, ...) so the ship sweeps the screen."""
    lo, hi, order, left = 0, n - 1, [], True
    while lo <= hi:
        if left:
            order.append(lo)
            lo += 1
        else:
            order.append(hi)
            hi -= 1
        left = not left
    return order


def _bug(x, label, color, theme, k, kill, respawn, loop):
    legs = "M-10 4 L-20 10 M-12 -1 L-23 -3 M-9 -6 L-18 -12 M10 4 L20 10 M12 -1 L23 -3 M9 -6 L18 -12 M-4 -9 L-8 -17 M4 -9 L8 -17"
    return f'''  <g transform="translate({x:.1f} {BUG_Y})">
    {_discrete("opacity", [(0, 1), (kill, 0), (respawn, 1)], loop)}
    <g>
      <animateTransform attributeName="transform" type="translate" values="0 0;0 7;0 0" dur="1.8s" begin="-{k * 0.45:.2f}s" repeatCount="indefinite"/>
      <path d="{legs}" stroke="{color}" stroke-width="1.8" stroke-linecap="round" fill="none" opacity="0.85"/>
      <ellipse rx="13" ry="10" fill="{color}" opacity="0.92"/>
      <circle cx="-5" cy="-3" r="2.8" fill="{theme['void']}"/>
      <circle cx="5" cy="-3" r="2.8" fill="{theme['void']}"/>
      <circle cx="-4.4" cy="-3.4" r="1" fill="#ffffff"/>
      <circle cx="5.6" cy="-3.4" r="1" fill="#ffffff"/>
      <text y="32" fill="{theme['text_dim']}" font-size="10" font-family="monospace" text-anchor="middle">{esc(label)}</text>
    </g>
  </g>'''


def render(bugs: list, theme: dict) -> str:
    """Render the Bug Hunt mini-game: a ship sweeps the screen squashing bugs.

    Args:
        bugs: list of bug labels (3 to 6 are used)
        theme: color palette dict
    """
    bugs = [str(b) for b in (bugs or DEFAULT_BUGS)][:6]
    if len(bugs) < 3:
        bugs = DEFAULT_BUGS
    n = len(bugs)
    cyan = theme.get("synapse_cyan", "#00d4ff")
    amber = theme.get("axon_amber", "#ffb020")
    violet = theme.get("dendrite_violet", "#a78bfa")

    margin = 110
    step = (WIDTH - 2 * margin) / (n - 1)
    xs = [margin + i * step for i in range(n)]
    order = _kill_order(n)
    arrive = {idx: FIRST_HIT + k * HIT_GAP for k, idx in enumerate(order)}
    kill = {idx: t + 0.35 for idx, t in arrive.items()}
    last_arrive = FIRST_HIT + (n - 1) * HIT_GAP
    clear_at = last_arrive + 0.35
    respawn = clear_at + 3.0
    loop = respawn + 1.0
    cx = WIDTH / 2

    # Ship path
    pts = [(0.0, cx)]
    prev_x, prev_free = cx, 0.0
    for k, idx in enumerate(order):
        a = FIRST_HIT + k * HIT_GAP
        dep = max(prev_free, a - 1.5)
        if dep > pts[-1][0]:
            pts.append((dep, prev_x))
        pts.append((a, xs[idx]))
        prev_x, prev_free = xs[idx], a + 0.6
        pts.append((prev_free, prev_x))
    ret_start = prev_free + 0.4
    pts.append((ret_start, prev_x))
    pts.append((ret_start + 1.4, cx))
    pts.append((loop, cx))
    ship_kt = ";".join(f"{t / loop:.4f}" for t, _ in pts)
    ship_vals = ";".join(f"{x:.1f} {SHIP_Y}" for _, x in pts)
    ship_splines = ";".join(["0.45 0 0.2 1"] * (len(pts) - 1))

    # Star field
    sx = deterministic_random("hunt-x", 30, 12, WIDTH - 12)
    sy = deterministic_random("hunt-y", 30, 50, HEIGHT - 12)
    sr = deterministic_random("hunt-r", 30, 0.3, 1.1)
    so = deterministic_random("hunt-o", 30, 0.08, 0.35)
    sd = deterministic_random("hunt-d", 30, 3.0, 7.0)
    stars = "\n".join(
        f'  <circle cx="{sx[i]:.1f}" cy="{sy[i]:.1f}" r="{sr[i]:.1f}" fill="{theme["text_dim"]}" opacity="{so[i]:.2f}">'
        f'<animate attributeName="opacity" values="{so[i]:.2f};{min(so[i] * 3, 0.8):.2f};{so[i]:.2f}" '
        f'dur="{sd[i]:.1f}s" repeatCount="indefinite"/></circle>'
        for i in range(30)
    )

    bugs_svg = "\n".join(
        _bug(xs[i], bugs[i], amber, theme, i, kill[i], respawn, loop) for i in range(n)
    )

    lasers, bursts = [], []
    for i in range(n):
        a = arrive[i]
        lasers.append(
            f'  <line x1="{xs[i]:.1f}" y1="{SHIP_Y - 18}" x2="{xs[i]:.1f}" y2="{BUG_Y + 14}" '
            f'stroke="{cyan}" stroke-width="3" stroke-linecap="round" opacity="0">'
            f'{_discrete("opacity", [(0, 0), (a + 0.1, 1), (a + 0.35, 0)], loop)}</line>'
        )
        e0, e1 = kill[i], kill[i] + 0.55
        kts = f"0;{e0 / loop:.4f};{e1 / loop:.4f};1"
        bursts.append(
            f'  <circle cx="{xs[i]:.1f}" cy="{BUG_Y}" r="0" fill="{amber}" opacity="0">'
            f'<animate attributeName="r" keyTimes="{kts}" values="0;0;30;30" dur="{loop:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" keyTimes="{kts}" values="0;0.9;0;0" dur="{loop:.2f}s" repeatCount="indefinite"/></circle>\n'
            f'  <circle cx="{xs[i]:.1f}" cy="{BUG_Y}" r="0" fill="none" stroke="{violet}" stroke-width="2" opacity="0">'
            f'<animate attributeName="r" keyTimes="{kts}" values="0;0;42;42" dur="{loop:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" keyTimes="{kts}" values="0;0.8;0;0" dur="{loop:.2f}s" repeatCount="indefinite"/></circle>'
        )

    # Score HUD: one text per count, shown in turn
    kill_times = [kill[idx] for idx in order]
    counters = []
    for c in range(n + 1):
        if c == 0:
            steps = [(0, 1), (kill_times[0], 0), (respawn, 1)]
        else:
            end = kill_times[c] if c < n else respawn
            steps = [(0, 0), (kill_times[c - 1], 1), (end, 0)]
        counters.append(
            f'  <text x="{WIDTH - 30}" y="38" fill="{theme["text_faint"]}" font-size="10" font-family="monospace" '
            f'letter-spacing="1" text-anchor="end" opacity="0">SQUASHED {c}/{n}'
            f'{_discrete("opacity", steps, loop)}</text>'
        )
    counters_str = "\n".join(counters)

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
    <filter id="hunt-glow" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="4"/>
    </filter>
  </defs>

  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" ry="12"
        fill="{theme['nebula']}" stroke="{theme['star_dust']}" stroke-width="1"/>
{brackets}
{stars}

  <text x="30" y="38" fill="{theme['text_faint']}" font-size="11" font-family="monospace" letter-spacing="3">BUG HUNT</text>
{counters_str}

  <line x1="12" y1="206" x2="{WIDTH - 12}" y2="206" stroke="{theme['text_faint']}" stroke-width="0.5" stroke-dasharray="4,8" opacity="0.25"/>

  <!-- Bugs -->
{bugs_svg}

  <!-- Lasers and explosions -->
{chr(10).join(lasers)}
{chr(10).join(bursts)}

  <text x="{cx}" y="{BUG_Y + 6}" fill="{cyan}" font-size="22" font-family="monospace" letter-spacing="8"
        text-anchor="middle" opacity="0">ALL CLEAR
    {_discrete("opacity", [(0, 0), (clear_at + 0.2, 1), (respawn, 0)], loop)}
  </text>

  <!-- Ship -->
  <g transform="translate({cx:.1f} {SHIP_Y})">
    <animateTransform attributeName="transform" type="translate" calcMode="spline"
      keyTimes="{ship_kt}" values="{ship_vals}" keySplines="{ship_splines}"
      dur="{loop:.2f}s" repeatCount="indefinite"/>
    <polygon points="-4,8 0,19 4,8" fill="{amber}" opacity="0.9">
      <animate attributeName="opacity" values="0.9;0.35;0.9" dur="0.25s" repeatCount="indefinite"/>
    </polygon>
    <polygon points="0,-16 13,10 0,5 -13,10" fill="{cyan}" opacity="0.2" filter="url(#hunt-glow)"/>
    <polygon points="0,-16 13,10 0,5 -13,10" fill="{cyan}" opacity="0.95"/>
    <circle cx="0" cy="-2" r="2.4" fill="#ffffff"/>
  </g>
</svg>'''
