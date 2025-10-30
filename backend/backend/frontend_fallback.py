import os
from django.conf import settings
from django.shortcuts import render
from datetime import datetime
from django.http import HttpResponse

def frontend_down(request):
    return render(request, "errors/maintenance.html", {"year": datetime.now().year}, status=503)

def serve_main(request):
    # locate the index.html file
    index_path = os.path.join(settings.BASE_DIR, 'frontend', 'index.html')
    
    # check if the file exists
    if not os.path.exists(index_path):
        # if not, render the frontend down page
        return render(request, "errors/maintenance.html", {"year": datetime.now().year}, status=503)
    
    # if it exists, serve the index.html file
    with open(index_path, encoding='utf-8') as f:
        html_content = f.read()
        return HttpResponse(html_content, content_type='text/html')