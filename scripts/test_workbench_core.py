"""Offline checks for experimental foundations, not workbench acceptance tests."""

from __future__ import annotations

import copy
import io
import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.contracts import (
    FAMILIES, ReportError, check_schema, critique_instructions, obj,
    public_report, rules_snapshot, validate_critique, validate_recipe,
)
from core.images import make_treatment, preview_bytes, read_photo
from core.provider import ProviderError, PublicHTTPSConnection, ResponsesProvider, request_bytes, validated_url
from test_render_visual_report import PNG_1X1, report_payload


def recipe() -> dict:
    return {
        'adjustments': [{
            'region': None, 'exposure': .25, 'contrast': 0, 'saturation': -.1,
            'warmth': .05, 'shadows': 0, 'highlights': 0,
            'reason': '让暗色与亮色的差别稍小，保留边缘位置。',
        }],
        'crop': {'x': .1, 'y': .1, 'width': .8, 'height': .8},
        'relationships': ['保留两块颜色的相对位置。', '暖色与冷色的距离稍有变化。'],
    }


class WorkbenchContractsTest(unittest.TestCase):
    def test_rules_are_loaded_from_shared_skill_sources(self) -> None:
        rules, revision = rules_snapshot()
        instructions, instruction_revision = critique_instructions()
        self.assertEqual(len(revision), 16)
        self.assertEqual(revision, instruction_revision)
        self.assertIn('references/evaluation-standard.md', rules)
        self.assertIn(rules, instructions)

    def test_schema_rejects_wrong_types_fields_and_nonfinite_values(self) -> None:
        schema = obj({'value': {'type': 'number'}})
        check_schema({'value': .5}, schema)
        for value in ({}, {'value': .5, 'extra': 1}, {'value': True}, {'value': float('nan')}):
            with self.subTest(value=value), self.assertRaises(ReportError):
                check_schema(value, schema)

    def test_recipe_limits_and_visible_relationships_are_enforced(self) -> None:
        validate_recipe(None)
        validate_recipe(recipe())
        for field, value in (('exposure', 2), ('warmth', .2), ('saturation', True)):
            invalid = recipe()
            invalid['adjustments'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ReportError):
                validate_recipe(invalid)
        for field, value in (('relationships', ['只有一处关系']),
                             ('crop', {'x': 0, 'y': 0, 'width': .4, 'height': .4})):
            invalid = recipe()
            invalid[field] = value
            with self.subTest(field=field), self.assertRaises(ReportError):
                validate_recipe(invalid)

    def test_critique_reuses_report_validation_without_inventing_a_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.png'
            source.write_bytes(PNG_1X1)
            report = report_payload(source)
            del report['source_image'], report['reference']
            report['decision'] = 'CONDITIONAL_BRANCH'
            report['integrity'] = [{'family': f, 'verdict': '观察', 'basis': '仍需回看原图。'} for f in FAMILIES]
            for observation in report['observations']:
                observation['regions'] = []
            payload = {'report': report, 'recipe': None, 'method_tags': ['明暗', '层次']}
            unchanged = copy.deepcopy(payload)
            validated = validate_critique(payload, source)
            self.assertIsNone(validated['reference'])
            self.assertTrue(validated['reference_status'])
            self.assertEqual(payload, unchanged)
            self.assertNotIn('source_image', public_report(validated))
            self.assertIsNone(public_report(None))
            payload['report']['scores'][0]['interval'] = '9-10 / 5'
            with self.assertRaises(ReportError):
                validate_critique(payload, source)


class WorkbenchProviderTest(unittest.TestCase):
    def test_provider_serializes_images_schema_and_usage_without_real_calls(self) -> None:
        schema = obj({'answer': {'type': 'string'}})
        result = {'status': 'completed', 'usage': {'input_tokens': 4, 'total_tokens': 6, 'private': 'omit'},
                  'output': [{'type': 'message', 'content': [{'type': 'output_text',
                              'text': '{"answer":"有依据的描述"}',
                              'annotations': [{'type': 'url_citation', 'url': 'https://example.com/work'}]}]}]}
        transport = Mock(return_value=(json.dumps(result).encode(), 'application/json'))
        provider = ResponsesProvider({'base_url': 'https://example.com/v1/', 'model': 'test-model',
                                      'api_key': 'test-key-not-a-secret'}, transport=transport)
        parsed, usage, citations = provider.generate(instructions='rules', text='photo', schema=schema,
                                                     images=[b'fixture'], search=True)
        url, method, body, headers = transport.call_args.args
        sent = json.loads(body)
        self.assertEqual((url, method), ('https://example.com/v1/responses', 'POST'))
        self.assertFalse(sent['store'])
        self.assertTrue(sent['text']['format']['strict'])
        self.assertEqual(sent['input'][0]['content'][1]['image_url'], 'data:image/jpeg;base64,Zml4dHVyZQ==')
        self.assertEqual(sent['tool_choice'], 'required')
        self.assertEqual(headers['Authorization'], 'Bearer test-key-not-a-secret')
        self.assertEqual(parsed['answer'], '有依据的描述')
        self.assertEqual(usage, {'input_tokens': 4, 'total_tokens': 6})
        self.assertEqual(citations, ['https://example.com/work'])
        transport.assert_called_once()

    def test_incomplete_refused_and_invalid_outputs_fail_without_retry(self) -> None:
        schema = obj({'answer': {'type': 'string'}})
        responses = [
            {'status': 'incomplete', 'usage': {'total_tokens': 3}},
            {'output': [{'content': [{'type': 'refusal', 'refusal': 'upstream detail'}]}]},
            {'output': [{'content': [{'type': 'output_text', 'text': '{"wrong":"upstream detail"}'}]}]},
            ['unexpected response'],
        ]
        for result in responses:
            transport = Mock(return_value=(json.dumps(result).encode(), 'application/json'))
            provider = ResponsesProvider({'base_url': 'https://example.com', 'model': 'test',
                                          'api_key': 'test-key-not-a-secret'}, transport=transport)
            with self.subTest(result=result), self.assertRaises(ProviderError) as raised:
                provider.generate(instructions='rules', text='photo', schema=schema)
            self.assertNotIn('upstream detail', str(raised.exception))
            self.assertNotIn('test-key', str(raised.exception))
            if isinstance(result, dict) and result.get('usage'):
                self.assertEqual(raised.exception.usage, {'total_tokens': 3})
            transport.assert_called_once()

    def test_urls_reject_private_credentials_and_unsafe_endpoints(self) -> None:
        for url in ('http://example.com', 'https://127.0.0.1', 'https://[::1]', 'https://10.0.0.1',
                    'https://host.local', 'https://localhost', 'https://user:pass@example.com',
                    'https://example.com:8443', 'https://example.com/../api', 'https://example.com?a=b'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validated_url(url, endpoint=True)
        self.assertEqual(validated_url('https://example.com/v1/', endpoint=True), 'https://example.com/v1')

    def test_mixed_private_dns_is_blocked_before_connecting(self) -> None:
        addresses = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443)),
                     (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))]
        with patch('core.provider.socket.getaddrinfo', return_value=addresses), \
                patch('core.provider.socket.create_connection') as connect:
            connection = PublicHTTPSConnection('example.com')
            with self.assertRaises(ProviderError):
                connection.connect()
            connect.assert_not_called()

    def test_transport_rejects_redirects_oversized_and_compressed_responses(self) -> None:
        for status, encoding, content in ((302, 'identity', b''), (200, 'identity', b'12345'),
                                          (200, 'gzip', b'')):
            response = Mock(status=status)
            response.getheader.side_effect = lambda name, default='', enc=encoding: enc if name == 'Content-Encoding' else default
            response.read.return_value = content
            connection = Mock()
            connection.getresponse.return_value = response
            with self.subTest(status=status, encoding=encoding), \
                    patch('core.provider.PublicHTTPSConnection', return_value=connection), \
                    self.assertRaises(ProviderError):
                request_bytes('https://example.com/image', limit=4)
            connection.request.assert_called_once()
            connection.close.assert_called_once()


class WorkbenchImagesTest(unittest.TestCase):
    def test_read_and_preview_handle_transparency_without_changing_source(self) -> None:
        image = Image.new('RGBA', (80, 40), (30, 100, 160, 0))
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        raw = buffer.getvalue()
        decoded, extension = read_photo(raw)
        self.assertEqual(extension, 'png')
        self.assertEqual(decoded.getpixel((0, 0)), (245, 245, 245))
        with Image.open(io.BytesIO(preview_bytes(decoded, side=32))) as preview:
            self.assertEqual(preview.size, (32, 16))
            self.assertFalse(preview.getexif())
        self.assertEqual(decoded.size, (80, 40))
        self.assertEqual(buffer.getvalue(), raw)

    def test_bad_unsupported_and_too_small_inputs_are_rejected(self) -> None:
        gif = io.BytesIO()
        Image.new('RGB', (40, 40)).save(gif, format='GIF')
        for raw in (b'', b'not an image', PNG_1X1, gif.getvalue()):
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                read_photo(raw)

    def test_color_and_crop_are_distinct_outputs_and_original_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'original.png'
            image = Image.new('RGB', (80, 60), (40, 100, 160))
            image.save(source)
            original = source.read_bytes()
            result = make_treatment(source, recipe(), root / 'preview')
            self.assertIsNotNone(result)
            self.assertGreater(result['mean_pixel_change'], .35)
            with Image.open(result['color_image']) as color, Image.open(result['treatment_image']) as cropped:
                self.assertEqual(color.size, image.size)
                self.assertEqual(cropped.size, (64, 48))
                self.assertIsNotNone(ImageChops.difference(image, color.convert('RGB')).getbbox())
            self.assertEqual(source.read_bytes(), original)

    def test_crop_only_does_not_masquerade_as_color_adjustment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'original.png'
            Image.new('RGB', (80, 60), (40, 100, 160)).save(source)
            value = recipe()
            value['adjustments'] = []
            self.assertIsNone(make_treatment(source, value, root / 'preview'))
            self.assertEqual(list(root.iterdir()), [source])


if __name__ == '__main__':
    unittest.main()
