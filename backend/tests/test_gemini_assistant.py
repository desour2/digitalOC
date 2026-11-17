import json
import os
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from backend.tests import test_assistant as helpers


class GeminiTests(TestCase):
    ask = helpers.AssistantTests.ask
    def setUp(self):
        helpers.AssistantTests.setUp(self)
        self.env = patch.dict(os.environ, {'DIGITALOC_ASSISTANT_PROVIDER': 'gemini',
                                          'GEMINI_API_KEY': 'test-secret', 'DIGITALOC_GEMINI_MODEL': 'gemini-3.8-flash'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def gemini_response(self, ids=None, finish='STOP'):
        return helpers.FakeResponse({'candidates': [{'finishReason': finish, 'content': {'parts': [{'text': json.dumps({
            'analysis': 'Review the available passing concepts against protection and the observed coverage. Confirm the read before choosing a call.',
            'call_ids': ['flood'] if ids is None else ids})}]}}]})

    def test_gemini_context_and_server_facts_are_separate(self):
        def fake(request, timeout, context):
            data = json.loads(request.data)
            self.assertNotIn('test-secret', request.full_url)
            self.assertEqual(request.get_header('X-goog-api-key'), 'test-secret')
            supplied = json.loads(data['contents'][-1]['parts'][0]['text'])
            self.assertNotIn('session_id', supplied['current_session'])
            self.assertEqual(supplied['current_session']['state'], self.session['state'])
            self.assertGreater(timeout, 0)
            self.assertLessEqual(timeout, 45)
            self.assertEqual(data['generationConfig']['thinkingConfig'], {'thinkingLevel': 'low'})
            self.assertTrue(context.check_hostname)
            return self.gemini_response()
        with patch('backend.decision_support.gemini_assistant.urlopen', side_effect=fake):
            result = self.ask().get_json()
        self.assertEqual(result['provider'], 'gemini')
        self.assertIn('Review the available', result['analysis'])
        self.assertIn('game is tied', result['reply'])
        self.assertEqual(result['analysis_basis'], 'model_authored_review_required')
        self.assertEqual(self.client.get(f"/api/sessions/{self.session['id']}").get_json(), self.session)

    def test_gemini_contextualizes_grounded_draft(self):
        with patch('backend.decision_support.gemini_assistant.urlopen', return_value=self.gemini_response()):
            result = self.ask(message='Draft three opening calls and two counters').get_json()
        self.assertEqual(len(result['plan']['opening_script']), 3)
        self.assertEqual(result['proposal_source'], 'coaching_rules')
        self.assertIsNotNone(result['analysis'])

    def test_gemini_rejects_invalid_references_and_truncation(self):
        for value in [self.gemini_response(['fake']), self.gemini_response(finish='MAX_TOKENS')]:
            with patch('backend.decision_support.gemini_assistant.urlopen', return_value=value):
                result = self.ask().get_json()
                self.assertIsNone(result['analysis'])
                self.assertIsNotNone(result['provider_warning'])

    def test_gemini_errors_do_not_expose_secrets(self):
        error = HTTPError('https://example.invalid', 429, 'test-secret', {}, None)
        with patch('backend.decision_support.gemini_assistant.urlopen', side_effect=error):
            result = self.ask()
        self.assertEqual(result.status_code, 200)
        self.assertNotIn('test-secret', str(result.get_json()))
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
            self.assertIn('GEMINI_API_KEY', self.ask().get_json()['provider_warning'])


    def upstream_error(self, code, status='UNAVAILABLE'):
        return HTTPError('https://example.invalid', code, 'secret-in-reason', {}, BytesIO(json.dumps({
            'error': {'status': status, 'message': 'test-secret and private coaching notes'}}).encode()))

    def test_transient_upstream_error_retries_once(self):
        with patch('backend.decision_support.gemini_assistant.urlopen', side_effect=[
                self.upstream_error(503), self.gemini_response()]) as call, \
                patch('backend.decision_support.gemini_assistant.time.sleep') as sleep:
            self.assertEqual(self.ask().status_code, 200)
        self.assertEqual(call.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_repeated_error_has_safe_status_and_no_session_changes(self):
        with patch('backend.decision_support.gemini_assistant.urlopen', side_effect=[
                self.upstream_error(503), self.upstream_error(503)]) as call, \
                patch('backend.decision_support.gemini_assistant.time.sleep'), \
                self.assertLogs('backend.decision_support.gemini_assistant', level='WARNING') as logs:
            result = self.ask()
        self.assertEqual(call.call_count, 2)
        self.assertIn('Google HTTP 503 / UNAVAILABLE', result.get_json()['provider_warning'])
        self.assertNotIn('test-secret', str(result.get_json()) + str(logs.output))
        self.assertNotIn('private coaching', str(result.get_json()) + str(logs.output))
        self.assertEqual(self.client.get(f"/api/sessions/{self.session['id']}").get_json(), self.session)

    def test_quota_error_not_retried_and_untrusted_status_not_echoed(self):
        with patch('backend.decision_support.gemini_assistant.urlopen', side_effect=self.upstream_error(
                429, 'test-secret')) as call:
            result = self.ask()
        self.assertEqual(call.call_count, 1)
        self.assertIn('Google HTTP 429', result.get_json()['provider_warning'])
        self.assertNotIn('test-secret', str(result.get_json()))

    def test_timeout_is_distinct_and_not_retried(self):
        for error in (TimeoutError('private data'), URLError(TimeoutError('private data'))):
            with patch('backend.decision_support.gemini_assistant.urlopen', side_effect=error) as call:
                result = self.ask()
            self.assertEqual(call.call_count, 1)
            self.assertEqual(result.status_code, 200)
            self.assertIn('45-second request budget', result.get_json()['provider_warning'])
            self.assertNotIn('private data', result.get_json()['provider_warning'])

    def test_provider_failure_preserves_editable_plan_without_saving(self):
        with patch('backend.decision_support.gemini_assistant.urlopen', side_effect=TimeoutError()):
            result = self.ask(message='Draft three opening calls and two counters').get_json()
        self.assertEqual(result['provider'], 'coaching_rules')
        self.assertEqual(result['configured_provider'], 'gemini')
        self.assertIsNone(result['analysis'])
        self.assertIn('timed out', result['provider_warning'])
        self.assertEqual(len(result['plan']['opening_script']), 3)
        self.assertEqual(len(result['plan']['counters']), 2)
        self.assertEqual(self.client.get(f"/api/sessions/{self.session['id']}").get_json(), self.session)

    def test_coverage_provenance_is_rendered_separately(self):
        from backend.decision_support.gemini_assistant import coverage_context
        context = {'state': {'coverage': 'UNKNOWN'}, 'preferences': {'anticipated_coverage': 'COVER_2'},
                   'evaluation': {'defense': {'status': 'historical_frequencies', 'sample_count': 207,
                       'seasons': [2020, 2024], 'scope': 'opponent and down', 'source': 'nflverse',
                       'distribution': [{'coverage': 'COVER_4', 'frequency': 0.2},
                                        {'coverage': 'COVER_2', 'frequency': 0.4}]}}}
        note = coverage_context(context)
        for text in ('No current defensive coverage', 'coach hypothesis', '207 labeled', '2020, 2024',
                     'opponent and down', 'source: nflverse', 'COVER_2: 40.0%', 'not the next snap'):
            self.assertIn(text, note)
        del context['evaluation']['defense']['source']
        self.assertIn('complete provenance is unavailable', coverage_context(context))
        self.assertNotIn('40.0%', coverage_context(context))

    def test_hypothetical_prompt_includes_exact_result_and_concise_instructions(self):
        def fake(request, **kwargs):
            body = json.loads(request.data)
            prompt = body['systemInstruction']['parts'][0]['text']
            self.assertIn('AND field position', prompt)
            self.assertIn('not a routine punt', prompt)
            self.assertIn('Never describe historical coverage as an observable read', prompt)
            supplied = json.loads(body['contents'][-1]['parts'][0]['text'])
            grounded = supplied['backend_grounded_answer']['reply']
            self.assertIn('fourth and 3 at Opponent 8', grounded)
            self.assertNotIn('punting', grounded)
            self.assertNotIn('defense', supplied['current_session']['evaluation'])
            self.assertIn('coverage_context', supplied['current_session'])
            return self.gemini_response()
        with patch('backend.decision_support.gemini_assistant.urlopen', side_effect=fake):
            result = self.ask(message='If we gain 12 yards, how do our options change?').get_json()
        self.assertEqual(result['provider'], 'gemini')
        self.assertIn('No current defensive coverage', result['coverage_context'])

    def test_guaranteed_points_claim_withheld_but_calculation_preserved(self):
        analysis = ('You would face fourth and three at the opponent eight. Check whether the guaranteed three points '
                    'outweigh the risk of going for it.')
        value = helpers.FakeResponse({'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps({
            'analysis': analysis, 'call_ids': []})}]}}]})
        with patch('backend.decision_support.gemini_assistant.urlopen', return_value=value):
            result = self.ask(message='If we gain 12 yards, what next?').get_json()
        self.assertIsNone(result['analysis'])
        self.assertEqual(result['provider'], 'coaching_rules')
        self.assertIn('scoring as certain', result['provider_warning'])
        self.assertIn('fourth and 3 at Opponent 8', result['reply'])
        self.assertIn('chance at three points', result['reply'])

    def test_conditional_kicking_language_accepted(self):
        analysis = ('You would face fourth and three at the opponent eight. A field goal offers a chance at three points; '
                    'no field goal is guaranteed. Confirm protection and conditions before deciding.')
        value = helpers.FakeResponse({'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps({
            'analysis': analysis, 'call_ids': []})}]}}]})
        with patch('backend.decision_support.gemini_assistant.urlopen', return_value=value):
            result = self.ask(message='If we gain 12 yards, what next?').get_json()
        self.assertEqual(result['analysis'], analysis)
        self.assertIsNone(result['provider_warning'])
