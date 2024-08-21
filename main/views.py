from django.shortcuts import render, redirect, get_object_or_404
from . import models
from django.core.paginator import Paginator
# Create your views here.
import requests
import random
from django.db.models.functions import Random
from django.contrib.auth.models import User
# Replace 'YOUR_UNSPLASH_ACCESS_KEY' with your Unsplash Access Key
import secrets
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import boto3
from django.db.models import Count
from instagrapi import Client
from io import BytesIO
from PIL import Image
### PUT THE AWS CODE ASAP

###

def hide_email(email):
    let_len = len(email)-12
    return email[:4]+('*'*let_len)+email[-9:]

def token_gen():
    return secrets.token_urlsafe(32)

def send_email(token, reciever):
    subject = 'Activate Uzbexposure account'
    message = f'Go to the website to activate your account: http://127.0.0.1:8000/activate/{token}'
    from_email = 'zaynobiddinshaxobiddinov9999@gmail.com'
    recipient_list = [f'{reciever}']
    send_mail(subject, message, from_email, recipient_list)


def fetch(request):
        images = models.Images.objects.all().order_by('-id')
        if request.user.is_superuser:
            access_key = 'jBrWtxyJmq8DvExdDtqNEEV0-iLHXPTOKMc7Of1XXw0'
            if request.method == 'POST':
                name = request.POST['name']
                query = name # Your search query
                url = f'https://api.unsplash.com/search/photos?query={query}&client_id={access_key}'
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for HTTP errors
                data = response.json()  # Parse JSON response
                for i in data['results']:
                    
                    if not models.Images.objects.filter(url =  i['urls']['regular']).first():
                        print(i['urls']['regular'])
                        models.Images.objects.create(
                            url = i['urls']['regular'],
                            description = i['description']
                        )
                return redirect('fetch')
        else:
            return redirect('main')
        return render(request,'fetch.html', {'images':images})

def get_pixabay(request):
    if request.method == "POST":
        name = request.POST['name']
         # Define your API key and the base URL for the Pixabay API
        api_key = '45382217-0b03ba2cf08344723ff5c0f96'
        url = 'https://pixabay.com/api/'

        # Parameters for the API request
        params = {
            'key': api_key,
            'q': name,  # Search keyword
            'image_type': 'photo',
            'per_page': 10,  # Number of results per page
}
        # Make the API request
        response = requests.get(url, params=params)
        for i in response.json()['hits']:
            models.Images.objects.create(
                 url = i['largeImageURL']
            )
        return redirect('fetch')

def main(request):
    all_images = models.Images.objects.filter(is_active = True).order_by('?')
    main_four = all_images[:4]
    page_number = int(request.GET.get('page', 1))
    paginator = Paginator(all_images, 10)
    images = paginator.get_page(page_number)

    context = {
        'images': images,
        'four': main_four
    }
    print(request.user)
    return render(request, 'index.html', context)

def delete_image_fetch(request, id):
     image = models.Images.objects.get(id = id)
     image.delete()
     return redirect('fetch')

def contribute(request):
     random_image = models.Images.objects.all().order_by('?').first
     return render(request, 'contribute.html', {'random':random_image})

def signup(request):
     random_image = models.Images.objects.all().order_by('?').first
     message = 'None'
     if request.method == 'POST':
          name = request.POST['user']
          email = request.POST['email']
          password = request.POST['password']
          password2 = request.POST['password2']
          if not User.objects.filter(email = email).first():
            if password2 == password:
                user = User.objects.create_user(
                    first_name= name,
                    email = email,
                    password = password,
                    username = token_gen()
                )
                user.is_active = False
                user.save()
                send_email(user.username, email)
                return redirect('req_verify')
            else:
                message = 'Make sure that two passwords are identical'
          else:
              message = 'This email is already registred. Try logging in'
     return render(request, 'signup.html', {'random':random_image, 'message':message})

def req_verify(request):
    return render(request, 'alert-verify.html')

def activate(request, slug):
    user = User.objects.get(username = slug)
    user.is_active = True
    user.save()
    return redirect('login')

def login_user(request):
    random_image = models.Images.objects.all().order_by('?').first()
    error = 'None'
    
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        try:
            # Get the username based on the provided email
            user = User.objects.get(email=email)
            username = user.username
            
            # Check if the user is active (i.e., has verified their email)
            if user.is_active:
                # Authenticate the user
                authenticated_user = authenticate(request, username=username, password=password)
                
                if authenticated_user is not None:
                    # Log the user in and redirect to the main page
                    login(request, authenticated_user)
                    return redirect('main')
                else:
                    error = 'Incorrect email or password'
            else:
                error = 'You have registered, but your account is not verified. Please check your email to verify your account.'
        
        except User.DoesNotExist:
            error = 'No account found with this email.'

    return render(request, 'login.html', {'error': error, 'random': random_image})


def upload_to_server(image, name):
    s3_client = boto3.client(
        service_name='s3',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    # Upload the file with public-read access
    s3_client.upload_fileobj(
        image,
        AWS_S3_BUCKET_NAME,
        name,
        ExtraArgs={'ACL': 'public-read'}
    )

    # Construct the URL
    url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{name}"
    return url

@login_required(login_url = 'login')
def upload(request):
    if request.method == "POST":
        image = request.FILES['image']
        description = request.POST['description']
        filetype = ''
        for i in str(image.name)[::-1]:
            if i != '.':
                filetype+=i
            else:
                break
        filename = str(token_gen()+'.'+filetype[::-1])
        print(filename)
        print(type(filename))

        url = upload_to_server(image = image, name = filename)
        

        models.Images.objects.create(
            url = url,
            description = description,
            is_active = False,
            author = request.user
        )
    return render(request, 'upload.html')

@login_required(login_url='login')
def dashboard(request):
    print(request.user.is_superuser)
    if request.user.is_superuser:
        images = models.Images.objects.filter(is_active = False)
    else:
        images = models.Images.objects.filter(author = request.user).order_by('-id')
    page_number = int(request.GET.get('page', 1))
    paginator = Paginator(images, 8)
    images = paginator.get_page(page_number)

    context = {'images':images}

    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def delete_image(request, id):
    image = models.Images.objects.get(id = id)
    image.delete()
    return redirect('dashboard')

@login_required(login_url='login')
def accept_image(request, id):
    if request.user.is_superuser:
        image = models.Images.objects.get(id = id)
        image.is_active = True
        image.save()
    return redirect('dashboard')

@login_required(login_url='login')
def logout_user(request):
    logout(request)
    return redirect('main')

def about(request):
    return render(request, 'about.html')

def ranking(request):
    ranked_users = User.objects.exclude(is_superuser=True).annotate(image_count=Count('images')).order_by('-image_count')

    ranked_users_with_rank = []
    for index, user in enumerate(ranked_users, start=1):
        ranked_users_with_rank.append({
            'rank': index,
            'first_name': user.first_name,
            'image_count': user.image_count,
            'email': hide_email(user.email)
        })
    return render(request, 'ranking.html', {'ranked_users_with_rank': ranked_users_with_rank})

def to_insta(request):
    images = models.Images.objects.filter(is_published_insta = False).order_by('-id')
    return render(request, 'to_insta.html', {'images': images})

def upload_to_insta(request, id):
    if request.user.is_superuser:
        # Fetch image data from the database
        data = get_object_or_404(models.Images, id=id)

        # Instagram credentials
        username = 'here is your username'
        password = 'here is your password'

        # Authenticate to Instagram
        cl = Client()
        cl.login(username, password)

        # Download the image to memory
        response = requests.get(data.url)

        with open('image.jpg', 'wb')as file:
            file.write(response.content)
        print('image saved')

        # Upload the image to Instagram from memory
        caption = data.description if data.description else ''
        cl.photo_upload('image.jpg', caption=caption)
        print('image uploaded')
        data.is_published_insta = True
        data.save()
        return redirect('to_insta')
    return redirect('main')