from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('add/', views.add_task, name='add_task'),
    path('group-task/', views.create_group_task, name='create_group_task'),
    path('daily/', views.daily_tasks, name='daily_tasks'),
    path('weekly/', views.weekly_tasks, name='weekly_tasks'),
    path('monthly/', views.monthly_tasks, name='monthly_tasks'),
    path('complete/<int:task_id>/', views.complete_task, name='complete_task'),
    path('voice-task/', views.voice_task, name='voice_task'),
    path('due/', views.due_tasks, name='due_tasks'),
    path('completed/', views.completed_tasks, name='completed_tasks'),
    path('complete/<int:task_id>/', views.complete_task, name='complete_task'),
    
]


