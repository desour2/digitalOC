"""Run in the backend's terminal: python3 -m backend.decision_support.gemini_check."""
import argparse
import json
import os
import re
import ssl
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

import certifi
from .gemini_assistant import contextualize, GeminiUnavailable


def explain_http_error(error, key):
    """Only for synthetic CLI probes: redact credentials before displaying Google prose."""
    try:
        payload = json.loads(error.read(16384))
        detail = payload.get('error', {})
        message = detail.get('message')
        if not isinstance(message, str):
            print('Google supplied no readable JSON error explanation.')
            return
        message = message.replace(key, '[REDACTED]') if key else message
        message = re.sub(r'AIza[\w-]+', '[REDACTED]', message)
        message = re.sub(r'(?i)(key=|x-goog-api-key[\s:=]+|bearer\s+)[^\s&\"<>]+', r'\1[REDACTED]', message)
        message = ''.join(c if c.isprintable() else ' ' for c in message)
        print('Google explanation (credentials redacted): ' + message[:1500])
    except (ValueError, TypeError, AttributeError, OSError):
        print('Google supplied no readable JSON error explanation.')
    finally:
        error.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate', action='store_true', help='Also test one synthetic generation (uses API quota).')
    parser.add_argument('--list-models', action='store_true', help='List model IDs advertising generateContent; no generation.')
    parser.add_argument('--plain', action='store_true', help='Test a minimal plain-text generation without a schema or game context.')
    parser.add_argument('--model', help='Test this model ID without changing the running backend.')
    args = parser.parse_args()
    key = os.environ.get('GEMINI_API_KEY', '').strip()
    model = (args.model or os.environ.get('DIGITALOC_GEMINI_MODEL', 'gemini-3.5-flash-lite')).strip()
    if not key:
        print('GEMINI_API_KEY is missing in this terminal. No request sent.')
        return 1
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}', model):
        print('Invalid model ID. No request sent.')
        return 1
    if args.list_models:
        token = None
        try:
            for _ in range(20):
                query = urlencode({'pageSize': 100, **({'pageToken': token} if token else {})})
                req = Request('https://generativelanguage.googleapis.com/v1beta/models?' + query,
                              headers={'x-goog-api-key': key})
                with urlopen(req, timeout=15, context=ssl.create_default_context(cafile=certifi.where())) as response:
                    page = json.load(response)
                for entry in page.get('models', []):
                    name = entry.get('name', '').removeprefix('models/')
                    if 'generateContent' in entry.get('supportedGenerationMethods', []) and re.fullmatch(r'[a-zA-Z0-9._-]{1,120}', name):
                        print(name)
                token = page.get('nextPageToken')
                if not token:
                    return 0
            print('More model pages exist; listing stopped at twenty pages.')
            return 1
        except HTTPError as error:
            print(f'Model listing failed: Google HTTP {error.code}.')
            explain_http_error(error, key)
            return 1
        except (URLError, TimeoutError, OSError, ValueError, TypeError, AttributeError):
            print('Could not read the model listing. No credentials or upstream body were printed.')
            return 1
    request = Request('https://generativelanguage.googleapis.com/v1beta/models/' + model,
                      headers={'x-goog-api-key': key})
    try:
        with urlopen(request, timeout=15, context=ssl.create_default_context(cafile=certifi.where())) as response:
            metadata = json.load(response)
        if 'generateContent' not in metadata.get('supportedGenerationMethods', []):
            print('The configured model does not advertise generateContent support.')
            return 1
        print('Authenticated model lookup succeeded; generateContent is supported.')
    except HTTPError as error:
        print(f'Model lookup failed: Google HTTP {error.code}. Check key permissions, quota and the configured model ID.')
        explain_http_error(error, key)
        return 1
    except (URLError, TimeoutError, OSError, ValueError):
        print('Model lookup failed before a usable response: check internet, DNS, proxy and TLS configuration.')
        return 1
    if args.plain:
        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'Reply with the word OK.'}]}],
                   'generationConfig': {'maxOutputTokens': 1024}}
        req = Request('https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent',
                      data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json', 'x-goog-api-key': key})
        try:
            with urlopen(req, timeout=45, context=ssl.create_default_context(cafile=certifi.where())) as response:
                data = json.load(response)
            parts = data['candidates'][0]['content']['parts']
            if not any(part.get('text', '').strip() for part in parts if not part.get('thought')):
                print('Plain generation returned no visible text; generation is not verified.')
                return 1
            print('Plain generation succeeded, without structured output or game context.')
        except HTTPError as error:
            print(f'Plain generation failed: Google HTTP {error.code}. This request used no coaching context or JSON schema.')
            explain_http_error(error, key)
            return 1
        except (URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError):
            print('Plain generation timed out, could not connect, or returned no usable text.')
            return 1
    if args.generate:
        os.environ['DIGITALOC_GEMINI_MODEL'] = model
        try:
            contextualize({'available_calls': [], 'state': {}, 'decision_limits': 'Synthetic connectivity check; no real game data.'},
                          'Explain that this is a connection test with no saved game and that no football recommendation can be made. Do not recommend a play.', [], None)
            print('Synthetic generation succeeded. The Gemini analysis transport is working.')
        except GeminiUnavailable as error:
            print(str(error))
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
