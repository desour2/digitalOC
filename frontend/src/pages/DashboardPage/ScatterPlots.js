import React, {useEffect, useId, useRef, useState} from 'react';
import {dashboardRequest} from './api';
import teamLogos from './teamLogos';
import './scatterPlots.css';

const defaults = {season: '2024', season_type: 'REG', downs: [], quarters: [], week_start: '1', week_end: '22'};
const initialX = {side: 'offense', metric: 'epa_per_run'};
const initialY = {side: 'offense', metric: 'epa_per_pass'};
const number = (value, unit) => `${value.toLocaleString(undefined, {minimumFractionDigits: unit === 'epa' ? 3 : 0, maximumFractionDigits: unit === 'epa' ? 3 : 2})}${unit === 'percent' ? '%' : ''}`;
const axisLabel = (axis, definition) => `${axis.side === 'offense' ? 'Offense' : 'Defense'} · ${definition.label}${axis.side === 'defense' && !['run_rate', 'pass_rate'].includes(axis.metric) ? ' allowed' : ''}`;

export function scatterPoints(rows, xAxis, yAxis, minimum) {
    return rows.flatMap(row => {
        const x = row[xAxis.side].metrics[xAxis.metric];
        const y = row[yAxis.side].metrics[yAxis.metric];
        return Number.isFinite(x?.value) && Number.isFinite(y?.value) && x.sample >= minimum && y.sample >= minimum
            ? [{team: row.team, x: x.value, y: y.value, xSample: x.sample, ySample: y.sample}] : [];
    });
}

function domain(values) {
    const low = Math.min(...values), high = Math.max(...values);
    const pad = (high - low) * .12 || Math.max(Math.abs(low) * .12, .1);
    return [low - pad, high + pad];
}

function AxisControls({name, value, onChange, definitions}) {
    return <fieldset className="oc-scatter-axis"><legend>{name} axis</legend>
        <label>Unit<select aria-label={`${name} axis unit`} value={value.side} onChange={e => onChange({...value, side: e.target.value})}><option value="offense">Offense</option><option value="defense">Defense</option></select></label>
        <label>Metric<select aria-label={`${name} axis metric`} value={value.metric} onChange={e => onChange({...value, metric: e.target.value})}>{definitions.map(d => <option key={d.key} value={d.key}>{d.label}</option>)}</select></label>
    </fieldset>;
}

function FilterChoices({label, values, selected, onChange}) {
    return <fieldset className="oc-scatter-choices"><legend>{label}</legend>
        <button type="button" aria-pressed={!selected.length} onClick={() => onChange([])}>All</button>
        {values.map(([value, title]) => <label key={value}><input type="checkbox" checked={selected.includes(value)} onChange={() => onChange(selected.includes(value) ? selected.filter(v => v !== value) : [...selected, value].sort())}/>{title}</label>)}
    </fieldset>;
}

function saveFile(contents, type, filename) {
    const url = URL.createObjectURL(new Blob([contents], {type}));
    const link = document.createElement('a');
    link.href = url; link.download = filename; document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function embedPlotLogos(svg) {
    const images = [...svg.querySelectorAll('image')];
    const sources = [...new Set(images.map(image => image.getAttribute('href')))];
    const embedded = new Map(await Promise.all(sources.map(async source => {
        if (source.startsWith('data:')) return [source, source];
        const response = await fetch(source);
        if (!response.ok) throw new Error('Unable to load team logos for download. Please retry.');
        const blob = await response.blob();
        const dataUrl = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(new Error('Unable to embed team logos. Please retry.'));
            reader.readAsDataURL(blob);
        });
        return [source, dataUrl];
    })));
    images.forEach(image => image.setAttribute('href', embedded.get(image.getAttribute('href'))));
}

function ScatterChart({points, xLabel, yLabel, xDefinition, yDefinition, highlight, labels, svgRef, onSelect}) {
    const titleId = useId();
    const width = 960, height = 580, left = 94, right = 40, top = 42, bottom = 90;
    const xDomain = domain(points.map(p => p.x)), yDomain = domain(points.map(p => p.y));
    const x = value => left + (value - xDomain[0]) / (xDomain[1] - xDomain[0]) * (width - left - right);
    const y = value => height - bottom - (value - yDomain[0]) / (yDomain[1] - yDomain[0]) * (height - top - bottom);
    const meanX = points.reduce((sum, p) => sum + p.x, 0) / points.length;
    const meanY = points.reduce((sum, p) => sum + p.y, 0) / points.length;
    const ticks = range => Array.from({length: 6}, (_, i) => range[0] + i * (range[1] - range[0]) / 5);
    return <svg ref={svgRef} xmlns="http://www.w3.org/2000/svg" viewBox={`0 0 ${width} ${height}`} role="group" aria-labelledby={titleId} className="oc-scatter-svg" fontFamily="Arial, sans-serif">
        <title id={titleId}>{xLabel} versus {yLabel}. Each point is one NFL team.</title>
        <desc>Use Tab to focus team points and Enter to inspect their metrics. Dashed lines show unweighted averages of displayed teams.</desc>
        <rect width={width} height={height} fill="#fff"/>
        {ticks(xDomain).map((value, i) => <g key={`x${i}`}><line x1={x(value)} x2={x(value)} y1={top} y2={height - bottom} stroke="#e6eae3"/><text x={x(value)} y={height - bottom + 26} textAnchor="middle" fontSize="12" fill="#59685d">{number(value, xDefinition.unit)}</text></g>)}
        {ticks(yDomain).map((value, i) => <g key={`y${i}`}><line x1={left} x2={width - right} y1={y(value)} y2={y(value)} stroke="#e6eae3"/><text x={left - 12} y={y(value) + 4} textAnchor="end" fontSize="12" fill="#59685d">{number(value, yDefinition.unit)}</text></g>)}
        {xDomain[0] < 0 && xDomain[1] > 0 && <line x1={x(0)} x2={x(0)} y1={top} y2={height - bottom} stroke="#bdc8be"/>}
        {yDomain[0] < 0 && yDomain[1] > 0 && <line x1={left} x2={width - right} y1={y(0)} y2={y(0)} stroke="#bdc8be"/>}
        <line x1={x(meanX)} x2={x(meanX)} y1={top} y2={height - bottom} stroke="#718175" strokeDasharray="6 5"/>
        <line x1={left} x2={width - right} y1={y(meanY)} y2={y(meanY)} stroke="#718175" strokeDasharray="6 5"/>
        <text x={left} y={22} fontSize="12" fill="#59685d">Displayed-team averages: X {number(meanX, xDefinition.unit)} · Y {number(meanY, yDefinition.unit)}</text>
        <line x1={left} x2={width - right} y1={height - bottom} y2={height - bottom} stroke="#9aab9c"/>
        <line x1={left} x2={left} y1={top} y2={height - bottom} stroke="#9aab9c"/>
        <text x={(left + width - right) / 2} y={height - 24} textAnchor="middle" fontSize="15" fontWeight="600" fill="#1c2923">{xLabel}</text>
        <text transform={`translate(23 ${(top + height - bottom) / 2}) rotate(-90)`} textAnchor="middle" fontSize="15" fontWeight="600" fill="#1c2923">{yLabel}</text>
        {[...points].sort((a, b) => Number(a.team === highlight) - Number(b.team === highlight)).map(point => <g key={point.team} role="button" tabIndex="0" className="oc-scatter-point" aria-label={`${point.team}: ${xLabel} ${number(point.x, xDefinition.unit)}, ${point.xSample} plays; ${yLabel} ${number(point.y, yDefinition.unit)}, ${point.ySample} plays`} onMouseEnter={() => onSelect(point.team)} onFocus={() => onSelect(point.team)} onClick={() => onSelect(point.team)} onKeyDown={event => {if (['Enter', ' '].includes(event.key)) {event.preventDefault(); onSelect(point.team);}}}>
            <title>{point.team}: X {number(point.x, xDefinition.unit)} (n={point.xSample}), Y {number(point.y, yDefinition.unit)} (n={point.ySample})</title>
            <g className="oc-scatter-marker" opacity={highlight && point.team !== highlight ? .35 : 1}>
                <circle cx={x(point.x)} cy={y(point.y)} r={point.team === highlight ? 23 : 20} fill="none" stroke={point.team === highlight ? '#234b36' : 'none'} strokeWidth="2"/>
                {teamLogos[point.team] && <image href={teamLogos[point.team]} x={x(point.x) - (point.team === highlight ? 19 : 16)} y={y(point.y) - (point.team === highlight ? 19 : 16)} width={point.team === highlight ? 38 : 32} height={point.team === highlight ? 38 : 32} preserveAspectRatio="xMidYMid meet" aria-hidden="true" pointerEvents="none"/>}
            </g>
            {(labels || point.team === highlight || !teamLogos[point.team]) && <text x={x(point.x)} y={y(point.y) - 27} textAnchor="middle" fill="#234b36" fontWeight="700" fontSize="11" paintOrder="stroke" stroke="#fff" strokeWidth="3" strokeLinejoin="round">{point.team}</text>}
        </g>)}
    </svg>;
}

export default function ScatterPlots() {
    const [draft, setDraft] = useState(defaults);
    const [filters, setFilters] = useState(defaults);
    const [xAxis, setXAxis] = useState(initialX);
    const [yAxis, setYAxis] = useState(initialY);
    const [minimum, setMinimum] = useState('20');
    const [highlight, setHighlight] = useState('');
    const [labels, setLabels] = useState(true);
    const [selected, setSelected] = useState('');
    const [data, setData] = useState(null);
    const [error, setError] = useState('');
    const [filterError, setFilterError] = useState('');
    const [retry, setRetry] = useState(0);
    const [exporting, setExporting] = useState(false);
    const [exportError, setExportError] = useState('');
    const svgRef = useRef(null);
    useEffect(() => {
        const controller = new AbortController();
        setData(null); setError('');
        const query = new URLSearchParams({...filters, downs: filters.downs.join(',') || 'all', quarters: filters.quarters.join(',') || 'all'});
        dashboardRequest(`/api/scatter?${query}`, {signal: controller.signal})
            .then(value => {if (!controller.signal.aborted) setData(value);})
            .catch(failure => {if (!controller.signal.aborted) setError(failure.message);});
        return () => controller.abort();
    }, [filters, retry]);
    const change = (key, value) => setDraft(previous => ({...previous, [key]: value}));
    const definitions = data?.metricDefinitions || [];
    const xDefinition = definitions.find(d => d.key === xAxis.metric);
    const yDefinition = definitions.find(d => d.key === yAxis.metric);
    const xLabel = xDefinition ? axisLabel(xAxis, xDefinition) : '';
    const yLabel = yDefinition ? axisLabel(yAxis, yDefinition) : '';
    const points = data ? scatterPoints(data.teams, xAxis, yAxis, Math.max(1, Number(minimum) || 1)) : [];
    const inspected = points.find(p => p.team === selected) || points.find(p => p.team === highlight);
    const apply = event => {
        event.preventDefault();
        if (Number(draft.week_start) > Number(draft.week_end)) {setFilterError('First week must be before or equal to last week.'); return;}
        setFilterError(''); setFilters({...draft});
    };
    const exportCSV = () => {
        const f = data.filters;
        const header = ['Team', xLabel, 'X sample', yLabel, 'Y sample', 'Season', 'Season type', 'Downs', 'Quarters', 'First week', 'Last week'];
        const rows = points.map(p => [p.team, p.x, p.xSample, p.y, p.ySample, f.season, f.season_type, f.downs?.join('+') || 'all', f.quarters?.join('+') || 'all', f.week_start, f.week_end]);
        saveFile([header, ...rows].map(row => row.map(value => `"${String(value).replace(/"/g, '""')}"`).join(',')).join('\r\n'), 'text/csv;charset=utf-8', `digitaloc-scatter-${f.season}.csv`);
    };
    const exportPlot = async () => {
        setExportError(''); setExporting(true);
        try {
            const svg = svgRef.current.cloneNode(true);
            // XMLSerializer supplies the SVG namespace from the element itself.
            svg.removeAttribute('xmlns');
            await embedPlotLogos(svg);
            saveFile(new XMLSerializer().serializeToString(svg), 'image/svg+xml;charset=utf-8', `digitaloc-scatter-${data.filters.season}.svg`);
        } catch (failure) {
            setExportError(failure.message || 'Unable to download the plot. Please retry.');
        } finally { setExporting(false); }
    };
    return <section className="oc-panel oc-scatter" aria-label="Scatter plot explorer">
        <div className="oc-scatter-heading"><span className="oc-tiny-badge">LEAGUE EXPLORER</span><h2>Build your comparison.</h2><p>One team per point. Choose any two metrics and isolate the situations that matter.</p></div>
        <form onSubmit={apply} className="oc-scatter-filter-form">
            <div className="oc-scatter-filter-row">
                <label>Season<select value={draft.season} onChange={e => change('season', e.target.value)}>{[2024, 2023, 2022, 2021, 2020].map(year => <option key={year}>{year}</option>)}</select></label>
                <label>Season phase<select value={draft.season_type} onChange={e => change('season_type', e.target.value)}><option value="REG">Regular season</option><option value="POST">Postseason</option><option value="all">Regular + postseason</option></select></label>
                <label>First week<input required type="number" min="1" max="22" value={draft.week_start} onChange={e => change('week_start', e.target.value)}/></label>
                <label>Last week<input required type="number" min="1" max="22" value={draft.week_end} onChange={e => change('week_end', e.target.value)}/></label>
            </div>
            <div className="oc-scatter-filter-row">
                <FilterChoices label="Downs" values={[[1, '1st'], [2, '2nd'], [3, '3rd'], [4, '4th']]} selected={draft.downs} onChange={value => change('downs', value)}/>
                <FilterChoices label="Quarters" values={[[1, 'Q1'], [2, 'Q2'], [3, 'Q3'], [4, 'Q4'], [5, 'OT']]} selected={draft.quarters} onChange={value => change('quarters', value)}/>
                <button type="submit" className="oc-primary">Apply filters</button>
            </div>
            {filterError && <p className="oc-error" role="alert">{filterError}</p>}
        </form>
        {error ? <div className="oc-error" role="alert">{error}<button className="oc-secondary" onClick={() => setRetry(n => n + 1)}>Retry</button></div> : !data ? <p role="status" className="oc-scatter-loading">Loading team scatter data…</p> : <>
            <div className="oc-scatter-axes"><AxisControls name="X" value={xAxis} onChange={setXAxis} definitions={definitions}/><button className="oc-secondary oc-scatter-swap" onClick={() => {setXAxis(yAxis); setYAxis(xAxis);}}>Swap axes</button><AxisControls name="Y" value={yAxis} onChange={setYAxis} definitions={definitions}/></div>
            <div className="oc-scatter-options">
                <label>Minimum plays per axis<input type="number" min="1" max="10000" value={minimum} onChange={e => setMinimum(e.target.value)}/></label>
                <label>Highlight team<select value={highlight} onChange={e => {setHighlight(e.target.value); setSelected(e.target.value);}}><option value="">All teams</option>{data.teams.map(row => <option key={row.team}>{row.team}</option>)}</select></label>
                <label className="oc-scatter-label-toggle"><input type="checkbox" checked={labels} onChange={e => setLabels(e.target.checked)}/>Show team labels</label>
                <div className="oc-scatter-exports"><button className="oc-secondary" disabled={!points.length} onClick={exportCSV}>Download CSV</button><button className="oc-secondary" disabled={!points.length || exporting} onClick={exportPlot}>{exporting ? 'Preparing plot…' : 'Download plot'}</button></div>
            </div>
            {exportError && <p className="oc-error" role="alert">{exportError}</p>}
            <p className="oc-scatter-context">{data.filters.season} · {data.filters.season_type === 'REG' ? 'Regular season' : data.filters.season_type === 'POST' ? 'Postseason' : 'Regular + postseason'} · Downs: {data.filters.downs?.join(', ') || 'all'} · Quarters: {data.filters.quarters?.map(q => q === 5 ? 'OT' : q).join(', ') || 'all'} · Weeks {data.filters.week_start}–{data.filters.week_end}</p>
            <div className="oc-scatter-result-heading"><strong>{points.length} of {data.teams.length} teams plotted</strong><span>{data.playCount.toLocaleString()} matching plays · {data.teams.length - points.length} teams lack the required axis samples</span></div>
            {points.length ? <>
                <div className="oc-scatter-chart-wrap"><ScatterChart points={points} xLabel={xLabel} yLabel={yLabel} xDefinition={xDefinition} yDefinition={yDefinition} highlight={highlight} labels={labels} svgRef={svgRef} onSelect={setSelected}/></div>
                <div className="oc-scatter-inspector" aria-live="polite">{inspected ? <><strong>{inspected.team}</strong><span>{xLabel}: <b>{number(inspected.x, xDefinition.unit)}</b> <small>({inspected.xSample} plays)</small></span><span>{yLabel}: <b>{number(inspected.y, yDefinition.unit)}</b> <small>({inspected.ySample} plays)</small></span></> : <span>Hover, click, or focus a team point to inspect its values and sample sizes.</span>}</div>
                <details className="oc-scatter-data"><summary>View plotted data ({points.length} teams)</summary><div className="oc-scatter-table-wrap"><table><caption>Values and sample sizes for the current axes and filters</caption><thead><tr><th>Team</th><th>{xLabel}</th><th>X plays</th><th>{yLabel}</th><th>Y plays</th></tr></thead><tbody>{points.map(p => <tr key={p.team}><th scope="row">{p.team}</th><td>{number(p.x, xDefinition.unit)}</td><td>{p.xSample}</td><td>{number(p.y, yDefinition.unit)}</td><td>{p.ySample}</td></tr>)}</tbody></table></div></details>
            </> : <div className="oc-empty" role="status"><h3>No teams meet these settings.</h3><p>Lower the minimum plays, broaden your filters, or select metrics with available samples.</p></div>}
            {highlight && !points.some(p => p.team === highlight) && <p className="oc-inline-help">{highlight} is outside the plotted sample for these settings.</p>}
        </>}
        <details className="oc-scatter-method"><summary>How these metrics are calculated</summary><p>Historical play-by-play, not model predictions. Run/pass follows the recorded play type: passes include sacks; quarterback scrambles count as runs. Kneels, spikes, two-point attempts, and non-run/pass records are excluded. Net yards per pass includes sack losses.</p><p>EPA is always from the offense’s perspective. Defensive EPA is EPA allowed, so lower is better. Defensive success and yardage rates also describe what opponents gained. Success means EPA &gt; 0. Missing EPA or yardage is excluded from that metric’s sample rather than counted as zero.</p><p>Minimum plays applies separately to each axis’s valid observations. Dashed lines show unweighted averages of the teams currently plotted. Week numbers follow the source, including postseason weeks (up to 22). Filters apply to both axes.</p></details>
    </section>;
}
