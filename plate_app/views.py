from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .ai_model import process_image
from .models import History

import base64
from django.core.files.base import ContentFile


# 🔐 REGISTER
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "User already exists"})

        User.objects.create_user(username=username, password=password)
        return redirect('/login/')

    return render(request, "register.html")


# 🏠 HOME
def home(request):
    return render(request, 'home.html')


# 🔐 LOGIN
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return redirect('/detect/')
        else:
            return render(request, 'login.html', {"error": "Invalid credentials"})

    return render(request, 'login.html')


# 🚪 LOGOUT
def logout_view(request):
    logout(request)
    return redirect('/login/')


# 🤖 DETECT NUMBER PLATE (FIXED 🔥)
@login_required
def detect_plate(request):
    if request.method == 'POST':

        # ✅ CASE 1: IMAGE FROM FILE UPLOAD
        if request.FILES.get('image'):
            image = request.FILES['image']

        # ✅ CASE 2: IMAGE FROM CAMERA (BASE64)
        elif request.POST.get('captured_image'):
            captured = request.POST.get('captured_image', '')

            imgstr = None

            if captured and ';base64,' in captured:
                imgstr = captured.split(';base64,')[1]
            ext = captured.split('/')[-1]
            image = ContentFile(base64.b64decode(imgstr), name='captured.' + ext)

        # ❌ NO IMAGE
        else:
            return render(request, 'detect.html', {'error': 'No image provided'})

        # 💾 SAVE IMAGE
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        file_path = fs.path(filename)

        # 🤖 PROCESS IMAGE
        result = process_image(file_path)

        # ✅ SUCCESS
        if result.get("status"):
            History.objects.create(
                user=request.user,
                image=filename,
                plate=result.get("plate"),
                state=result.get("state"),
                confidence=result.get("confidence")
            )

            context = {
                "image_url": fs.url(filename),
                "plate": result.get("plate"),
                "state": result.get("state"),
                "confidence": result.get("confidence")
            }

        # ❌ FAILURE
        else:
            context = {
                "image_url": fs.url(filename),
                "error": result.get("message", "Detection failed")
            }

        return render(request, 'result.html', context)

    return render(request, 'detect.html')
import cv2
import base64
import numpy as np
from .ai_model import process_image

def detect_frame(request):
    return render(request, "live.html")

import json
from django.http import JsonResponse
import base64
import numpy as np
import cv2
from .ai_model import process_image, process_image_from_array

def process_frame(request):

    data = json.loads(request.body)
    image_data = data['image']

    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    result = process_image_from_array(img)

    return JsonResponse(result)

# 📊 HISTORY
@login_required
def history(request):
    data = History.objects.filter(user=request.user).order_by('-date')
    return render(request, 'history.html', {"data": data})