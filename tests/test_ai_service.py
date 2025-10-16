"""
Unit tests for ai_service.py
"""

import os
import base64
import tempfile
import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import pytest
from django.test import TestCase

from django_app.ai_service import (
    ChartAnalysisService,
    _read_config_parameter,
    analyze_chart_image,
    create_analysis_prompt,
    encode_image,
    get_few_shot_examples
)


class TestReadConfigParameter(TestCase):
    """Test kind: unit_tests. Original method FQN: _read_config_parameter"""

    @pytest.mark.timeout(30)
    def test_read_config_parameter_from_env_local_file(self):
        """Test reading parameter from .env.local file"""
        with patch('django_app.ai_service.Path') as mock_path, \
             patch('django_app.ai_service.dotenv_values') as mock_dotenv_values, \
             patch.dict(os.environ, {}, clear=True):

            # Mock file exists and dotenv_values returns our parameter
            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file
            mock_dotenv_values.return_value = {'TEST_PARAM': 'env_local_value'}

            result = _read_config_parameter('test_param')

            self.assertEqual(result, 'env_local_value')
            mock_path.assert_called_once_with('.env.local')
            mock_dotenv_values.assert_called_once_with(mock_file)

    @pytest.mark.timeout(30)
    def test_read_config_parameter_from_environment(self):
        """Test reading parameter from environment when .env.local doesn't exist"""
        with patch('django_app.ai_service.Path') as mock_path, \
             patch('django_app.ai_service.dotenv_values') as mock_dotenv_values, \
             patch.dict(os.environ, {'TEST_PARAM': 'env_value'}, clear=True):

            # Mock file doesn't exist
            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_path.return_value = mock_file
            mock_dotenv_values.return_value = {}

            result = _read_config_parameter('test_param')

            self.assertEqual(result, 'env_value')

    @pytest.mark.timeout(30)
    def test_read_config_parameter_case_insensitive(self):
        """Test that parameter reading is case-insensitive"""
        with patch('django_app.ai_service.Path') as mock_path, \
             patch('django_app.ai_service.dotenv_values') as mock_dotenv_values, \
             patch.dict(os.environ, {}, clear=True):

            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file
            mock_dotenv_values.return_value = {'TEST_PARAM': 'value'}

            result = _read_config_parameter('test_param')

            self.assertEqual(result, 'value')

    @pytest.mark.timeout(30)
    def test_read_config_parameter_env_local_priority(self):
        """Test that .env.local takes priority over environment"""
        with patch('django_app.ai_service.Path') as mock_path, \
             patch('django_app.ai_service.dotenv_values') as mock_dotenv_values, \
             patch.dict(os.environ, {'TEST_PARAM': 'env_value'}, clear=True):

            mock_file = MagicMock()
            mock_file.exists.return_value = True
            mock_path.return_value = mock_file
            mock_dotenv_values.return_value = {'TEST_PARAM': 'env_local_value'}

            result = _read_config_parameter('test_param')

            self.assertEqual(result, 'env_local_value')

    @pytest.mark.timeout(30)
    def test_read_config_parameter_not_found(self):
        """Test when parameter is not found anywhere"""
        with patch('django_app.ai_service.Path') as mock_path, \
             patch('django_app.ai_service.dotenv_values') as mock_dotenv_values, \
             patch.dict(os.environ, {}, clear=True):

            mock_file = MagicMock()
            mock_file.exists.return_value = False
            mock_path.return_value = mock_file
            mock_dotenv_values.return_value = {}

            result = _read_config_parameter('nonexistent_param')

            self.assertIsNone(result)


class TestEncodeImage(TestCase):
    """Test kind: unit_tests. Original method FQN: encode_image"""

    @pytest.mark.timeout(30)
    def test_encode_image_success(self):
        """Test successful image encoding"""
        test_content = b"test image content"
        expected_encoded = base64.b64encode(test_content).decode('utf-8')

        with patch('builtins.open', mock_open(read_data=test_content)):
            result = encode_image('/test/image.jpg')

            self.assertEqual(result, expected_encoded)

    @pytest.mark.timeout(30)
    def test_encode_image_file_not_found(self):
        """Test behavior when image file doesn't exist"""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with self.assertRaises(FileNotFoundError):
                encode_image('/nonexistent/image.jpg')


class TestGetFewShotExamples(TestCase):
    """Test kind: unit_tests. Original method FQN: get_few_shot_examples"""

    @pytest.mark.timeout(30)
    def test_get_few_shot_examples_format(self):
        """Test that few-shot examples are formatted correctly"""
        with patch('django_app.ai_service.random.sample') as mock_sample:
            # Mock sample to return predictable examples
            mock_examples = [
                {
                    'visual_description': 'Test visual',
                    'pattern_analysis': 'Test pattern',
                    'humorous_prediction': 'Test prediction',
                    'technical_explanation': 'Test explanation'
                }
            ]
            mock_sample.return_value = mock_examples

            result = get_few_shot_examples()

            self.assertIn("Here are some examples of the style we want:", result)
            self.assertIn("Example 1:", result)
            self.assertIn("Visual Description: Test visual", result)
            self.assertIn("Pattern Analysis: Test pattern", result)
            self.assertIn("Humorous Prediction: Test prediction", result)
            self.assertIn("Technical Explanation: Test explanation", result)

    @pytest.mark.timeout(30)
    def test_get_few_shot_examples_sample_limit(self):
        """Test that sample is limited to 3 examples"""
        mock_examples = [
            {'visual_description': f'Visual {i}', 'pattern_analysis': f'Pattern {i}',
             'humorous_prediction': f'Prediction {i}', 'technical_explanation': f'Technical {i}'}
            for i in range(5)
        ]

        with patch('django_app.ai_service.random.sample') as mock_sample, \
             patch('django_app.ai_service.CHART_ANALYSIS_EXAMPLES', mock_examples):

            mock_sample.return_value = mock_examples[:3]  # Return first 3 examples

            get_few_shot_examples()

            # Should sample min(3, len(examples))
            mock_sample.assert_called_once_with(mock_examples, 3)


class TestCreateAnalysisPrompt(TestCase):
    """Test kind: unit_tests. Original method FQN: create_analysis_prompt"""

    @pytest.mark.timeout(30)
    def test_create_analysis_prompt_includes_examples(self):
        """Test that the prompt includes few-shot examples"""
        with patch('django_app.ai_service.get_few_shot_examples', return_value='Mock examples'):
            result = create_analysis_prompt()

            self.assertIn('Mock examples', result)
            self.assertIn('hilarious financial chart analyst', result)
            self.assertIn('Visual Description:', result)
            self.assertIn('Pattern Analysis:', result)
            self.assertIn('Humorous Prediction:', result)
            self.assertIn('Technical Explanation:', result)


class TestAnalyzeChartImage(TestCase):
    """Test kind: unit_tests. Original method FQN: analyze_chart_image"""

    @pytest.mark.timeout(30)
    def test_analyze_chart_image_creates_service_and_calls_analyze(self):
        """Test that analyze_chart_image creates service and calls analyze method"""
        mock_result = {'test': 'result'}

        with patch('django_app.ai_service.ChartAnalysisService') as mock_service_class:
            mock_service = MagicMock()
            mock_service.analyze_chart.return_value = mock_result
            mock_service_class.return_value = mock_service

            result = analyze_chart_image('/test/image.jpg')

            mock_service_class.assert_called_once()
            mock_service.analyze_chart.assert_called_once_with('/test/image.jpg')
            self.assertEqual(result, mock_result)


class TestChartAnalysisService(TestCase):
    """Test kind: unit_tests. Original method FQN: ChartAnalysisService.__init__ and ChartAnalysisService._parse_analysis_response"""

    @pytest.mark.timeout(30)
    def test_init_success(self):
        """Test successful service initialization"""
        with patch('django_app.ai_service._read_config_parameter', return_value='test-api-key'), \
             patch('django_app.ai_service.OpenAI') as mock_openai:

            service = ChartAnalysisService()

            self.assertEqual(service.api_key, 'test-api-key')
            mock_openai.assert_called_once_with(api_key='test-api-key')

    @pytest.mark.timeout(30)
    def test_init_no_api_key(self):
        """Test initialization failure when no API key is found"""
        with patch('django_app.ai_service._read_config_parameter', return_value=None):
            with self.assertRaises(ValueError) as context:
                ChartAnalysisService()

            self.assertIn('OPENAI_API_KEY not found', str(context.exception))

    @pytest.mark.timeout(30)
    def test_parse_analysis_response_complete(self):
        """Test parsing a complete AI response"""
        service = ChartAnalysisService.__new__(ChartAnalysisService)  # Skip __init__

        response_content = """Visual Description: Test visual description
Pattern Analysis: Test pattern analysis
Humorous Prediction: Test humorous prediction
Technical Explanation: Test technical explanation"""

        result = service._parse_analysis_response(response_content)

        expected = {
            'visual_description': 'Test visual description',
            'pattern_analysis': 'Test pattern analysis',
            'humorous_prediction': 'Test humorous prediction',
            'technical_explanation': 'Test technical explanation'
        }

        self.assertEqual(result, expected)

    @pytest.mark.timeout(30)
    def test_parse_analysis_response_multiline(self):
        """Test parsing response with multiline content"""
        service = ChartAnalysisService.__new__(ChartAnalysisService)  # Skip __init__

        response_content = """Visual Description: First line
Second line of description

Pattern Analysis: Pattern line 1
Pattern line 2

Humorous Prediction: Funny prediction

Technical Explanation: Technical line 1
Technical line 2"""

        result = service._parse_analysis_response(response_content)

        self.assertEqual(result['visual_description'], 'First line Second line of description')
        self.assertEqual(result['pattern_analysis'], 'Pattern line 1 Pattern line 2')

    @pytest.mark.timeout(30)
    def test_parse_analysis_response_missing_sections(self):
        """Test parsing response with missing sections"""
        service = ChartAnalysisService.__new__(ChartAnalysisService)  # Skip __init__

        response_content = """Visual Description: Only this section exists"""

        result = service._parse_analysis_response(response_content)

        self.assertEqual(result['visual_description'], 'Only this section exists')
        # Missing sections should be filled with default text
        self.assertIn('speechless', result['pattern_analysis'])
        self.assertIn('speechless', result['humorous_prediction'])
        self.assertIn('speechless', result['technical_explanation'])

    @pytest.mark.timeout(30)
    def test_parse_analysis_response_parse_error(self):
        """Test parsing when an exception occurs during splitting"""
        service = ChartAnalysisService.__new__(ChartAnalysisService)  # Skip __init__

        # Simulate parsing error by patching split method
        original_method = service._parse_analysis_response

        def mock_parse_with_error(content):
            # Simulate an error in the parsing logic
            try:
                # Force an error during processing
                raise Exception('Parse error')
            except Exception:
                # This should trigger the exception handling in the method
                return original_method(content)

        # Patch the split method to cause an error
        with patch.object(str, 'split', side_effect=Exception('Parse error')):
            result = service._parse_analysis_response('any content')

        # Should handle the error gracefully
        self.assertEqual(result['visual_description'], 'any content')
        self.assertIn('Parsing Error', result['pattern_analysis'])

    @pytest.mark.timeout(30)
    def test_parse_analysis_response_empty_fields(self):
        """Test that empty fields get filled with default text"""
        service = ChartAnalysisService.__new__(ChartAnalysisService)  # Skip __init__

        response_content = """Visual Description:
Pattern Analysis: Some content
Humorous Prediction:
Technical Explanation: """

        result = service._parse_analysis_response(response_content)

        # Empty fields should be filled
        self.assertIn('speechless', result['visual_description'])
        self.assertEqual(result['pattern_analysis'], 'Some content')
        self.assertIn('speechless', result['humorous_prediction'])
        self.assertIn('speechless', result['technical_explanation'])


class TestChartAnalysisServiceExternalAPI(TestCase):
    """Test kind: external_api_tests. Original method FQN: ChartAnalysisService.analyze_chart"""

    @pytest.mark.timeout(30)
    def test_analyze_chart_real_api_call(self):
        """Test real API call to OpenAI (requires valid API key)"""
        # Skip if no API key is available
        api_key = _read_config_parameter('OPENAI_API_KEY')
        if not api_key:
            self.skipTest("OPENAI_API_KEY not found - skipping external API test")

        # Create a simple test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            # Create a minimal JPEG-like content (not a real image, but will work for base64 encoding)
            temp_file.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C\x00')
            temp_path = temp_file.name

        try:
            service = ChartAnalysisService()

            # This will make an actual API call
            result = service.analyze_chart(temp_path)

            # Verify the structure of the response
            expected_keys = {
                'visual_description', 'pattern_analysis', 'humorous_prediction',
                'technical_explanation', 'processing_time_seconds', 'confidence_score'
            }
            self.assertEqual(set(result.keys()), expected_keys)

            # All text fields should be non-empty strings
            for key in ['visual_description', 'pattern_analysis', 'humorous_prediction', 'technical_explanation']:
                self.assertIsInstance(result[key], str)
                self.assertTrue(len(result[key]) > 0)

            # Numeric fields should be valid
            self.assertIsInstance(result['processing_time_seconds'], (int, float))
            self.assertIsInstance(result['confidence_score'], (int, float))
            self.assertGreaterEqual(result['processing_time_seconds'], 0)
            self.assertGreaterEqual(result['confidence_score'], 0)
            self.assertLessEqual(result['confidence_score'], 1)

        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)