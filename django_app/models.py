from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import uuid


class ChartUpload(models.Model):
    """Model to store uploaded chart images"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Name of the chart")

    image = models.ImageField(
        upload_to='charts/',
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])],
        help_text="Upload PNG or JPEG chart image (max 10MB)"
    )

    uploaded_at = models.DateTimeField(default=timezone.now)

    # Analysis status
    ANALYSIS_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    analysis_status = models.CharField(
        max_length=20,
        choices=ANALYSIS_STATUS_CHOICES,
        default='pending'
    )

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Chart: {self.name} ({self.uploaded_at.strftime('%Y-%m-%d %H:%M')})"


class ChartAnalysis(models.Model):
    """Model to store AI-generated chart analysis"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chart = models.OneToOneField(ChartUpload, on_delete=models.CASCADE, related_name='analysis')

    # AI analysis results
    visual_description = models.TextField(help_text="AI's description of what it sees in the chart")
    pattern_analysis = models.TextField(help_text="Technical patterns identified (e.g., 'lion figure', 'head and shoulders')")
    humorous_prediction = models.TextField(help_text="Fun and humorous market prediction")
    technical_explanation = models.TextField(help_text="Mock-serious technical analysis explanation")

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    processing_time_seconds = models.FloatField(null=True, blank=True, help_text="Time taken to generate analysis")

    # AI model info
    ai_model_used = models.CharField(max_length=100, default="gpt-4o")
    confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence in analysis (0-1)")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Analysis for {self.chart.name}"
