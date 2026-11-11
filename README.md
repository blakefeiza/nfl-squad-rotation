# Squad rotation

One row per player, one glyph per game: who started, who came off the bench, who sat, and who was hurt. All 32 teams, 2026 season; pick a team from the menu (the URL hash keeps the choice, e.g. `#GB`).

- `prep.py` (all 32 teams, or name some: `python3 prep.py CHI GB`) downloads nflverse snap counts, injury reports, weekly rosters, ESPN depth-chart snapshots and the schedule, classifies every player-game, and writes `data/<TEAM>.json` plus `data/teams.json`. Raw downloads go to `raw/` (gitignored, ~85 MB).
- `index.html`, `style.css`, `app.js` are a static page that loads the picked team's JSON (hover details, click a player or a game, filter by status, offense / defense / special-teams views).
- `refresh.sh` re-runs the prep after each game day.

**How each state is decided**
- *Started:* the first player listed at a depth-chart slot just before kickoff who actually played (so a replacement for an injured starter counts).
- *Off the bench:* offense or defense snaps, not a starter. *On the bench:* on the roster and healthy, no snaps. *Hurt:* out or doubtful on the injury report, on injured reserve, or inactive with an injury designation.
- Pie fill is the player's share of the team's snaps in that game.
