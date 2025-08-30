from celery import shared_task
from django.contrib.auth import get_user_model
from .models import Query
from .email_service import EmailService
from .generate_ror_chart import generate_ror_chart_with_confidence_intervals
import os
import logging
from django.conf import settings
import time
import random

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True)
def process_query_analysis(self, query_id):
    """
    Async task to process query analysis and send email notification
    """
    try:
        # Get the query object
        query = Query.objects.get(id=query_id)
        user = query.user
        
        logger.info(f"Starting analysis for query {query_id}: {query.name}")
        
        # Update query status to processing
        query.status = 'processing'
        query.save()
        
        # Simulate processing time (15-30 minutes in production)
        # For testing, you can reduce this time
        total_processing_time = random.uniform(15 * 60, 30 * 60)  # 15-30 minutes
        
        # Step weights for realistic progress
        steps = [
            ("Validating query parameters", 0.05),
            ("Processing drug data", 0.15),
            ("Analyzing reactions", 0.15),
            ("Computing frequency analysis", 0.35),
            ("Generating visualization", 0.25),
            ("Preparing results", 0.05)
        ]
        
        current_progress = 0
        
        for step_name, weight in steps:
            step_duration = total_processing_time * weight
            logger.info(f"Processing step: {step_name} (duration: {step_duration:.2f}s)")
            
            # Update task progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'current_step': step_name,
                    'progress': current_progress,
                    'total_steps': len(steps)
                }
            )
            
            # Simulate processing time for this step
            time.sleep(step_duration)
            current_progress += weight * 100
        
        # Generate the actual ROR chart with confidence intervals
        chart_file_path, data_file_path = generate_ror_chart_with_confidence_intervals(query)
        
        # Update query with results
        query.status = 'completed'
        query.chart_file_path = chart_file_path
        query.data_file_path = data_file_path  # Store data path too
        query.save()
        
        # Send success email
        email_service = EmailService()
        chart_url = f"{settings.SITE_URL}/queries/{query_id}/results/"
        
        success = email_service.send_query_completion_email(
            user_email=user.email,
            query_name=query.name,
            chart_url=chart_url,
            chart_file_path=chart_file_path
        )
        
        if success:
            logger.info(f"Email sent successfully for query {query_id}")
        else:
            logger.error(f"Failed to send email for query {query_id}")
        
        return {
            'status': 'completed',
            'query_id': query_id,
            'chart_path': chart_file_path,
            'data_path': data_file_path,
            'email_sent': success
        }
        
    except Query.DoesNotExist:
        logger.error(f"Query {query_id} not found")
        return {'status': 'error', 'message': 'Query not found'}
        
    except Exception as e:
        logger.error(f"Error processing query {query_id}: {str(e)}")
        
        # Update query status to failed
        try:
            query = Query.objects.get(id=query_id)
            query.status = 'failed'
            query.error_message = str(e)
            query.save()
            
            # Send error email
            email_service = EmailService()
            email_service.send_query_error_email(
                user_email=query.user.email,
                query_name=query.name,
                error_message=str(e)
            )
            
        except Exception as email_error:
            logger.error(f"Failed to send error email: {str(email_error)}")
        
        return {'status': 'error', 'message': str(e)}