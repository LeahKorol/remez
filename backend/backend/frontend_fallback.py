import os
from django.conf import settings
from django.shortcuts import render
from datetime import datetime
from django.http import HttpResponse

FRONTEND_URL = getattr(settings, "FRONTEND_URL", "http://localhost:3000")


def frontend_down(request):
    return render(
        request, "errors/maintenance.html", {"year": datetime.now().year}, status=503
    )


def serve_main(request):
    # Path to the built frontend (adjust based on your build output)
    possible_paths = [
        os.path.join(
            settings.BASE_DIR.parent, "frontend", "dist", "index.html"
        ),  # Vite
        os.path.join(
            settings.BASE_DIR.parent, "frontend", "build", "index.html"
        ),  # React
        os.path.join(settings.BASE_DIR, "frontend", "index.html"),  # Custom location
    ]

    for index_path in possible_paths:
        if os.path.exists(index_path):
            try:
                with open(index_path, encoding="utf-8") as f:
                    html_content = f.read()
                    return HttpResponse(html_content, content_type="text/html")
            except Exception:
                pass

    # If no frontend found, show maintenance page
    return frontend_down(request)

    # # locate the index.html file
    # index_path = os.path.join(settings.BASE_DIR, 'frontend', 'index.html')

    # # check if the file exists
    # if not os.path.exists(index_path):
    #     # if not, render the frontend down page
    #     return render(request, "errors/maintenance.html", {"year": datetime.now().year}, status=503)

    # # if it exists, serve the index.html file
    # with open(index_path, encoding='utf-8') as f:
    #     html_content = f.read()
    #     return HttpResponse(html_content, content_type='text/html')
