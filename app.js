// Squad rotation: one row per player, one glyph per game. Reads window.ROTATION (written by prep.py).
(function () {
  'use strict';
  var D, S, N, W, P, ST = [], ALL = [], lastWeek = 0, TEAMS = null;
  var $ = function (id) { return document.getElementById(id); };
  var C = { start: '#e0561a', sub: '#2f6fbd', bench: '#9aa3b2', inj: '#c97b84', st: '#c9961a' };
  var LABEL = { start: 'Started', sub: 'Off the bench', bench: 'On the bench', inj: 'Hurt', none: 'Not on the roster', st: 'Played special teams' };
  var UNIT_WORD = { Offense: 'offense', Defense: 'defense', 'Special teams': 'special-teams' };
  var state = { view: 'Offense', spot: null, sel: null, game: null };     // sel = { id, idx }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function last(name) { var t = name.split(' ').filter(function (x) { return !/^(Jr\.?|Sr\.?|II|III|IV|V)$/.test(x); }); return t[t.length - 1]; }
  function pct(x) { return Math.round(x * 100) + '%'; }
  function nice(iso) { return new Date(iso + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }); }
  function darken(hex, t) { var n = parseInt(hex.slice(1), 16), m = function (v) { return Math.round(v * (1 - t)); }; return 'rgb(' + m(n >> 16) + ',' + m((n >> 8) & 255) + ',' + m(n & 255) + ')'; }

  // ---------- load a team ----------
  function use(d) {
    D = d; S = d.sched; N = S.length; W = d.weeks_played; P = d.players; ST = d.stPlayers || [];
    P.forEach(function (p, i) { p.idx = i; }); ST.forEach(function (p, i) { p.idx = P.length + i; });
    ALL = P.concat(ST); lastWeek = S.filter(function (g) { return g.played; }).slice(-1)[0].week;
    state.spot = null; state.sel = null; state.game = null;
    $('title').textContent = D.teamName;
    $('sub').innerHTML = 'Squad rotation - <span class="acc">through week ' + lastWeek + '</span>';
    document.documentElement.style.setProperty('--accent', darken(D.color || '#d4560f', 0.3));
    $('foot').innerHTML = 'Viz by <b>Blake Feiza</b>  \u00b7  Data: nflverse snap counts, injury reports, weekly rosters and ESPN depth charts, ' + D.season + ' NFL season (games played as of ' + nice(D.asof) + ')';
    document.title = D.teamName + ' squad rotation';
  }
  function loadTeam(code) {
    $('panel').innerHTML = '<div class="loading">Loading ' + esc(code) + '...</div>';
    return fetch('data/' + code + '.json').then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (d) {
      use(d); render(); try { localStorage.setItem('rotation-team', code); } catch (e) {} if (location.hash.slice(1) !== code) history.replaceState(null, '', '#' + code);
    }).catch(function () { $('panel').innerHTML = '<div class="loading">Could not load that team. Try again in a moment.</div>'; });
  }

  // ---------- glyphs ----------
  function pie(p, r, mirror) {       // a slice that grows clockwise from 12 o'clock, or counterclockwise when mirrored
    if (p >= 0.999) return '<circle cx="12" cy="12" r="' + r + '"/>';
    var a = p * 2 * Math.PI, x = 12 + (mirror ? -1 : 1) * r * Math.sin(a), y = 12 - r * Math.cos(a);
    return '<path d="M12 12L12 ' + (12 - r) + 'A' + r + ' ' + r + ' 0 ' + (p > 0.5 ? 1 : 0) + ' ' + (mirror ? 0 : 1) + ' ' + x.toFixed(2) + ' ' + y.toFixed(2) + 'Z"/>';
  }
  function glyph(c) {
    var s = '<svg viewBox="0 0 24 24" aria-hidden="true">';
    if (!c) return s + '<circle cx="12" cy="12" r="9" fill="none" stroke="#d6d3ca" stroke-dasharray="2 3"/></svg>';
    var k = c[0];
    if (k === 'none') return s + '<circle cx="12" cy="12" r="1.6" fill="#d6d3ca"/></svg>';
    if (k === 'start' || k === 'sub' || k === 'st') {
      var col = C[k];
      return s + '<circle cx="12" cy="12" r="9.6" fill="' + col + '" fill-opacity=".13" stroke="' + col + '" stroke-opacity="' + (k === 'start' ? 1 : 0.7) + '" stroke-width="' + (k === 'start' ? 2 : 1.3) + '"/><g fill="' + col + '">' + pie(Math.max(0.035, c[1]), 8, k === 'sub') + '</g></svg>';
    }
    if (k === 'bench') return s + '<circle cx="12" cy="12" r="9" fill="none" stroke="' + C.bench + '" stroke-width="1.4"/></svg>';
    return s + '<circle cx="12" cy="12" r="9.2" fill="' + C.inj + '" fill-opacity=".1" stroke="' + C.inj + '" stroke-width="1.3"/><path d="M12 7.8v8.4M7.8 12h8.4" stroke="' + C.inj + '" stroke-width="1.8" stroke-linecap="round"/></svg>';
  }

  // ---------- key (also filters) ----------
  function renderLegend() {
    var st = state.view === 'Special teams';
    var keys = st ? ['st', 'bench', 'inj'] : ['start', 'sub', 'bench', 'inj'];
    var name = st ? { st: 'Played', bench: 'Did not play', inj: 'Hurt' } : { start: 'Started', sub: 'Off the bench', bench: 'Bench', inj: 'Hurt' };
    var demo = { start: ['start', 0.7, 0, 0, ''], sub: ['sub', 0.45, 0, 0, ''], st: ['st', 0.7, 0, 0, ''], bench: ['bench', 0, 0, 0, ''], inj: ['inj', 0, 0, 0, ''] };
    $('legend').innerHTML = keys.map(function (k) { return '<button class="key" data-s="' + k + '" aria-pressed="' + (state.spot === k ? 'true' : 'false') + '">' + glyph(demo[k]) + name[k] + '</button>'; }).join('') +
      '<span class="note">Pie = share of snaps</span>';
  }

  // ---------- grid ----------
  function sorted(list) { return list.slice().sort(function (a, b) { return b.share - a.share || (b.counts.start || 0) - (a.counts.start || 0) || a.name.localeCompare(b.name); }); }
  function rowHTML(p) {
    var cells = '', dimRow = state.sel && state.sel.id !== p.id;
    for (var g = 0; g < N; g++) {
      var c = p.cells[g], dim = (state.spot && (!c || c[0] !== state.spot)) || (state.game !== null && state.game !== g);
      cells += '<div class="cell' + (dim ? ' dim' : '') + '" data-p="' + p.idx + '" data-g="' + g + '">' + glyph(c) + '</div>';
    }
    return '<div class="row' + (state.sel && state.sel.id === p.id ? ' sel' : '') + (dimRow ? ' dim' : '') + '"><div class="nm" data-n="' + p.idx + '"><span class="t">' + esc(p.name) + '</span><i>' + esc(p.pos) + '</i></div>' + cells + '<div class="shr">' + pct(p.share) + '</div></div>';
  }
  function headerHTML() {
    var h = '<div class="hdr"><div class="corner"></div>';
    S.forEach(function (g, i) {
      var cls = g.played ? (g.result === 'W' ? 'w' : g.result === 'L' ? 'l' : '') : 'future';
      var tip = 'Week ' + g.week + ': ' + (g.home ? 'vs ' : 'at ') + g.opp + (g.played ? ', ' + g.result + ' ' + g.us + '–' + g.them : ' (upcoming)');
      h += '<button class="gh ' + cls + '" data-g="' + i + '" title="' + tip + '" aria-pressed="' + (state.game === i ? 'true' : 'false') + '"><span class="opp">' + (g.home ? '' : '@') + g.opp + '</span><span class="res"></span><span class="wk">' + g.week + '</span></button>';
    });
    return h + '<div class="sh">snap<br>share</div></div>';
  }
  function renderPanel() {
    var isST = state.view === 'Special teams', list = isST ? ST : P.filter(function (p) { return p.unit === state.view; }), groups = isST ? D.stGroups : D.groups, body = '';
    groups.forEach(function (grp) {
      var rows = sorted(list.filter(function (p) { return p.group === grp; }));
      if (!rows.length) return;
      if (body) body += '<div class="grp-l"></div>';
      body += rows.map(rowHTML).join('');
    });
    $('panel').innerHTML = '<div class="inner" style="--n:' + N + '">' + headerHTML() + body + '</div>';
  }

  // ---------- selection bar (only shown when something is selected) ----------
  function playerLine(p) {
    var c = p.counts, tag = '<b>' + esc(p.name) + '</b> <span class="muted">' + esc(p.pos) + (p.jersey ? ' #' + p.jersey : '') + '</span> · ';
    if (p.unit === 'Special teams') return tag + 'played special teams in ' + c.st + ' of ' + W + ' games · ' + pct(p.share) + ' of the team’s special-teams snaps';
    var weeks = []; p.cells.forEach(function (x, i) { if (x && x[0] === 'inj') weeks.push(S[i].week); });
    return tag + c.start + ' start' + (c.start === 1 ? '' : 's') + ', ' + c.sub + ' off the bench, ' + c.bench + ' on the bench, ' + c.inj + ' hurt · ' + pct(p.share) + ' of ' + UNIT_WORD[p.unit] + ' snaps' +
      (weeks.length && weeks.length < W ? ' <span class="muted">(hurt in week' + (weeks.length > 1 ? 's' : '') + ' ' + weeks.join(', ') + ')</span>' : '');
  }
  function gameLine(i) {
    var g = S[i], pool = state.view === 'Special teams' ? ST : P.filter(function (p) { return p.unit === state.view; });
    if (!g.played) return '<b>Week ' + g.week + '</b> · ' + (g.home ? 'vs ' : 'at ') + g.opp + ' <span class="muted">not played yet</span>';
    var out = pool.filter(function (p) { return p.cells[i] && p.cells[i][0] === 'inj' && p.snaps > 0; }), sub = pool.filter(function (p) { return p.cells[i] && p.cells[i][0] === 'sub'; }).length;
    return '<b>Week ' + g.week + '</b> · ' + (g.home ? 'vs ' : 'at ') + g.opp + ' · ' + g.result + ' ' + g.us + '–' + g.them +
      (state.view === 'Special teams' ? '' : ' · ' + sub + ' came off the bench') +
      (out.length ? ' · hurt: <span class="muted">' + esc(out.slice(0, 7).map(function (p) { return last(p.name); }).join(', ') + (out.length > 7 ? ' and ' + (out.length - 7) + ' more' : '')) + '</span>' : '');
  }
  function renderDetail() {
    var d = $('detail'), html = '';
    if (state.sel) html = playerLine(ALL[state.sel.idx]); else if (state.game !== null) html = gameLine(state.game);
    d.hidden = !html; d.innerHTML = html ? '<button class="x" id="clear">Clear</button>' + html : '';
  }
  function render() { if (!D) return; renderLegend(); renderPanel(); renderDetail(); }

  // ---------- tooltip ----------
  var tip = $('tip'), hl = document.createElement('style'); document.head.appendChild(hl);
  function tipHTML(p, g) {
    var c = p.cells[g], s = S[g], h = '<div class="n">' + esc(p.name) + '</div><div class="m">' + esc(p.pos) + (p.jersey ? ' · #' + p.jersey : '') + '</div>' +
      '<div class="m">Week ' + s.week + ' · ' + (s.home ? 'vs ' : 'at ') + s.opp + (s.played ? ' (' + s.result + ' ' + s.us + '–' + s.them + ')' : '') + '</div>';
    if (!c) return h + '<div class="d" style="margin-top:6px">Not played yet</div>';
    var k = c[0], d = [];
    h += '<div class="s"><i style="background:' + (C[k] || '#d6d3ca') + '"></i>' + LABEL[k] + '</div>';
    if (k === 'start' || k === 'sub' || k === 'st') d.push(c[2] + ' ' + UNIT_WORD[p.unit] + ' snaps (' + pct(c[1]) + ' of the team’s)');
    if (k === 'bench') d.push(p.unit === 'Special teams' ? 'Healthy, no special-teams snaps' : 'Healthy, took no snaps');
    if (k === 'none') d.push('Not on the active roster that week');
    if (c[4]) d.push((k === 'inj' ? '' : 'Injury report: ') + c[4]); else if (k === 'inj') d.push('Out');
    return h + '<div class="d">' + d.map(esc).join('<br>') + '</div>';
  }
  function placeTip(x, y) {
    var w = tip.offsetWidth, h = tip.offsetHeight, tx = x + 16, ty = y + 16;
    if (tx + w > innerWidth - 8) tx = x - w - 16; if (ty + h > innerHeight - 8) ty = y - h - 16;
    tip.style.transform = 'translate(' + Math.max(8, tx) + 'px,' + Math.max(8, ty) + 'px)';
  }
  var panel = $('panel');
  panel.addEventListener('mouseover', function (e) {
    var cell = e.target.closest('.cell'); if (!cell) return;
    var g = +cell.dataset.g; tip.innerHTML = tipHTML(ALL[+cell.dataset.p], g); tip.classList.add('on'); placeTip(e.clientX, e.clientY);
    hl.textContent = '.cell[data-g="' + g + '"]{background:rgba(18,21,28,.035)}';
  });
  panel.addEventListener('mousemove', function (e) { if (tip.classList.contains('on')) placeTip(e.clientX, e.clientY); });
  panel.addEventListener('mouseout', function (e) { if (!e.relatedTarget || !e.relatedTarget.closest || !e.relatedTarget.closest('.cell')) { tip.classList.remove('on'); hl.textContent = ''; } });

  // ---------- clicks ----------
  document.addEventListener('click', function (e) {
    var t = e.target, cell = t.closest('.cell'), nm = t.closest('.nm'), gh = t.closest('.gh'), key = t.closest('.key');
    if (cell && matchMedia('(hover: none)').matches) { var r = cell.getBoundingClientRect(); tip.innerHTML = tipHTML(ALL[+cell.dataset.p], +cell.dataset.g); tip.classList.add('on'); placeTip(r.left, r.bottom); return; }
    tip.classList.remove('on');
    if (nm) { var p = ALL[+nm.dataset.n]; state.sel = state.sel && state.sel.id === p.id ? null : { id: p.id, idx: p.idx }; state.game = null; state.spot = null; render(); return; }
    if (gh) { var g = +gh.dataset.g; state.game = state.game === g ? null : g; state.sel = null; state.spot = null; render(); return; }
    if (key) { var s = key.dataset.s; state.spot = state.spot === s ? null : s; state.sel = null; state.game = null; render(); return; }
    if (t.id === 'clear') { state.sel = null; state.game = null; state.spot = null; render(); }
  });
  $('tabs').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    state.view = b.dataset.v; state.spot = null; state.sel = null; state.game = null;
    [].forEach.call($('tabs').children, function (x) { x.setAttribute('aria-selected', x === b ? 'true' : 'false'); });
    render();
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { state.sel = null; state.game = null; state.spot = null; tip.classList.remove('on'); render(); } });

  $('team').addEventListener('change', function () { loadTeam(this.value); });
  addEventListener('hashchange', function () { var c = location.hash.slice(1).toUpperCase(); if (TEAMS && c && c !== $('team').value && TEAMS.some(function (t) { return t.code === c; })) { $('team').value = c; loadTeam(c); } });
  fetch('data/teams.json').then(function (r) { return r.json(); }).then(function (idx) {
    TEAMS = idx.teams;
    $('team').innerHTML = TEAMS.map(function (t) { return '<option value="' + t.code + '">' + esc(t.name) + '</option>'; }).join('');
    var want = location.hash.slice(1).toUpperCase(), saved = ''; try { saved = localStorage.getItem('rotation-team') || ''; } catch (e) {}
    var pick = [want, saved, 'CHI'].filter(function (c) { return TEAMS.some(function (t) { return t.code === c; }); })[0] || TEAMS[0].code;
    $('team').value = pick; return loadTeam(pick);
  }).catch(function () { $('panel').innerHTML = '<div class="loading">Could not load the data.</div>'; });
  window.__rotation = { state: state, render: render, get D() { return D; } };
})();
