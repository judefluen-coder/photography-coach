"""Real loopback HTTP + injected Responses transport. No external API calls or fees."""

from __future__ import annotations

import copy
import http.client
import io
import json
import re
import sys
import tempfile
import threading
import time
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.server import LocalServer
from app.workbench import ROOT, Workbench, WorkbenchError, atomic_json
from core.contracts import REPORT_SCHEMA
from core.images import MAX_BYTES
from core.provider import ResponsesProvider
from test_workbench_core import recipe


def photo() -> bytes:
    buffer = io.BytesIO()
    Image.new('RGB', (80, 60), (40, 100, 160)).save(buffer, format='PNG')
    return buffer.getvalue()


def fixture() -> dict:
    original = json.loads((ROOT / 'docs/demo/report.json').read_text())
    report = {key: copy.deepcopy(original[key]) for key in REPORT_SCHEMA['properties']}
    report['edit'].pop('crop_region', None)
    for observation in report['observations']:
        observation.setdefault('regions', [])
    return {'report': report, 'recipe': recipe(), 'method_tags': ['明暗', '形状']}


class OfflineTransport:
    def __init__(self):
        self.calls = []
        self.release = threading.Event()
        self.release.set()
        self.started = threading.Event()
        self.invalid = False

    def __call__(self, url, method, body, headers):
        self.calls.append(json.loads(body))
        self.started.set()
        self.release.wait(5)
        schema = self.calls[-1]['text']['format']['schema']
        output = fixture() if 'report' in schema['properties'] else {'answer': '离线测试回答，不是对合成图的真实点评。', 'boundary': '没有修改原评分。'}
        if self.invalid:
            output = {'wrong': 'not a report'}
        response = {'status': 'completed', 'usage': {'input_tokens': 20, 'output_tokens': 30, 'total_tokens': 50},
                    'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(output)}]}]}
        return json.dumps(response).encode(), 'application/json'


class WorkbenchServerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data = Path(self.temp.name).resolve() / 'private'
        self.transport = OfflineTransport()
        self.workbench = Workbench(self.data, provider_factory=lambda settings: ResponsesProvider(settings, transport=self.transport))
        self.server = LocalServer(0, self.workbench)
        self.worker = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=.02), daemon=True)
        self.worker.start()
        self.token = self.server.token

    def tearDown(self):
        self.transport.release.set()
        if self.workbench.thread:
            self.workbench.thread.join(10)
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(2)
        self.temp.cleanup()

    def request(self, method, path, data=None, *, headers=None):
        base = {'Host': self.server.host, 'X-Workbench-Token': self.token}
        if isinstance(data, dict):
            data = json.dumps(data).encode()
            base['Content-Type'] = 'application/json'
        elif isinstance(data, bytes):
            base['Content-Type'] = 'application/octet-stream'
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body=data, headers={**base, **(headers or {})})
            response = connection.getresponse()
            body = response.read()
            return response.status, body, dict(response.getheaders())
        finally:
            connection.close()

    def json_request(self, method, path, data=None, **kwargs):
        status, raw, _ = self.request(method, path, data, **kwargs)
        return status, json.loads(raw)

    def upload(self):
        status, value = self.json_request('POST', '/api/photos', photo(), headers={'X-Photo-Name': 'test-only.png'})
        self.assertEqual(status, 201, value)
        return value['id']

    def configure(self):
        status, config = self.json_request('POST', '/api/config', {'base_url': 'https://example.com/v1', 'model': 'offline-test-model', 'api_key': 'test-only-not-a-real-key', 'max_output_tokens': 10000})
        self.assertEqual(status, 200, config)
        return config['revision']

    def start(self, session_id, task='critique', **extra):
        payload = {'request_id': uuid.uuid4().hex, 'consent': True, 'config_revision': self.workbench.config_revision, **extra}
        return self.json_request('POST', f'/api/sessions/{session_id}/{task}', payload)

    def finish(self, session_id):
        deadline = time.monotonic() + 10
        while self.workbench.busy and time.monotonic() < deadline:
            self.workbench.thread.join(.05)
        self.assertIsNone(self.workbench.busy)
        return self.workbench.get(session_id)

    def test_standalone_page_and_demo_need_no_key_or_codex(self):
        for path in ('/', '/app.css', '/app.js', '/demo/index.html?embedded=1', '/demo/assets/source-preview.jpg', '/demo-street/index.html?embedded=1', '/demo-street/assets/source.jpg'):
            status, body, headers = self.request('GET', path)
            self.assertEqual(status, 200, path)
            self.assertTrue(body)
            self.assertEqual(headers['Cache-Control'], 'no-store')
        status, state = self.json_request('GET', '/api/state')
        self.assertEqual(status, 200)
        self.assertFalse(state['config']['configured'])
        self.assertEqual(state['sessions'], [])
        self.assertEqual(self.transport.calls, [])

    def test_host_origin_fetch_site_and_token_are_enforced(self):
        for headers in ({'Host': 'evil.example'}, {'Origin': 'https://evil.example'}, {'Sec-Fetch-Site': 'cross-site'}, {'X-Workbench-Token': 'wrong'}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request('POST', '/api/photos', photo(), headers=headers)[0], 403)
        self.assertEqual(self.request('GET', '/api/state', headers={'Origin': 'https://evil.example'})[0], 403)
        self.assertEqual(self.request('GET', '/', headers={'Host': 'localhost:'+str(self.server.server_port)})[0], 403)

    def test_paths_and_private_files_are_not_served(self):
        session_id = self.upload()
        for path in ('/../README.md', '/%2e%2e/README.md', '/.git/config', '/api/photos', '/demo/report.json', '/demo-street/report.json', '/demo-street/assets/../../README.md', '/demo-street/assets/source.jpg/../../README.md', '/demo-street/assets/not-allowed.jpg', f'/media/{session_id}/session.json', f'/media/{session_id}/../../workbench.json'):
            self.assertEqual(self.request('GET', path)[0], 404, path)

    def test_file_validation_and_limits(self):
        for raw in (b'', b'not-an-image'):
            self.assertEqual(self.request('POST', '/api/photos', raw)[0], 400)
        self.assertEqual(self.request('POST', '/api/photos', b'', headers={'Content-Length': str(MAX_BYTES+1)})[0], 413)
        self.assertEqual(self.request('POST', '/api/photos', photo(), headers={'Content-Type': 'image/png'})[0], 415)
        self.assertEqual(self.request('POST', '/api/config', b'[]', headers={'Content-Type': 'application/json'})[0], 400)

    def test_photo_upload_does_not_call_model_and_retains_original(self):
        session_id = self.upload()
        status, result = self.json_request('GET', '/api/sessions/'+session_id)
        self.assertEqual((status, result['state']), (200, 'uploaded'))
        self.assertIsNone(result['report_url'])
        self.assertEqual(self.transport.calls, [])
        original = self.request('GET', result['original_url'])[1]
        self.assertEqual(original, photo())
        self.assertNotIn(str(self.data), json.dumps(result))

    def test_config_is_memory_only_and_private_endpoint_rejected(self):
        self.configure()
        _, state = self.json_request('GET', '/api/state')
        self.assertNotIn('test-only-not-a-real-key', json.dumps(state))
        self.assertNotIn('api_key', state['config'])
        self.assertEqual(self.transport.calls, [])
        for file in self.data.rglob('*.json'):
            self.assertNotIn('test-only-not-a-real-key', file.read_text())
        self.assertFalse(Workbench(self.data).configuration()['configured'])
        for endpoint in ('http://example.com', 'https://127.0.0.1', 'https://example.com:8443', 'https://user:secret@example.com'):
            self.assertEqual(self.request('POST', '/api/config', {'base_url':endpoint,'model':'test','api_key':'test'})[0], 400)

    def test_normalized_copies_do_not_inherit_original_metadata(self):
        image = Image.new('RGB', (80, 60), (40, 100, 160))
        exif = Image.Exif()
        exif[270] = 'test-only-private-description'
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', exif=exif)
        status, uploaded = self.json_request('POST', '/api/photos', buffer.getvalue())
        self.assertEqual(status, 201)
        self.assertEqual(self.request('GET', uploaded['original_url'])[1], buffer.getvalue())
        directory = self.workbench.directory(uploaded['id'])
        for name in ('source.png', 'preview.jpg'):
            with Image.open(directory / name) as normalized:
                self.assertFalse(normalized.getexif())
                self.assertNotIn('icc_profile', normalized.info)
            self.assertNotIn(b'test-only-private-description', (directory / name).read_bytes())

    def test_confirmation_and_current_destination_are_required(self):
        session_id = self.upload()
        self.assertEqual(self.start(session_id)[0], 409)
        revision = self.configure()
        self.assertEqual(self.start(session_id, consent=False)[0], 409)
        self.configure()
        self.assertEqual(self.start(session_id, config_revision=revision)[0], 409)
        self.assertEqual(self.transport.calls, [])

    def test_teaching_guides_survive_provider_validation_and_rendering(self):
        # Geometry is a transport fixture, not a real critique of the synthetic upload.
        output = fixture()
        output['report']['visual_guides'] = [{
            'title': '位置示意', 'takeaway': '离线测试图解。', 'boundary': '不是对测试照片的实际判断。',
            'areas': [{'tone': 'accent', 'points': [{'x': .1, 'y': .1}, {'x': .2, 'y': .1}, {'x': .2, 'y': .3}]}],
            'lines': [], 'labels': [{'x': .4, 'y': .1, 'text': '测试区域', 'explanation': '测试标注的说明。'}],
        }]
        session_id = self.upload()
        self.configure()
        with patch(f'{__name__}.fixture', return_value=output):
            self.assertEqual(self.start(session_id)[0], 202)
            result = self.finish(session_id)
        self.assertEqual(result['state'], 'ready', result['error'])
        status, html, _ = self.request('GET', result['report_url'])
        self.assertEqual(status, 200)
        payload = json.loads(re.search(rb'<script id="reportData" type="application/json">(.*?)</script>', html, re.S)[1])
        self.assertEqual(payload['visual_guides'], output['report']['visual_guides'])
        self.assertEqual(payload['learning_check'], output['report']['learning_check'])
        self.assertIn('visual_guides', self.transport.calls[0]['instructions'])
        self.assertIn('learning_check', self.transport.calls[0]['instructions'])

    def test_http_to_provider_to_report_and_export(self):
        session_id = self.upload()
        self.configure()
        self.assertEqual(self.start(session_id, context='<script>not an instruction</script>')[0], 202)
        result = self.finish(session_id)
        self.assertEqual(result['state'], 'ready', result['error'])
        self.assertTrue(result['can_preview'])
        self.assertEqual(len(self.transport.calls), 1)
        request = self.transport.calls[0]
        self.assertFalse(request['store'])
        self.assertIn('references/evaluation-standard.md', request['instructions'])
        self.assertTrue(request['input'][0]['content'][1]['image_url'].startswith('data:image/jpeg;base64,'))
        status, html, _ = self.request('GET', result['report_url'])
        self.assertEqual(status, 200)
        payload = json.loads(re.search(rb'<script id="reportData" type="application/json">(.*?)</script>', html, re.S)[1])
        self.assertEqual(len(payload['scores']), 8)
        self.assertIsNone(payload['reference'])
        self.assertIn('尚未检索', payload['reference_status'])
        self.assertNotIn(str(self.data).encode(), html)
        self.assertNotIn(b'test-only-not-a-real-key', html)
        self.assertEqual(self.request('GET', result['report_url'].replace('index.html','assets/source.png'))[0], 200)
        status, archive, headers = self.request('GET', f'/export/{session_id}.zip')
        self.assertEqual(status, 200)
        with zipfile.ZipFile(io.BytesIO(archive)) as exported:
            self.assertIn('index.html', exported.namelist())
            self.assertIn('assets/source.png', exported.namelist())
            self.assertNotIn('session.json', exported.namelist())
        self.assertIn('attachment', headers['Content-Disposition'])

    def test_duplicate_clicks_and_repeat_critique_do_not_spend_twice(self):
        session_id = self.upload()
        self.configure()
        request_id = uuid.uuid4().hex
        self.assertEqual(self.start(session_id, request_id=request_id)[0], 202)
        self.assertEqual(self.start(session_id, request_id=request_id)[0], 202)
        self.finish(session_id)
        self.assertEqual(self.start(session_id, request_id=request_id)[0], 202)
        self.assertEqual(self.start(session_id)[0], 409)
        self.assertEqual(len(self.transport.calls), 1)

    def test_cancel_does_not_claim_remote_refund_or_allow_parallel_charge(self):
        session_id = self.upload()
        self.configure()
        self.transport.release.clear()
        self.start(session_id)
        self.assertTrue(self.transport.started.wait(2))
        status, result = self.json_request('POST', f'/api/sessions/{session_id}/cancel', {})
        self.assertEqual((status,result['state']), (200,'cancelled'))
        self.assertIn('计费', result['error'])
        self.assertEqual(self.start(session_id)[0], 409)
        self.assertEqual(self.request('POST', f'/api/sessions/{session_id}/archive', {})[0], 409)
        self.transport.release.set()
        result = self.finish(session_id)
        self.assertIsNone(result['report_url'])
        self.assertEqual(result['state'],'cancelled')
        self.assertEqual(len(self.transport.calls),1)

    def test_bad_model_output_does_not_fall_back_to_demo(self):
        session_id = self.upload()
        self.configure()
        self.transport.invalid = True
        self.start(session_id)
        result = self.finish(session_id)
        self.assertEqual(result['state'],'error')
        self.assertIsNone(result['report_url'])
        self.assertEqual(len(self.transport.calls),1)
        self.assertEqual(self.request('GET',result['original_url'])[0],200)

    def test_render_failure_preserves_reported_usage_without_retry(self):
        session_id = self.upload()
        self.configure()
        with patch.object(self.workbench, '_render', side_effect=OSError('private path must not be exposed')):
            self.start(session_id)
            result = self.finish(session_id)
        self.assertEqual(result['state'], 'error')
        self.assertIsNone(result['report_url'])
        self.assertEqual(result['usage'][0]['total_tokens'], 50)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertNotIn('private path', result['error'])

    def test_question_and_real_local_color_preview(self):
        session_id = self.upload()
        self.configure()
        self.start(session_id)
        first = self.finish(session_id)
        self.assertEqual(self.start(session_id, 'question', question='What about the dark areas?')[0],202)
        answered = self.finish(session_id)
        self.assertEqual(len(answered['messages']),1)
        self.assertEqual(first['report_url'],answered['report_url'])
        self.assertEqual(len(self.transport.calls),2)
        self.assertEqual(self.start(session_id, 'preview', consent=False)[0],202)
        edited = self.finish(session_id)
        self.assertEqual(edited['state'],'ready',edited['error'])
        self.assertTrue(edited['edited'])
        self.assertFalse(edited['can_preview'])
        self.assertEqual(len(self.transport.calls),2)
        self.assertNotEqual(edited['report_url'],first['report_url'])
        path = self.workbench.directory(session_id)
        with Image.open(path/'adjusted.color.jpg') as color, Image.open(path/'adjusted.treatment.jpg') as cropped:
            self.assertEqual(color.size,(80,60))
            self.assertEqual(cropped.size,(64,48))
        self.assertEqual((path/'original.png').read_bytes(),photo())

    def test_restart_recovers_without_automatic_charge_and_archive_is_recoverable(self):
        session_id = self.upload()
        session = self.workbench._load(session_id)
        session['state']='running'
        self.workbench._save(session)
        recovered=Workbench(self.data)
        self.assertEqual(recovered.get(session_id)['state'],'interrupted')
        self.assertFalse(recovered.configuration()['configured'])
        self.assertEqual(self.transport.calls,[])
        status, result=self.json_request('POST',f'/api/sessions/{session_id}/archive',{})
        self.assertEqual(status,200)
        self.assertIn('可恢复',result['message'])
        self.assertEqual(self.request('GET',f'/api/sessions/{session_id}')[0],404)
        saved=list((self.data/'trash').iterdir())
        self.assertEqual(len(saved),1)
        self.assertEqual((saved[0]/'original.png').read_bytes(),photo())

    def test_data_directory_cannot_claim_repo_or_unrelated_folder(self):
        for path in (ROOT, ROOT/'private-photos', Path.home()):
            with self.assertRaises(WorkbenchError):
                Workbench(path)
        unrelated=Path(self.temp.name).resolve()/'unrelated'
        unrelated.mkdir(mode=0o700)
        (unrelated/'user.txt').write_text('preserve')
        with self.assertRaises(WorkbenchError):
            Workbench(unrelated)
        self.assertEqual((unrelated/'user.txt').read_text(),'preserve')


if __name__ == '__main__':
    unittest.main()
