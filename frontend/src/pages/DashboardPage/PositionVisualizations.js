import React, {useEffect, useState} from 'react';
import {dashboardRequest} from './api';
import teamLogos from './teamLogos';
import './positionVisualizations.css';

const defaults = {season: '2024', season_type: 'REG', min_dropbacks: '50', week_start: '1', week_end: '22', downs: 'all', quarters: 'all'};
const format = (value, unit) => {
    if (value == null) return '—';
    const digits = unit === 'epa' ? 2 : 1;
    return `${['epa', 'points'].includes(unit) && value > 0 ? '+' : ''}${value.toFixed(digits)}${unit === 'percent' ? '%' : unit === 'points' ? ' pp' : ''}`;
};
const shading = metric => {
    if (!metric.rank || metric.rankedPlayers < 2) return '#f8f9f7';
    const percentile = (metric.rank - 1) / (metric.rankedPlayers - 1);
    return percentile <= .5 ? `hsl(128 35% ${77 + percentile * 42}%)` : `hsl(263 48% ${98 - (percentile - .5) * 30}%)`;
};

export default function PositionVisualizations() {
    const [draft, setDraft] = useState(defaults);
    const [filters, setFilters] = useState(defaults);
    const [data, setData] = useState(null);
    const [error, setError] = useState('');
    const [filterError, setFilterError] = useState('');
    const [retry, setRetry] = useState(0);
    const [team, setTeam] = useState('all');
    const [search, setSearch] = useState('');
    const [sort, setSort] = useState({key: 'epa_per_play', ascending: false});
    useEffect(() => {
        const controller = new AbortController();
        setData(null); setError('');
        dashboardRequest(`/api/position-visualizations?${new URLSearchParams({...filters, position: 'QB'})}`, {signal: controller.signal})
            .then(value => {if (!controller.signal.aborted) setData(value);})
            .catch(failure => {if (!controller.signal.aborted) setError(failure.message);});
        return () => controller.abort();
    }, [filters, retry]);
    const change = (key, value) => setDraft(previous => ({...previous, [key]: value}));
    const apply = event => {
        event.preventDefault();
        if (Number(draft.week_start) > Number(draft.week_end)) {setFilterError('First week must be before or equal to last week.'); return;}
        setFilterError(''); setFilters({...draft});
    };
    const teams = data ? [...new Set(data.players.flatMap(player => player.teams))].sort() : [];
    const rows = (data?.players || []).filter(player => (team === 'all' || player.teams.includes(team)) && player.name.toLowerCase().includes(search.trim().toLowerCase()));
    rows.sort((a, b) => {
        if (sort.key === 'name') return (sort.ascending ? 1 : -1) * a.name.localeCompare(b.name);
        const av = sort.key === 'dropbacks' ? a.dropbacks : a.metrics[sort.key].value;
        const bv = sort.key === 'dropbacks' ? b.dropbacks : b.metrics[sort.key].value;
        if (av == null || bv == null) return av == null ? (bv == null ? a.name.localeCompare(b.name) : 1) : -1;
        return (sort.ascending ? av - bv : bv - av) || a.name.localeCompare(b.name);
    });
    const sortColumn = (key, ascending) => setSort(previous => ({key, ascending: previous.key === key ? !previous.ascending : ascending}));
    const sorted = key => sort.key === key ? (sort.ascending ? 'ascending' : 'descending') : 'none';
    const arrow = key => sort.key === key ? (sort.ascending ? ' ↑' : ' ↓') : '';
    return <section className="oc-panel oc-position" aria-label="Position-level visualizations">
        <header className="oc-position-heading"><span className="oc-tiny-badge">POSITION SCOUTING · QB</span><h2>NFL Quarterback Leaderboard</h2><p>Dropback efficiency, passing accuracy, and pocket tendencies.</p></header>
        <form className="oc-position-filters" onSubmit={apply}>
            <label>Season<select value={draft.season} onChange={e => change('season', e.target.value)}>{[2024, 2023, 2022, 2021, 2020].map(year => <option key={year}>{year}</option>)}</select></label>
            <label>Season phase<select value={draft.season_type} onChange={e => change('season_type', e.target.value)}><option value="REG">Regular season</option><option value="POST">Postseason</option><option value="all">Regular + postseason</option></select></label>
            <label>Minimum dropbacks<input required type="number" min="1" max="10000" value={draft.min_dropbacks} onChange={e => change('min_dropbacks', e.target.value)}/></label>
            <label>First week<input required type="number" min="1" max="22" value={draft.week_start} onChange={e => change('week_start', e.target.value)}/></label>
            <label>Last week<input required type="number" min="1" max="22" value={draft.week_end} onChange={e => change('week_end', e.target.value)}/></label>
            <label>Down<select value={draft.downs} onChange={e => change('downs', e.target.value)}><option value="all">All downs</option>{[1, 2, 3, 4].map(d => <option key={d} value={d}>Down {d}</option>)}</select></label>
            <label>Quarter<select value={draft.quarters} onChange={e => change('quarters', e.target.value)}><option value="all">All quarters</option>{[1, 2, 3, 4].map(q => <option key={q} value={q}>Q{q}</option>)}<option value="5">Overtime</option></select></label>
            <button type="submit" className="oc-primary">Apply filters</button>
        </form>
        {filterError && <p role="alert" className="oc-error">{filterError}</p>}
        {error ? <div role="alert" className="oc-error">{error}<button className="oc-secondary" onClick={() => setRetry(n => n + 1)}>Retry</button></div> : !data ? <p role="status" className="oc-position-loading">Loading quarterback leaderboard…</p> : <>
            <p className="oc-position-context">{data.filters.season} · {data.filters.season_type === 'REG' ? 'Regular season' : data.filters.season_type === 'POST' ? 'Postseason' : 'Regular + postseason'} · Weeks {data.filters.week_start}–{data.filters.week_end} · Down {data.filters.downs?.join(', ') || 'all'} · Quarter {data.filters.quarters?.map(q => q === 5 ? 'OT' : q).join(', ') || 'all'} · Qualified passers: minimum {data.filters.min_dropbacks} dropbacks</p>
            <div className="oc-position-tools"><label>Search player<input type="search" placeholder="Player name" value={search} onChange={e => setSearch(e.target.value)}/></label><label>Team<select value={team} onChange={e => setTeam(e.target.value)}><option value="all">All teams</option>{[...new Set([...teams, ...(team === 'all' ? [] : [team])])].sort().map(t => <option key={t}>{t}</option>)}</select></label><p role="status">{rows.length} of {data.qualifiedPlayers} qualified quarterbacks</p><div className="oc-position-legend"><span>Higher rank</span><i/><span>Lower rank</span></div></div>
            {rows.length ? <div className="oc-position-table-wrap" tabIndex="0" role="region" aria-label="Scrollable quarterback statistics"><table className="oc-position-table">
                <caption>Rank among qualified quarterbacks appears in parentheses. Select a column heading to sort.</caption>
                <thead><tr><th scope="col" aria-sort={sorted('name')}><button onClick={() => sortColumn('name', true)}>Player{arrow('name')}</button></th><th scope="col">Team</th><th scope="col" aria-sort={sorted('dropbacks')}><button onClick={() => sortColumn('dropbacks', false)}>Dropbacks{arrow('dropbacks')}</button></th>{data.metricDefinitions.map(definition => <th key={definition.key} scope="col" aria-sort={sorted(definition.key)}><button onClick={() => sortColumn(definition.key, definition.lowerBetter)}>{definition.label}{arrow(definition.key)}</button></th>)}</tr></thead>
                <tbody>{rows.map(player => <tr key={player.id}><th scope="row">{player.name}</th><td><div className="oc-position-teams">{player.teams.map(t => <span key={t} title={t}>{teamLogos[t] ? <img src={teamLogos[t]} alt={t}/> : t}</span>)}</div></td><td className="oc-position-sample">{player.dropbacks.toLocaleString()}</td>{data.metricDefinitions.map(definition => {
                    const metric = player.metrics[definition.key];
                    return <td key={definition.key}><div className="oc-position-value" style={{background: shading(metric)}} title={`${definition.label}: ${metric.sample} observations${definition.key === 'pressure_to_sack' ? `; pressure charted on ${player.pressureCharted} of ${player.dropbacks} dropbacks` : ''}`}><span>{format(metric.value, definition.unit)}{metric.rank != null && <small> ({metric.rank})</small>}</span></div></td>;
                })}</tr>)}</tbody>
            </table></div> : <div className="oc-empty" role="status"><h3>No quarterbacks match these settings.</h3><p>Try fewer required dropbacks, broader game filters, or a different team or name.</p></div>}
            <p className="oc-position-note">Ranks compare all {data.qualifiedPlayers} qualified quarterbacks before team and name filters. Players who changed teams have combined stats and all team logos shown. Pressure charting covers {data.pressureCharted.toLocaleString()} of {data.dropbacks.toLocaleString()} qualified dropbacks.</p>
        </>}
        <details className="oc-position-method"><summary>Metric definitions and data coverage</summary>
            <p>Quarterbacks are identified by GSIS ID and position in the local player roster. A dropback is a recorded QB dropback, including passes, sacks, and scrambles. Kneels, spikes, two-point attempts, and non-run/pass records are excluded. EPA / play uses these dropbacks, not designed QB runs.</p>
            <p>Success rate is the percentage of valid-EPA dropbacks with EPA &gt; 0. Early downs are 1st and 2nd; late downs are 3rd and 4th. Each rate uses its own eligible sample. CPOE is the mean completion percentage over expectation on charted pass attempts, in percentage points (pp). Average depth of target is mean recorded air yards on pass attempts, in yards.</p>
            <p>Pressure to sack is sacks divided by dropbacks explicitly charted as pressured in the participation source; lower ranks better. Uncharted pressure is excluded. Scramble rate is scrambles divided by dropbacks. Depth and scramble ranks describe style, not necessarily quality. Ties share a rank; unavailable metrics have no rank or heat shading. Hover a metric for its sample size.</p>
        </details>
    </section>;
}
