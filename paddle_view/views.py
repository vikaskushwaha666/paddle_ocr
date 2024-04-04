from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.apps import apps
import json
from django.views.decorators.clickjacking import xframe_options_exempt
import requests
import base64
import hmac
import hashlib
from io import BytesIO
import base64
from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
import io
import os
# Create your views here.


UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

def extract_text_and_coordinates(image_path):
    result = ocr.ocr(image_path, cls=False)
    
    text_areas = []
    for line in result:
        for word_box, word_info in line:
            # Extract coordinates
            x_min, y_min = word_box[0]
            x_max, y_max = word_box[2]  # Bottom-right corner
            
            # Calculate width and height
            width = x_max - x_min
            height = y_max - y_min
            
            text_areas.append({
                'left': x_min,
                'top': y_min,
                'width': width,
                'height': height,
                'text': word_info[0]
            })

    return text_areas

def index(request):
    return render(request, 'index.html')


@csrf_exempt
def upload(request):
    if request.method == 'POST' and 'file' in request.FILES:
        file = request.FILES['file']

        if file.name == '':
            return JsonResponse({'error': 'No selected file'})

        file_path = os.path.join(UPLOAD_FOLDER, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        text_areas = extract_text_and_coordinates(file_path)
        os.remove(file_path)

        return JsonResponse({'textAreas': text_areas})

    return JsonResponse({'error': 'No file part'})


@csrf_exempt
def fetch_image(request):
    data = json.loads(request.body)
    try:
        response = requests.get(data['img_url'])
        response.raise_for_status() 
        image_bytes_io = BytesIO(response.content)
        image = Image.open(image_bytes_io)
        image_format = image.format
        image_data = BytesIO()
        image.save(image_data, format=image_format)
        image_data.seek(0)

        text_areas = extract_text_and_coordinates(image_data.read())

        return JsonResponse({"textAreas":text_areas})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
