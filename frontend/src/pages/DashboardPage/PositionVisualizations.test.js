import React from 'react';
import {fireEvent, render, screen, waitFor, within} from '@testing-library/react';
import PositionVisualizations from './PositionVisualizations';
import {dashboardRequest} from './api';

jest.mock('./api', () => ({dashboardRequest: jest.fn()}));
const metric = (value, rank) => ({value, rank, sample: 60, rankedPlayers: 2});
const report = {
    filters: {season: 2024, season_type: 'REG', min_dropbacks: 50, week_start: 1, week_end: 22, downs: null, quarters: null},
    qualifiedPlayers: 2, dropbacks: 150, pressureCharted: 120,
    metricDefinitions: [{key: 'epa_per_play', label: 'EPA / play', unit: 'epa', lowerBetter: false},
        {key: 'pressure_to_sack', label: 'Pressure to sack', unit: 'percent', lowerBetter: true}],
    players: [
        {id: 'qb1', name: 'Baker Mayfield', teams: ['TB'], dropbacks: 90, pressureCharted: 80,
            metrics: {epa_per_play: metric(.3, 1), pressure_to_sack: metric(20, 2)}},
        {id: 'qb2', name: 'Josh Allen', teams: ['BUF'], dropbacks: 60, pressureCharted: 40,
            metrics: {epa_per_play: metric(.1, 2), pressure_to_sack: metric(10, 1)}},
    ],
};
beforeEach(() => {jest.clearAllMocks(); dashboardRequest.mockResolvedValue(report);});

test('shows ranked metrics and logos and sorts with the correct direction', async () => {
    render(<PositionVisualizations/>);
    expect(await screen.findByText('Baker Mayfield')).toBeInTheDocument();
    expect(screen.getByRole('img', {name: 'TB'})).toBeInTheDocument();
    expect(screen.getByText('+0.30')).toHaveTextContent('+0.30 (1)');
    fireEvent.click(screen.getByRole('button', {name: 'Pressure to sack'}));
    const body = screen.getByRole('table').querySelector('tbody');
    expect(within(body).getAllByRole('row')[0]).toHaveTextContent('Josh Allen');
    expect(screen.getByRole('columnheader', {name: /Pressure to sack/})).toHaveAttribute('aria-sort', 'ascending');
    fireEvent.change(screen.getByLabelText('Team'), {target: {value: 'TB'}});
    expect(screen.queryByText('Josh Allen')).not.toBeInTheDocument();
    expect(screen.getByText('20.0%')).toHaveTextContent('20.0% (2)');
    expect(dashboardRequest).toHaveBeenCalledTimes(1);
});

test('searches locally and submits situational filters together', async () => {
    render(<PositionVisualizations/>);
    await screen.findByText('Baker Mayfield');
    fireEvent.change(screen.getByLabelText('Search player'), {target: {value: 'allen'}});
    expect(screen.queryByText('Baker Mayfield')).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Minimum dropbacks'), {target: {value: '100'}});
    fireEvent.change(screen.getByLabelText('Quarter'), {target: {value: '4'}});
    fireEvent.click(screen.getByText('Apply filters'));
    await waitFor(() => expect(dashboardRequest).toHaveBeenCalledTimes(2));
    const params = new URLSearchParams(dashboardRequest.mock.calls[1][0].split('?')[1]);
    expect(params.get('min_dropbacks')).toBe('100');
    expect(params.get('quarters')).toBe('4');
    expect(params.get('position')).toBe('QB');
});

test('handles empty samples and retries backend errors', async () => {
    dashboardRequest.mockRejectedValueOnce(new Error('Missing player data'));
    dashboardRequest.mockResolvedValue({...report, players: [], qualifiedPlayers: 0, dropbacks: 0, pressureCharted: 0});
    render(<PositionVisualizations/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Missing player data');
    fireEvent.click(screen.getByText('Retry'));
    expect(await screen.findByText('No quarterbacks match these settings.')).toBeInTheDocument();
});
