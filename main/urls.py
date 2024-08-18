from django.urls import path
from . import views

urlpatterns = [
    path("", views.main, name = 'main'),
    path('fetch', views.fetch, name='fetch'),
    path('delete/<int:id>', views.delete_image, name='delete_image'),
    path('pixabay', views.get_pixabay, name='pixabay'),
    path('contribute', views.contribute, name='contribute'),
    path('sign-up', views.signup, name='signup'),
    path('alert-verification', views.req_verify, name='req_verify'),
    path('activate/<str:slug>', views.activate, name='activate'),
    path('login', views.login_user, name='login'),
    path('upload', views.upload, name='upload'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('delete-image/<int:id>', views.delete_image, name='delete_image'),
    path('accept-image/<int:id>', views.accept_image, name='accept_image'),
    path('log-out', views.logout_user, name='logout'),
    path('about', views.about, name='about'),
    path('ranking', views.ranking, name='ranking'),
    path('to-insta', views.to_insta, name='to_insta'),
    path('upload-to-insta/<int:id>', views.upload_to_insta, name='upload_to_insta')
]