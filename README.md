# Squad rotation

One row per player, one glyph per game: who started, who came off the bench, who sat, and who was hurt. All 32 teams, 2026 season; pick a team from the menu (the URL hash keeps the choice, e.g. `#GB`).

- `prep.py` (all 32 teams, or name some: `python3 prep.py CHI GB`) downloads nflverse snap counts, injury reports, weekly rosters, ESPN depth-chart snapshots and the schedule, classifies every player-game, and writes `data/<TEAM>.json` plus `data/teams.json`. Raw downloads go to `raw/` (gitignored, ~85 MB).
- `index.html`, `style.css`, `app.js` are a static page that loads the picked team's JSON (hover details, click a player or a game, filter by status, offense / defense / special-teams views).
- `refresh.sh` re-runs the prep for the current season after each game day. Data lives in `data/<season>/` (2026 and 2025), and `data/seasons.json` lists them.
- **Yards per play with a player on the field** (the dot + histogram column, offense and defense only) needs nflverse's play-by-play participation file, which is published after a season ends. 2025 has it; 2026 will pick it up automatically the next time `prep.py` runs after nflverse posts it (until then the column is left out and the page says so). Plays counted: run and pass plays, sacks included; kneels, spikes, penalties and special teams excluded. A dot needs 100 plays on the field.

**How each state is decided**
- *Started:* the first player listed at a depth-chart slot just before kickoff who actually played (so a replacement for an injured starter counts).
- *Off the bench:* offense or defense snaps, not a starter. *On the bench:* on the roster and healthy, no snaps. *Hurt:* out or doubtful on the injury report, on injured reserve, or inactive with an injury designation.
- Pie fill is the player's share of the team's snaps in that game.
