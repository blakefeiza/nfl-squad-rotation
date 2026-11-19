#!/usr/bin/env python3
"""NFL squad rotation: one row per player, one column per game, one glyph per player-game.
Downloads nflverse data (snap counts, injury reports, weekly rosters, ESPN depth chart snapshots, schedule), classifies every
player-game as started / off the bench / on the bench / injured / not on the roster, and writes data/<TEAM>.json plus data/teams.json for the web page.
Also computes yards per play with each player on the field (run and pass plays, sacks included) when nflverse has published the play-by-play
participation file for the season (it appears after a season ends); without it the page simply leaves that column out.
Usage:  python3 prep.py [--cached] [--season=2026] [TEAM ...]      (default: all 32 teams; output goes to data/<season>/)"""
import json, sys, urllib.error, urllib.request
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SEASON = next((int(a.split("=")[1]) for a in sys.argv[1:] if a.startswith("--season=")), 2026)
BASE = "https://github.com/nflverse/nflverse-data/releases/download"
SRC = {
    "snaps": f"{BASE}/snap_counts/snap_counts_{SEASON}.csv",
    "inj": f"{BASE}/injuries/injuries_{SEASON}.csv",
    "roster": f"{BASE}/weekly_rosters/roster_weekly_{SEASON}.csv",
    "depth": f"{BASE}/depth_charts/depth_charts_{SEASON}.csv",
    "games": "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv",
}
NAMES = {"ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens", "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
         "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys", "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
         "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars", "KC": "Kansas City Chiefs", "LA": "Los Angeles Rams", "LAC": "Los Angeles Chargers",
         "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings", "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
         "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers", "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
         "TEN": "Tennessee Titans", "WAS": "Washington Commanders"}
# glyph colors per team: "start" fills the pies of starters, "sub" the pies of players who came off the bench. Each pair is picked to contrast with each other and with the cream page.
PALETTE = {"ARI": ("#97233f", "#e0a526"), "ATL": ("#a71930", "#9aa4ab"), "BAL": ("#3d2a8c", "#b08d1c"), "BUF": ("#00338d", "#d03a4d"), "CAR": ("#0085ca", "#3b4048"),
           "CHI": ("#e0561a", "#1e3a6e"), "CIN": ("#fb4f14", "#2a2a2a"), "CLE": ("#6b3f1d", "#ff5a1f"), "DAL": ("#1f5aa6", "#8a97a3"), "DEN": ("#fb4f14", "#1b3a63"),
           "DET": ("#0076b6", "#8a9199"), "GB": ("#2f7d46", "#e0a312"), "HOU": ("#a71930", "#1c3a52"), "IND": ("#2a62c4", "#7b8794"), "JAX": ("#00778b", "#b58a10"),
           "KC": ("#e31837", "#e8a317"), "LA": ("#1b4ba0", "#e0a60a"), "LAC": ("#0080c6", "#d49b00"), "LV": ("#2b2f33", "#8a9199"), "MIA": ("#008e97", "#f0742a"),
           "MIN": ("#4f2683", "#e0a60a"), "NE": ("#1c3f77", "#c8102e"), "NO": ("#b8902d", "#2b2b2b"), "NYG": ("#1a3f9a", "#a71930"), "NYJ": ("#125740", "#9aa5ad"),
           "PHI": ("#004c54", "#8a9199"), "PIT": ("#2a2a2a", "#e0a60a"), "SEA": ("#4c9a1a", "#1b3a63"), "SF": ("#aa0000", "#b3995d"), "TB": ("#d50a0a", "#3b3b3b"),
           "TEN": ("#3d86d0", "#c8102e"), "WAS": ("#5a1414", "#e09a00")}
RAW = HERE / next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith("--raw=")), "raw")        # where the downloads go (a separate folder lets you build another season)
OUT = HERE / next((x.split("=", 1)[1] for x in sys.argv[1:] if x.startswith("--out=")), f"data/{SEASON}")
RAW.mkdir(exist_ok=True)
for k, url in SRC.items():
    dst = RAW / f"{k}.csv"
    if "--cached" in sys.argv and dst.exists(): continue      # reuse the files already downloaded
    print("download", k, "...", end=" ", flush=True)
    urllib.request.urlretrieve(url, dst)
    print(f"{dst.stat().st_size / 1e6:.1f} MB")

# on-field data (who was on the field for each play) only exists once nflverse has published the participation file
PART, PBP = RAW / "part.csv", RAW / "pbp.csv"
if not ("--cached" in sys.argv and PART.exists() and PBP.exists()):
    try:
        print("download on-field data ...", end=" ", flush=True)
        urllib.request.urlretrieve(f"{BASE}/pbp_participation/pbp_participation_{SEASON}.csv", PART)
        urllib.request.urlretrieve(f"{BASE}/pbp/play_by_play_{SEASON}.csv", PBP)
        print("ok")
    except urllib.error.HTTPError:
        print(f"not published for {SEASON} yet")
        PART.unlink(missing_ok=True)

snaps_all = pd.read_csv(RAW / "snaps.csv")
inj_all = pd.read_csv(RAW / "inj.csv")
ros_all = pd.read_csv(RAW / "roster.csv", low_memory=False)
depth_all = pd.read_csv(RAW / "depth.csv")
games = pd.read_csv(RAW / "games.csv")
GROUP = {"QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE", "T": "OL", "G": "OL", "C": "OL", "OL": "OL",
         "DE": "DL", "DT": "DL", "NT": "DL", "DL": "DL", "LB": "LB", "ILB": "LB", "OLB": "LB", "MLB": "LB",
         "CB": "DB", "S": "DB", "SS": "DB", "FS": "DB", "DB": "DB"}
UNIT = {"QB": "Offense", "RB": "Offense", "WR": "Offense", "TE": "Offense", "OL": "Offense", "DL": "Defense", "LB": "Defense", "DB": "Defense"}
ORDER = ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB"]
COLORS = json.load(open(HERE / "colors.json"))
# league-wide id lookups: nflverse snap counts use PFR ids, everything else GSIS ids (a player can sit on another roster file)
BRIDGE = ros_all.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id").set_index("pfr_id").gsis_id.to_dict()
import re
def norm(n):    # "Orlando Brown Jr." and "Orlando Brown" are the same player
    return re.sub(r"[^a-z]", "", re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", str(n).lower()))
_names = pd.concat([ros_all[["full_name", "gsis_id"]].rename(columns={"full_name": "n"}), depth_all[["player_name", "gsis_id"]].rename(columns={"player_name": "n"}),
                    inj_all[["full_name", "gsis_id"]].rename(columns={"full_name": "n"})]).dropna()
NAME2GSIS = {norm(n): g for n, g in zip(_names.n, _names.gsis_id)}
UNMAPPED = {}


def compute_ypp():
    """{team: {unit: {avg, plays, players: {id: [plays, yards per play]}}}} or None when the on-field data is missing."""
    if not (PART.exists() and PBP.exists()): return None
    p = pd.read_csv(PBP, low_memory=False, usecols=["game_id", "play_id", "season_type", "posteam", "defteam", "play_type", "yards_gained", "qb_kneel", "qb_spike"])
    p = p[(p.season_type == "REG") & p.play_type.isin(["run", "pass"]) & (p.qb_kneel != 1) & (p.qb_spike != 1) & p.yards_gained.notna()]
    m = p.merge(pd.read_csv(PART, usecols=["nflverse_game_id", "play_id", "offense_players", "defense_players"]), left_on=["game_id", "play_id"], right_on=["nflverse_game_id", "play_id"])
    res = {}
    for unit, tcol, pcol in (("Offense", "posteam", "offense_players"), ("Defense", "defteam", "defense_players")):
        tot = m.groupby(tcol).yards_gained.agg(["mean", "count"])
        ex = m[[tcol, "yards_gained", pcol]].dropna()
        ex = ex.assign(pid=ex[pcol].str.split(";")).explode("pid")
        g = ex.groupby([tcol, "pid"]).yards_gained.agg(["count", "mean"])
        for (tm, pid), r in g.iterrows():
            res.setdefault(tm, {}).setdefault(unit, dict(avg=round(float(tot.loc[tm, "mean"]), 3), plays=int(tot.loc[tm, "count"]), players={}))["players"][pid] = [int(r["count"]), round(float(r["mean"]), 2)]
    print(f"on-field yards per play: {len(m)} plays")
    return res


YPP = compute_ypp()


def build(TEAM):
    snaps = snaps_all[(snaps_all.team == TEAM) & (snaps_all.game_type == "REG")].copy()
    inj = inj_all[inj_all.team == TEAM]
    ros = ros_all[(ros_all.team == TEAM) & (ros_all.game_type == "REG")]
    depth = depth_all[depth_all.team == TEAM].copy()
    # ---- schedule: our regular-season games in order (the bye week has no column)
    g = games[(games.season == SEASON) & (games.game_type == "REG") & ((games.home_team == TEAM) | (games.away_team == TEAM))].sort_values("week")
    sched = []
    for r in g.itertuples():
        home = r.home_team == TEAM
        played = pd.notna(r.home_score)
        us, them = (r.home_score, r.away_score) if home else (r.away_score, r.home_score)
        ko = pd.Timestamp(f"{r.gameday} {r.gametime}").tz_localize("America/New_York").tz_convert("UTC") if pd.notna(r.gametime) else pd.Timestamp(r.gameday, tz="UTC") + pd.Timedelta(hours=17)
        sched.append(dict(week=int(r.week), date=r.gameday, home=home, opp=r.away_team if home else r.home_team, played=bool(played),
                          us=int(us) if played else None, them=int(them) if played else None,
                          result=("W" if us > them else "L" if us < them else "T") if played else "", kickoff=ko))
    wk_idx = {s["week"]: i for i, s in enumerate(sched)}

    # ---- identities: nflverse snap counts use PFR ids, everything else uses GSIS ids
    snaps["gsis"] = snaps.pfr_player_id.map(BRIDGE)
    snaps.loc[snaps.gsis.isna(), "gsis"] = snaps.player.map(lambda n: NAME2GSIS.get(norm(n)))
    snaps.loc[snaps.gsis.isna(), "gsis"] = "pfr:" + snaps.pfr_player_id.astype(str)      # last resort so nobody is dropped
    missing = snaps[snaps.gsis.isna()].player.unique()
    if len(missing): print("  WARNING no id for:", list(missing))


    # ---- depth chart before kickoff: for each game, the last snapshot before kickoff, as ordered lists per position slot
    slots_by_wk = {}
    depth["ts"] = pd.to_datetime(depth.dt, utc=True)
    for s in sched:
        if not s["played"]: continue
        snap = depth[depth.ts <= s["kickoff"]]
        if snap.empty: slots_by_wk[s["week"]] = {}; continue
        # use the latest snapshot that lists a full lineup (a few snapshots are cut off, e.g. only 4 offensive slots on one game morning)
        pick = snap[snap.ts == snap.ts.max()]
        for ts in sorted(snap.ts.unique(), reverse=True):
            cand = snap[snap.ts == ts]
            if cand[cand.pos_grp == "3WR 1TE"].pos_slot.nunique() >= 10 and cand[cand.pos_grp.str.startswith("Base")].pos_slot.nunique() >= 10:
                pick = cand; break
        snap = pick
        s["depth_asof"] = snap.ts.max().isoformat()
        snap = snap[snap.pos_grp.isin(["3WR 1TE", "Base 4-3 D", "Base 3-4 D"])].sort_values("pos_rank")
        slots_by_wk[s["week"]] = {k: list(dict.fromkeys(v.gsis_id.dropna())) for k, v in snap.groupby(["pos_grp", "pos_slot"])}

    # ---- roster status and injury report by player and week
    rstat = ros.groupby(["gsis_id", "week"]).status.first().to_dict()
    ri = inj.groupby(["gsis_id", "week"]).agg(rs=("report_status", "first"), pi=("report_primary_injury", "first"), pr=("practice_status", "first")).to_dict("index")
    info = ros.sort_values("week").drop_duplicates("gsis_id", keep="last").set_index("gsis_id")
    name_of = snaps.groupby("gsis").player.first().to_dict()

    # ---- who gets a row: anyone with an offense or defense snap, or who was hurt (out, doubtful or on injured reserve) during the games played
    played_weeks = [s["week"] for s in sched if s["played"]]
    snap_by = {(r.gsis, int(r.week)): r for r in snaps.itertuples()}
    # a slot's starter is the first player listed there who actually played (so a replacement for an injured starter counts as starting)
    starters = {}
    for wk, slots in slots_by_wk.items():
        taken = set(); filled = set()
        for pass_no in (0, 1):
            for key, order in sorted(slots.items()):
                if key in filled: continue
                cand = order[:1] if pass_no == 0 else order
                for gid in cand:
                    r = snap_by.get((gid, wk))
                    if r is not None and (r.offense_snaps + r.defense_snaps) > 0 and gid not in taken:
                        taken.add(gid); filled.add(key); break
        starters[wk] = taken
    pos_of = snaps.groupby("gsis").position.agg(lambda x: x.value_counts().index[0]).to_dict()
    cands = set(k[0] for k, r in snap_by.items() if (r.offense_snaps + r.defense_snaps) > 0)
    for (gid, wk), v in ri.items():
        if wk in played_weeks and v["rs"] in ("Out", "Doubtful"): cands.add(gid)
    for (gid, wk), st in rstat.items():
        if wk in played_weeks and st == "RES": cands.add(gid)

    players = []
    for gid in cands:
        row = info.loc[gid] if gid in info.index else None
        pos = pos_of.get(gid) or (row.position if row is not None else None)
        grp = GROUP.get(pos) or GROUP.get(row.depth_chart_position if row is not None else "")
        if grp is None:
            UNMAPPED[pos] = UNMAPPED.get(pos, 0) + 1
            continue
        unit = UNIT[grp]
        cells = []
        for s in sched:
            wk = s["week"]
            if not s["played"]: cells.append(None); continue
            sr = snap_by.get((gid, wk)); stat = rstat.get((gid, wk)); ij = ri.get((gid, wk))
            pct = 0.0; n = 0; st_n = 0
            if sr is not None:
                n = int(sr.offense_snaps if unit == "Offense" else sr.defense_snaps)
                pct = float(sr.offense_pct if unit == "Offense" else sr.defense_pct)
                st_n = int(sr.st_snaps)
            note = ""
            if ij and isinstance(ij["rs"], str): note = ij["rs"] + (f" ({ij['pi']})" if isinstance(ij["pi"], str) else "")
            if n > 0:
                state = "start" if gid in starters.get(wk, set()) else "sub"
            elif ij and ij["rs"] in ("Out", "Doubtful") or stat == "RES" or (stat == "INA" and ij and isinstance(ij["rs"], str)):
                state = "inj"
                if stat == "RES" and not note: note = "Injured reserve"
            elif stat in ("ACT", "INA"):
                state = "bench"
            else:
                state = "none"
            cells.append([state, round(pct, 3), n, st_n, note])
        played_cells = [c for c in cells if c]
        if not any(c[0] != "none" for c in played_cells): continue
        tot = sum(c[2] for c in played_cells)
        players.append(dict(id=gid, name=(row.full_name if row is not None else name_of.get(gid, "")), jersey=(int(row.jersey_number) if row is not None and pd.notna(row.jersey_number) else None),
                            pos=pos, group=grp, unit=unit, cells=cells, snaps=tot,
                            counts={k: sum(1 for c in played_cells if c[0] == k) for k in ("start", "sub", "bench", "inj", "none")}))

    # ---- special teams: everyone who took a special-teams snap (plus kickers, punters and long snappers), pie = share of the team's special-teams snaps
    st_possible = sum(int(d.st_snaps.max()) for _, d in snaps.groupby("week"))
    st_players = []
    for gid in set(k[0] for k, r in snap_by.items() if r.st_snaps > 0):
        row = info.loc[gid] if gid in info.index else None
        pos = pos_of.get(gid) or (row.position if row is not None else "")
        cells = []
        for s in sched:
            wk = s["week"]
            if not s["played"]: cells.append(None); continue
            sr = snap_by.get((gid, wk)); stat = rstat.get((gid, wk)); ij = ri.get((gid, wk))
            n = int(sr.st_snaps) if sr is not None else 0
            note = ""
            if ij and isinstance(ij["rs"], str): note = ij["rs"] + (f" ({ij['pi']})" if isinstance(ij["pi"], str) else "")
            if n > 0: state = "st"
            elif ij and ij["rs"] in ("Out", "Doubtful") or stat == "RES" or (stat == "INA" and ij and isinstance(ij["rs"], str)):
                state = "inj"
                if stat == "RES" and not note: note = "Injured reserve"
            elif stat in ("ACT", "INA"): state = "bench"
            else: state = "none"
            cells.append([state, round(float(sr.st_pct), 3) if sr is not None else 0.0, n, 0, note])
        played_cells = [c for c in cells if c]
        tot = sum(c[2] for c in played_cells)
        st_players.append(dict(id=gid, name=(row.full_name if row is not None else name_of.get(gid, "")), jersey=(int(row.jersey_number) if row is not None and pd.notna(row.jersey_number) else None),
                               pos=pos, group="Specialists" if pos in ("K", "P", "LS") else "Coverage and returns", unit="Special teams", cells=cells, snaps=tot,
                               share=round(tot / st_possible, 4) if st_possible else 0,
                               counts={k: sum(1 for c in played_cells if c[0] == k) for k in ("st", "bench", "inj", "none")}))
    st_players.sort(key=lambda p: (p["group"] != "Specialists", -p["snaps"], p["name"]))

    # team unit totals per game (the denominator for "share of the team's snaps")
    unit_snaps = {wk: dict(Offense=int(d.offense_snaps.max()), Defense=int(d.defense_snaps.max())) for wk, d in snaps.groupby("week")}
    possible = dict(Offense=sum(v["Offense"] for v in unit_snaps.values()), Defense=sum(v["Defense"] for v in unit_snaps.values()))
    for p in players:
        p["share"] = round(p["snaps"] / possible[p["unit"]], 4) if possible[p["unit"]] else 0
    players.sort(key=lambda p: (ORDER.index(p["group"]), -p["snaps"], p["name"]))

    yt = (YPP or {}).get(TEAM)
    if yt:
        for p in players:
            e = yt.get(p["unit"], {}).get("players", {}).get(p["id"]); p["ypp"] = e
    out = dict(team=TEAM, teamName=NAMES.get(TEAM, TEAM), color=PALETTE[TEAM][0], palette=dict(start=PALETTE[TEAM][0], sub=PALETTE[TEAM][1]), season=SEASON, asof=max((s["date"] for s in sched if s["played"]), default=""), weeks_played=len(played_weeks),
               sched=[{k: v for k, v in s.items() if k != "kickoff"} for s in sched], unit_snaps=unit_snaps, possible=possible, groups=ORDER, players=players, stPlayers=st_players, stGroups=["Specialists", "Coverage and returns"], hasYpp=bool(yt), yppTeam=({u: dict(avg=v["avg"], plays=v["plays"]) for u, v in yt.items()} if yt else None), minYppPlays=100)
    return out


teams = ARGS or sorted(NAMES)
OUT.mkdir(parents=True, exist_ok=True)
index = []
for tm in teams:
    out = build(tm)
    (OUT / f"{tm}.json").write_text(json.dumps(out, separators=(",", ":")))
    rec = [sum(1 for s in out["sched"] if s["result"] == r) for r in ("W", "L", "T")]
    index.append(dict(code=tm, name=out["teamName"], color=out["color"], sub=out["palette"]["sub"], w=rec[0], l=rec[1], t=rec[2], weeks=out["weeks_played"], asof=out["asof"]))
    print(f"{tm}: {len(out['players'])} players, {out['weeks_played']} games, {len(out['stPlayers'])} special-teams rows")
if not ARGS:
    index.sort(key=lambda x: x["name"])
    (OUT / "teams.json").write_text(json.dumps(dict(season=SEASON, teams=index), separators=(",", ":")))
    seasons = sorted((int(d.name) for d in (HERE / "data").iterdir() if d.is_dir() and d.name.isdigit() and (d / "teams.json").exists()), reverse=True)
    (HERE / "data" / "seasons.json").write_text(json.dumps(dict(seasons=seasons), separators=(",", ":")))
if UNMAPPED: print("positions without a unit (skipped):", UNMAPPED)
