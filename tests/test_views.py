"""
Endpoint tests for views.py
"""

import json
import tempfile
import uuid
from io import BytesIO
from unittest.mock import patch, MagicMock

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from PIL import Image

from django_app.models import ChartUpload, ChartAnalysis


class TestHomeView(TestCase):
    """Test kind: endpoint_tests. Original method FQN: home"""

    @pytest.mark.timeout(30)
    def setUp(self):
        self.client = Client()

    @pytest.mark.timeout(30)
    def test_home_view_get(self):
        """Test GET request to home view"""
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Financial Horoscope - AI Chart Analysis')
        self.assertIn('recent_charts', response.context)
        self.assertIn('title', response.context)

    @pytest.mark.timeout(30)
    def test_home_view_with_completed_charts(self):
        """Test home view displays completed charts"""
        # Create test chart data
        chart1 = ChartUpload.objects.create(
            name="Test Chart 1",
            analysis_status='completed'
        )
        chart2 = ChartUpload.objects.create(
            name="Test Chart 2",
            analysis_status='processing'
        )
        chart3 = ChartUpload.objects.create(
            name="Test Chart 3",
            analysis_status='completed'
        )

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        recent_charts = response.context['recent_charts']

        # Should only show completed charts
        self.assertEqual(len(recent_charts), 2)
        chart_names = [chart.name for chart in recent_charts]
        self.assertIn("Test Chart 1", chart_names)
        self.assertIn("Test Chart 3", chart_names)
        self.assertNotIn("Test Chart 2", chart_names)

    @pytest.mark.timeout(30)
    def test_home_view_chart_limit(self):
        """Test home view limits charts to 6"""
        # Create 10 completed charts
        for i in range(10):
            ChartUpload.objects.create(
                name=f"Chart {i}",
                analysis_status='completed'
            )

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        recent_charts = response.context['recent_charts']
        self.assertEqual(len(recent_charts), 6)


class TestUploadChartView(TestCase):
    """Test kind: endpoint_tests. Original method FQN: upload_chart"""

    @pytest.mark.timeout(30)
    def setUp(self):
        self.client = Client()

    @pytest.mark.timeout(30)
    def test_upload_chart_get(self):
        """Test GET request to upload_chart view"""
        response = self.client.get(reverse('upload_chart'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload Chart for Analysis')
        self.assertEqual(response.context['title'], 'Upload Chart for Analysis')

    @pytest.mark.timeout(30)
    def test_upload_chart_post_redirects_to_handle(self):
        """Test POST request to upload_chart redirects to handle_chart_upload"""
        # Create a simple test image
        image = BytesIO()
        img = Image.new('RGB', (100, 100), color='red')
        img.save(image, 'JPEG')
        image.seek(0)

        uploaded_file = SimpleUploadedFile(
            "test.jpg",
            image.getvalue(),
            content_type="image/jpeg"
        )

        with patch('django_app.views.handle_chart_upload') as mock_handle:
            mock_handle.return_value = MagicMock()

            response = self.client.post(reverse('upload_chart'), {
                'chart_image': uploaded_file,
                'chart_name': 'Test Chart'
            })

            mock_handle.assert_called_once()


class TestHandleChartUploadView(TestCase):
    """Test kind: endpoint_tests. Original method FQN: handle_chart_upload"""

    @pytest.mark.timeout(30)
    def setUp(self):
        self.client = Client()

    def _create_test_image(self):
        """Helper to create a test image file"""
        image = BytesIO()
        img = Image.new('RGB', (100, 100), color='red')
        img.save(image, 'JPEG')
        image.seek(0)
        return SimpleUploadedFile(
            "test.jpg",
            image.getvalue(),
            content_type="image/jpeg"
        )

    @pytest.mark.timeout(30)
    def test_handle_chart_upload_no_file(self):
        """Test upload without file"""
        response = self.client.post(reverse('upload_chart'), {
            'chart_name': 'Test Chart'
        })

        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('No file was uploaded' in str(m) for m in messages))

    @pytest.mark.timeout(30)
    def test_handle_chart_upload_invalid_file_type(self):
        """Test upload with invalid file type"""
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"not an image",
            content_type="text/plain"
        )

        response = self.client.post(reverse('upload_chart'), {
            'chart_image': invalid_file,
            'chart_name': 'Test Chart'
        })

        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('PNG or JPEG' in str(m) for m in messages))

    @pytest.mark.timeout(30)
    def test_handle_chart_upload_file_too_large(self):
        """Test upload with file too large"""
        # Create a large file (simulate > 10MB)
        large_file = SimpleUploadedFile(
            "test.jpg",
            b"x" * (11 * 1024 * 1024),  # 11MB
            content_type="image/jpeg"
        )

        response = self.client.post(reverse('upload_chart'), {
            'chart_image': large_file,
            'chart_name': 'Test Chart'
        })

        self.assertEqual(response.status_code, 302)  # Redirect
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('less than 10MB' in str(m) for m in messages))

    @pytest.mark.timeout(30)
    def test_handle_chart_upload_success(self):
        """Test successful chart upload"""
        uploaded_file = self._create_test_image()

        with patch('django_app.views.analyze_chart_image') as mock_analyze:
            mock_analyze.return_value = {
                'visual_description': 'Test description',
                'pattern_analysis': 'Test pattern',
                'humorous_prediction': 'Test prediction',
                'technical_explanation': 'Test explanation',
                'processing_time_seconds': 1.5,
                'confidence_score': 0.9
            }

            response = self.client.post(reverse('upload_chart'), {
                'chart_image': uploaded_file,
                'chart_name': 'Test Chart'
            })

            self.assertEqual(response.status_code, 302)  # Redirect to analysis

            # Check that chart was created
            chart = ChartUpload.objects.get(name='Test Chart')
            self.assertEqual(chart.analysis_status, 'completed')

            # Check that analysis was created
            analysis = ChartAnalysis.objects.get(chart=chart)
            self.assertEqual(analysis.visual_description, 'Test description')

    @pytest.mark.timeout(30)
    def test_handle_chart_upload_default_name(self):
        """Test upload with default chart name"""
        uploaded_file = self._create_test_image()

        with patch('django_app.views.analyze_chart_image') as mock_analyze:
            mock_analyze.return_value = {
                'visual_description': 'Test',
                'pattern_analysis': 'Test',
                'humorous_prediction': 'Test',
                'technical_explanation': 'Test',
                'processing_time_seconds': 1.0,
                'confidence_score': 0.8
            }

            response = self.client.post(reverse('upload_chart'), {
                'chart_image': uploaded_file,
                'chart_name': ''  # Empty name
            })

            chart = ChartUpload.objects.first()
            self.assertIn('Chart test.jpg', chart.name)

    @pytest.mark.timeout(30)
    def test_handle_chart_upload_analysis_error(self):
        """Test upload when analysis fails"""
        uploaded_file = self._create_test_image()

        with patch('django_app.views.analyze_chart_image') as mock_analyze:
            mock_analyze.side_effect = Exception('Analysis failed')

            response = self.client.post(reverse('upload_chart'), {
                'chart_image': uploaded_file,
                'chart_name': 'Test Chart'
            })

            self.assertEqual(response.status_code, 302)  # Still redirects

            # Check that chart was marked as failed
            chart = ChartUpload.objects.get(name='Test Chart')
            self.assertEqual(chart.analysis_status, 'failed')

            # Check that error analysis was created
            analysis = ChartAnalysis.objects.get(chart=chart)
            self.assertIn('Analysis failed', analysis.visual_description)


class TestViewAnalysisView(TestCase):
    """Test kind: endpoint_tests. Original method FQN: view_analysis"""

    @pytest.mark.timeout(30)
    def setUp(self):
        self.client = Client()
        self.chart = ChartUpload.objects.create(name="Test Chart")

    @pytest.mark.timeout(30)
    def test_view_analysis_with_analysis(self):
        """Test viewing analysis when analysis exists"""
        analysis = ChartAnalysis.objects.create(
            chart=self.chart,
            visual_description="Test description",
            pattern_analysis="Test pattern",
            humorous_prediction="Test prediction",
            technical_explanation="Test explanation"
        )

        response = self.client.get(reverse('view_analysis', args=[self.chart.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['chart'], self.chart)
        self.assertEqual(response.context['analysis'], analysis)
        self.assertEqual(response.context['title'], f'Analysis: {self.chart.name}')

    @pytest.mark.timeout(30)
    def test_view_analysis_without_analysis(self):
        """Test viewing analysis when no analysis exists"""
        response = self.client.get(reverse('view_analysis', args=[self.chart.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['chart'], self.chart)
        self.assertIsNone(response.context['analysis'])

    @pytest.mark.timeout(30)
    def test_view_analysis_chart_not_found(self):
        """Test viewing analysis for non-existent chart"""
        non_existent_id = uuid.uuid4()
        response = self.client.get(reverse('view_analysis', args=[non_existent_id]))

        self.assertEqual(response.status_code, 404)


class TestGalleryView(TestCase):
    """Test kind: endpoint_tests. Original method FQN: gallery"""

    @pytest.mark.timeout(30)
    def setUp(self):
        self.client = Client()

    @pytest.mark.timeout(30)
    def test_gallery_view_all_charts(self):
        """Test gallery view shows all charts"""
        chart1 = ChartUpload.objects.create(name="Chart 1", analysis_status='completed')
        chart2 = ChartUpload.objects.create(name="Chart 2", analysis_status='processing')
        chart3 = ChartUpload.objects.create(name="Chart 3", analysis_status='failed')

        response = self.client.get(reverse('gallery'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['title'], 'Chart Gallery')
        self.assertIsNone(response.context['status_filter'])

        charts = response.context['charts']
        self.assertEqual(len(charts), 3)

    @pytest.mark.timeout(30)
    def test_gallery_view_filter_by_status(self):
        """Test gallery view with status filter"""
        ChartUpload.objects.create(name="Chart 1", analysis_status='completed')
        ChartUpload.objects.create(name="Chart 2", analysis_status='processing')
        ChartUpload.objects.create(name="Chart 3", analysis_status='completed')

        response = self.client.get(reverse('gallery'), {'status': 'completed'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['status_filter'], 'completed')

        charts = response.context['charts']
        self.assertEqual(len(charts), 2)

        for chart in charts:
            self.assertEqual(chart.analysis_status, 'completed')

    @pytest.mark.timeout(30)
    def test_gallery_view_invalid_status_filter(self):
        """Test gallery view ignores invalid status filter"""
        ChartUpload.objects.create(name="Chart 1", analysis_status='completed')

        response = self.client.get(reverse('gallery'), {'status': 'invalid_status'})

        self.assertEqual(response.status_code, 200)
        # Invalid status should be ignored, so no filtering
        self.assertIsNone(response.context['status_filter'])

    @pytest.mark.timeout(30)
    def test_gallery_view_valid_status_filters(self):
        """Test gallery view with all valid status filters"""
        ChartUpload.objects.create(name="Chart 1", analysis_status='completed')
        ChartUpload.objects.create(name="Chart 2", analysis_status='processing')
        ChartUpload.objects.create(name="Chart 3", analysis_status='failed')
        ChartUpload.objects.create(name="Chart 4", analysis_status='pending')

        valid_statuses = ['completed', 'processing', 'failed', 'pending']

        for status in valid_statuses:
            with self.subTest(status=status):
                response = self.client.get(reverse('gallery'), {'status': status})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['status_filter'], status)

                charts = response.context['charts']
                self.assertEqual(len(charts), 1)
                self.assertEqual(charts[0].analysis_status, status)


class TestApiAnalysisView(TestCase):
    """Test kind: endpoint_tests. Original method FQN: api_analysis"""

    @pytest.mark.timeout(30)
    def setUp(self):
        self.client = Client()
        self.chart = ChartUpload.objects.create(
            name="Test Chart",
            analysis_status='completed'
        )

    @pytest.mark.timeout(30)
    def test_api_analysis_with_analysis(self):
        """Test API endpoint with existing analysis"""
        analysis = ChartAnalysis.objects.create(
            chart=self.chart,
            visual_description="API test description",
            pattern_analysis="API test pattern",
            humorous_prediction="API test prediction",
            technical_explanation="API test explanation",
            processing_time_seconds=2.5,
            confidence_score=0.95,
            ai_model_used="gpt-4-vision-preview"
        )

        response = self.client.get(reverse('api_analysis', args=[self.chart.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = json.loads(response.content)

        # Check chart data
        self.assertEqual(data['chart']['name'], 'Test Chart')
        self.assertEqual(data['chart']['analysis_status'], 'completed')

        # Check analysis data
        self.assertIsNotNone(data['analysis'])
        self.assertEqual(data['analysis']['visual_description'], 'API test description')
        self.assertEqual(data['analysis']['processing_time_seconds'], 2.5)
        self.assertEqual(data['analysis']['confidence_score'], 0.95)

    @pytest.mark.timeout(30)
    def test_api_analysis_without_analysis(self):
        """Test API endpoint without analysis"""
        response = self.client.get(reverse('api_analysis', args=[self.chart.id]))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['chart']['name'], 'Test Chart')
        self.assertIsNone(data['analysis'])

    @pytest.mark.timeout(30)
    def test_api_analysis_chart_not_found(self):
        """Test API endpoint with non-existent chart"""
        non_existent_id = uuid.uuid4()
        response = self.client.get(reverse('api_analysis', args=[non_existent_id]))

        self.assertEqual(response.status_code, 404)

    @pytest.mark.timeout(30)
    def test_api_analysis_invalid_method(self):
        """Test API endpoint with invalid HTTP method"""
        response = self.client.post(reverse('api_analysis', args=[self.chart.id]))

        self.assertEqual(response.status_code, 405)  # Method not allowed

    @pytest.mark.timeout(30)
    def test_api_analysis_json_serialization(self):
        """Test API endpoint JSON serialization of dates and UUIDs"""
        analysis = ChartAnalysis.objects.create(
            chart=self.chart,
            visual_description="Test",
            pattern_analysis="Test",
            humorous_prediction="Test",
            technical_explanation="Test"
        )

        response = self.client.get(reverse('api_analysis', args=[self.chart.id]))

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        # Check that UUIDs are serialized as strings
        self.assertIsInstance(data['chart']['id'], str)
        self.assertIsInstance(data['analysis']['id'], str)

        # Check that datetimes are serialized as ISO format
        self.assertIn('T', data['chart']['uploaded_at'])  # ISO format contains T
        self.assertIn('T', data['analysis']['created_at'])  # ISO format contains T