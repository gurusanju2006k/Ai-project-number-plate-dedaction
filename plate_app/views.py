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
            format, imgstr = request.POST['captured_image'].split(';base64,')
            ext = format.split('/')[-1]
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


# 📊 HISTORY
@login_required
def history(request):
    data = History.objects.filter(user=request.user).order_by('-date')
    return render(request, 'history.html', {"data": data})