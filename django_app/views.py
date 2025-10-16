from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.conf import settings
import json
import os

from .models import ChartUpload, ChartAnalysis
from .ai_service import analyze_chart_image


def home(request):
    """
    Home page view showing recent chart analyses.
    """
    recent_charts = ChartUpload.objects.filter(analysis_status='completed')[:6]

    context = {
        'recent_charts': recent_charts,
        'title': 'Financial Horoscope - AI Chart Analysis'
    }
    return render(request, 'django_app/home.html', context)


def upload_chart(request):
    """
    Handle chart upload and display upload form.
    """
    if request.method == 'POST':
        return handle_chart_upload(request)

    context = {
        'title': 'Upload Chart for Analysis'
    }
    return render(request, 'django_app/upload.html', context)


def handle_chart_upload(request):
    """
    Handle the actual file upload and initiate analysis.
    """
    try:
        # Validate file upload
        if 'chart_image' not in request.FILES:
            messages.error(request, 'No file was uploaded.')
            return redirect('upload_chart')

        uploaded_file = request.FILES['chart_image']
        chart_name = request.POST.get('chart_name', '').strip()

        if not chart_name:
            chart_name = f"Chart {uploaded_file.name}"

        # Validate file type and size
        if not uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            messages.error(request, 'Please upload a PNG or JPEG image.')
            return redirect('upload_chart')

        if uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
            messages.error(request, 'File size must be less than 10MB.')
            return redirect('upload_chart')

        # Create chart upload record
        chart_upload = ChartUpload.objects.create(
            name=chart_name,
            image=uploaded_file,
            analysis_status='processing'
        )

        # Process analysis in background (synchronous for now)
        try:
            image_path = chart_upload.image.path
            analysis_results = analyze_chart_image(image_path)

            # Create analysis record
            ChartAnalysis.objects.create(
                chart=chart_upload,
                visual_description=analysis_results['visual_description'],
                pattern_analysis=analysis_results['pattern_analysis'],
                humorous_prediction=analysis_results['humorous_prediction'],
                technical_explanation=analysis_results['technical_explanation'],
                processing_time_seconds=analysis_results['processing_time_seconds'],
                confidence_score=analysis_results['confidence_score'],
                ai_model_used="gpt-4-vision-preview"
            )

            chart_upload.analysis_status = 'completed'
            chart_upload.save()

            messages.success(request, f'Chart "{chart_name}" has been analyzed successfully!')
            return redirect('view_analysis', chart_id=chart_upload.id)

        except Exception as e:
            chart_upload.analysis_status = 'failed'
            chart_upload.save()

            # Create a failure analysis record for debugging
            ChartAnalysis.objects.create(
                chart=chart_upload,
                visual_description=f"Analysis failed: {str(e)}",
                pattern_analysis="The 'System Error' pattern - very bearish for our servers.",
                humorous_prediction="Our AI crystal ball seems to have developed technical difficulties. Please try again!",
                technical_explanation=f"Error details: {str(e)}",
                processing_time_seconds=0,
                confidence_score=0.0,
                ai_model_used="error-handler-v1.0"
            )

            messages.error(request, f'Analysis failed: {str(e)}')
            return redirect('view_analysis', chart_id=chart_upload.id)

    except Exception as e:
        messages.error(request, f'Upload failed: {str(e)}')
        return redirect('upload_chart')


def view_analysis(request, chart_id):
    """
    Display the analysis results for a specific chart.
    """
    chart = get_object_or_404(ChartUpload, id=chart_id)

    try:
        analysis = chart.analysis
    except ChartAnalysis.DoesNotExist:
        analysis = None

    context = {
        'chart': chart,
        'analysis': analysis,
        'title': f'Analysis: {chart.name}'
    }
    return render(request, 'django_app/analysis.html', context)


def gallery(request):
    """
    Show gallery of all analyzed charts.
    """
    charts = ChartUpload.objects.all()

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['completed', 'processing', 'failed', 'pending']:
        charts = charts.filter(analysis_status=status_filter)

    context = {
        'charts': charts,
        'status_filter': status_filter,
        'title': 'Chart Gallery'
    }
    return render(request, 'django_app/gallery.html', context)


@require_http_methods(["GET"])
def api_analysis(request, chart_id):
    """
    API endpoint to get analysis results as JSON.
    """
    try:
        chart = get_object_or_404(ChartUpload, id=chart_id)

        response_data = {
            'chart': {
                'id': str(chart.id),
                'name': chart.name,
                'image_url': chart.image.url if chart.image else None,
                'uploaded_at': chart.uploaded_at.isoformat(),
                'analysis_status': chart.analysis_status,
            }
        }

        if hasattr(chart, 'analysis'):
            analysis = chart.analysis
            response_data['analysis'] = {
                'id': str(analysis.id),
                'visual_description': analysis.visual_description,
                'pattern_analysis': analysis.pattern_analysis,
                'humorous_prediction': analysis.humorous_prediction,
                'technical_explanation': analysis.technical_explanation,
                'created_at': analysis.created_at.isoformat(),
                'processing_time_seconds': analysis.processing_time_seconds,
                'confidence_score': analysis.confidence_score,
                'ai_model_used': analysis.ai_model_used,
            }
        else:
            response_data['analysis'] = None

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
