import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.error import HTTPError
from backend.decision_support import gemini_check
from backend.tests.test_assistant import FakeResponse


class GeminiCheckTests(unittest.TestCase):
    def run_check(self, args, responses):
        output = io.StringIO()
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'secret-key'}), \
                patch('sys.argv', ['gemini_check', *args]), \
                patch.object(gemini_check, 'urlopen', side_effect=responses) as call, redirect_stdout(output):
            code = gemini_check.main()
        self.assertNotIn('secret-key', output.getvalue())
        return code, output.getvalue(), call

    def test_model_list_paginates_and_filters(self):
        code, output, call = self.run_check(['--list-models'], [
            FakeResponse({'models': [{'name': 'models/test-flash', 'supportedGenerationMethods': ['generateContent']}], 'nextPageToken': 'next'}),
            FakeResponse({'models': [{'name': 'models/embedding', 'supportedGenerationMethods': ['embedContent']}]})])
        self.assertEqual(code, 0)
        self.assertIn('test-flash', output)
        self.assertNotIn('embedding', output)
        self.assertEqual(call.call_count, 2)

    def test_plain_probe_excludes_schema_and_context(self):
        code, output, call = self.run_check(['--plain', '--model', 'test-flash'], [
            FakeResponse({'supportedGenerationMethods': ['generateContent']}),
            FakeResponse({'candidates': [{'content': {'parts': [{'text': 'OK'}]}}]})])
        self.assertEqual(code, 0)
        req = call.call_args.args[0]
        self.assertIn('/test-flash:generateContent', req.full_url)
        body = json.loads(req.data)
        self.assertNotIn('responseJsonSchema', body['generationConfig'])
        self.assertNotIn('systemInstruction', body)

    def test_plain_503_reports_stage(self):
        code, output, _ = self.run_check(['--plain'], [
            FakeResponse({'supportedGenerationMethods': ['generateContent']}),
            HTTPError('https://example.invalid', 503, 'secret-key', {}, None)])
        self.assertEqual(code, 1)
        self.assertIn('Plain generation failed: Google HTTP 503', output)

    def test_plain_404_explanation_redacts_key(self):
        error = HTTPError('https://example.invalid', 404, 'not found', {}, io.BytesIO(json.dumps({
            'error': {'message': 'Model is not supported for generateContent. Key=secret-key.'}
        }).encode()))
        code, output, _ = self.run_check(['--plain'], [
            FakeResponse({'supportedGenerationMethods': ['generateContent']}), error])
        self.assertEqual(code, 1)
        self.assertIn('Model is not supported for generateContent', output)
        self.assertIn('[REDACTED]', output)
