from venv import logger
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import os
import mimetypes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def serve_chart(request, query_id):
    """
    Serve the generated chart image for a query
    """
    try:
        query = get_object_or_404(Query, id=query_id, user=request.user)
        
        if query.status != 'completed' or not query.chart_file_path:
            return Response(
                {'error': 'Chart not available yet'}, 
                status=400
            )
        
        if not os.path.exists(query.chart_file_path):
            return Response(
                {'error': 'Chart file not found'}, 
                status=404
            )
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(query.chart_file_path)
        if not content_type:
            content_type = 'image/png'
        
        # Return the file
        response = FileResponse(
            open(query.chart_file_path, 'rb'),
            content_type=content_type
        )
        
        # Set filename for download
        filename = f"ror_chart_{query.name.replace(' ', '_')}.png"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving chart {query_id}: {str(e)}")
        raise Http404("Chart not found")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chart_data(request, query_id):
    """
    Get the raw data used to generate the chart
    """
    try:
        query = get_object_or_404(Query, id=query_id, user=request.user)
        
        if query.status != 'completed':
            return Response(
                {'error': 'Data not available yet'}, 
                status=400
            )
        
        # Check if data file exists
        if hasattr(query, 'data_file_path') and query.data_file_path and os.path.exists(query.data_file_path):
            import json
            with open(query.data_file_path, 'r') as f:
                chart_data = json.load(f)
            
            return Response({
                'query_id': query_id,
                'query_name': query.name,
                'chart_data': chart_data,
                'chart_url': f'/api/v1/queries/{query_id}/chart/'
            })
        else:
            # If no data file, return basic info
            return Response({
                'query_id': query_id,
                'query_name': query.name,
                'status': query.status,
                'chart_url': f'/api/v1/queries/{query_id}/chart/',
                'message': 'Raw data not available, but chart can be viewed'
            })
        
    except Exception as e:
        logger.error(f"Error getting chart data {query_id}: {str(e)}")
        return Response(
            {'error': 'Failed to get chart data'}, 
            status=500
        )

