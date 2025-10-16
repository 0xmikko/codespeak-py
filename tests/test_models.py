"""
Unit tests for models.py
"""

from django.test import TestCase
from django.utils import timezone
from datetime import datetime
import pytest
import uuid

from django_app.models import ChartUpload, ChartAnalysis


class TestChartUpload(TestCase):
    """Test kind: unit_tests. Original method FQN: ChartUpload.__str__"""

    @pytest.mark.timeout(30)
    def test_chart_upload_str_method(self):
        """Test ChartUpload __str__ method"""
        # Create a test datetime
        test_time = timezone.make_aware(datetime(2023, 12, 25, 14, 30, 45))

        # Create a ChartUpload instance without saving to DB
        chart = ChartUpload(
            name="Test Chart",
            uploaded_at=test_time
        )

        result = str(chart)
        expected = "Chart: Test Chart (2023-12-25 14:30)"

        self.assertEqual(result, expected)

    @pytest.mark.timeout(30)
    def test_chart_upload_str_method_different_time(self):
        """Test ChartUpload __str__ method with different time format"""
        test_time = timezone.make_aware(datetime(2024, 1, 1, 9, 5, 0))

        chart = ChartUpload(
            name="New Year Chart",
            uploaded_at=test_time
        )

        result = str(chart)
        expected = "Chart: New Year Chart (2024-01-01 09:05)"

        self.assertEqual(result, expected)

    @pytest.mark.timeout(30)
    def test_chart_upload_str_method_long_name(self):
        """Test ChartUpload __str__ method with a long name"""
        test_time = timezone.make_aware(datetime(2024, 6, 15, 23, 59, 59))
        long_name = "A Very Long Chart Name That Contains Multiple Words And Descriptions"

        chart = ChartUpload(
            name=long_name,
            uploaded_at=test_time
        )

        result = str(chart)
        expected = f"Chart: {long_name} (2024-06-15 23:59)"

        self.assertEqual(result, expected)

    @pytest.mark.timeout(30)
    def test_chart_upload_str_method_special_characters(self):
        """Test ChartUpload __str__ method with special characters in name"""
        test_time = timezone.make_aware(datetime(2024, 3, 14, 15, 9, 26))

        chart = ChartUpload(
            name="Chart with $pecial Ch@rs & Numbers 123!",
            uploaded_at=test_time
        )

        result = str(chart)
        expected = "Chart: Chart with $pecial Ch@rs & Numbers 123! (2024-03-14 15:09)"

        self.assertEqual(result, expected)


class TestChartAnalysis(TestCase):
    """Test kind: unit_tests. Original method FQN: ChartAnalysis.__str__"""

    @pytest.mark.timeout(30)
    def test_chart_analysis_str_method(self):
        """Test ChartAnalysis __str__ method"""
        # Create ChartUpload instance (without saving to DB)
        chart = ChartUpload(name="Test Chart")

        # Create ChartAnalysis instance (without saving to DB)
        analysis = ChartAnalysis(chart=chart)

        result = str(analysis)
        expected = "Analysis for Test Chart"

        self.assertEqual(result, expected)

    @pytest.mark.timeout(30)
    def test_chart_analysis_str_method_different_chart_name(self):
        """Test ChartAnalysis __str__ method with different chart name"""
        chart = ChartUpload(name="Bitcoin Weekly Analysis")
        analysis = ChartAnalysis(chart=chart)

        result = str(analysis)
        expected = "Analysis for Bitcoin Weekly Analysis"

        self.assertEqual(result, expected)

    @pytest.mark.timeout(30)
    def test_chart_analysis_str_method_empty_chart_name(self):
        """Test ChartAnalysis __str__ method with empty chart name"""
        chart = ChartUpload(name="")
        analysis = ChartAnalysis(chart=chart)

        result = str(analysis)
        expected = "Analysis for "

        self.assertEqual(result, expected)

    @pytest.mark.timeout(30)
    def test_chart_analysis_str_method_long_chart_name(self):
        """Test ChartAnalysis __str__ method with long chart name"""
        long_name = "Comprehensive Technical Analysis of S&P 500 Futures with Multiple Indicators"
        chart = ChartUpload(name=long_name)
        analysis = ChartAnalysis(chart=chart)

        result = str(analysis)
        expected = f"Analysis for {long_name}"

        self.assertEqual(result, expected)

    @pytest.mark.timeout(30)
    def test_chart_analysis_str_method_special_characters(self):
        """Test ChartAnalysis __str__ method with special characters in chart name"""
        chart = ChartUpload(name="EUR/USD Chart @2024 #TradingView")
        analysis = ChartAnalysis(chart=chart)

        result = str(analysis)
        expected = "Analysis for EUR/USD Chart @2024 #TradingView"

        self.assertEqual(result, expected)