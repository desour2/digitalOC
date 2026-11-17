import React from 'react';
import {fireEvent, render, screen, waitFor} from '@testing-library/react';
import ScatterPlots, {scatterPoints} from './ScatterPlots';
import {dashboardRequest} from './api';

jest.mock('./api', () => ({dashboardRequest: jest.fn()}));

const definitions = [
    {key: 'epa_per_run', label: 'EPA per run', unit: 'epa'},
    {key: 'epa_per_pass', label: 'EPA per pass', unit: 'epa'},
    {key: 'success_rate', label: 'Success rate', unit: 'percent'},
];
const unit = (run, pass, sample = 100) => ({metrics: {
    epa_per_run: {value: run, sample}, epa_per_pass: {value: pass, sample}, success_rate: {value: 50, sample},
}});
const report = {
    filters: {season: 2024, season_type: 'REG', downs: null, quarters: null, week_start: 1, week_end: 22},
    metricDefinitions: definitions, playCount: 400,
    teams: [
        {team: 'TB', offense: unit(.12, .35), defense: unit(-.1, -.2)},
        {team: 'BUF', offense: unit(-.03, .4), defense: unit(-.05, .1)},
        {team: 'NYJ', offense: unit(.01, null), defense: unit(.1, .2, 3)},
    ],
};

beforeEach(() => {jest.clearAllMocks(); dashboardRequest.mockResolvedValue(report);});

test('axes support cross-unit comparisons and inspectable points with their own samples', async () => {
    render(<ScatterPlots/>);
    expect(await screen.findByText('2 of 3 teams plotted')).toBeInTheDocument();
    const point = screen.getByRole('button', {name: /TB: Offense.*EPA per run/});
    fireEvent.focus(point);
    expect(screen.getByText('0.120', {selector: 'b'})).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Y axis unit'), {target: {value: 'defense'}});
    expect(screen.getByRole('button', {name: /TB:.*Defense.*EPA per pass allowed -0.200/})).toBeInTheDocument();
    expect(dashboardRequest).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('Swap axes'));
    expect(screen.getByLabelText('X axis unit')).toHaveValue('defense');
    expect(screen.getByLabelText('X axis metric')).toHaveValue('epa_per_pass');
});

test('submits combined situational filters and rejects inverted weeks', async () => {
    render(<ScatterPlots/>);
    await screen.findByText('2 of 3 teams plotted');
    fireEvent.click(screen.getByLabelText('1st'));
    fireEvent.click(screen.getByLabelText('3rd'));
    fireEvent.click(screen.getByLabelText('Q4'));
    fireEvent.change(screen.getByLabelText('First week'), {target: {value: '5'}});
    fireEvent.change(screen.getByLabelText('Last week'), {target: {value: '2'}});
    fireEvent.click(screen.getByText('Apply filters'));
    expect(screen.getByRole('alert')).toHaveTextContent('First week');
    expect(dashboardRequest).toHaveBeenCalledTimes(1);
    fireEvent.change(screen.getByLabelText('Last week'), {target: {value: '10'}});
    fireEvent.click(screen.getByText('Apply filters'));
    await waitFor(() => expect(dashboardRequest).toHaveBeenCalledTimes(2));
    const url = dashboardRequest.mock.calls[1][0];
    const params = new URLSearchParams(url.split('?')[1]);
    expect(params.get('downs')).toBe('1,3');
    expect(params.get('quarters')).toBe('4');
    expect(params.get('week_start')).toBe('5');
    expect(params.get('week_end')).toBe('10');
});

test('excludes missing values and low samples; handles empty and identical-value charts', async () => {
    expect(scatterPoints(report.teams, {side: 'offense', metric: 'epa_per_run'}, {side: 'offense', metric: 'epa_per_pass'}, 20)).toHaveLength(2);
    dashboardRequest.mockResolvedValue({...report, teams: [report.teams[0]]});
    render(<ScatterPlots/>);
    expect(await screen.findByText('1 of 1 teams plotted')).toBeInTheDocument();
    expect(screen.getByRole('group', {name: /versus/}).innerHTML).not.toMatch(/NaN|Infinity/);
    fireEvent.change(screen.getByLabelText('Minimum plays per axis'), {target: {value: '101'}});
    expect(screen.getByText('No teams meet these settings.')).toBeInTheDocument();
    expect(screen.getByText('Download plot')).toBeDisabled();
});

test('recovers from backend errors through retry', async () => {
    dashboardRequest.mockRejectedValueOnce(new Error('Missing source files'));
    render(<ScatterPlots/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Missing source files');
    fireEvent.click(screen.getByText('Retry'));
    expect(await screen.findByText('2 of 3 teams plotted')).toBeInTheDocument();
});

test('downloaded SVG embeds logo images so it works away from the app', async () => {
    const originalFetch = global.fetch;
    const originalCreate = URL.createObjectURL;
    const originalRevoke = URL.revokeObjectURL;
    const click = jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    global.fetch = jest.fn().mockResolvedValue({ok: true, blob: async () => new Blob(['logo'], {type: 'image/png'})});
    URL.createObjectURL = jest.fn(() => 'blob:plot');
    URL.revokeObjectURL = jest.fn();
    try {
        render(<ScatterPlots/>);
        await screen.findByText('2 of 3 teams plotted');
        expect(screen.getByRole('button', {name: /TB: Offense/}).querySelector('image')).toBeInTheDocument();
        fireEvent.click(screen.getByText('Download plot'));
        await waitFor(() => expect(URL.createObjectURL).toHaveBeenCalledTimes(1));
        const svg = await new Promise(resolve => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.readAsText(URL.createObjectURL.mock.calls[0][0]);
        });
        const document = new DOMParser().parseFromString(svg, 'image/svg+xml');
        expect(document.querySelector('parsererror')?.textContent).toBeUndefined();
        const images = [...document.querySelectorAll('image')];
        expect(images).toHaveLength(2);
        images.forEach(image => expect(image.getAttribute('href')).toMatch(/^data:image\/png;base64,/));
        expect(click).toHaveBeenCalledTimes(1);
    } finally {
        global.fetch = originalFetch;
        URL.createObjectURL = originalCreate;
        URL.revokeObjectURL = originalRevoke;
        click.mockRestore();
    }
});
