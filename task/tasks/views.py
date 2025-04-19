from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import login
from datetime import timedelta, date
import calendar
from .forms import SignupForm, TaskForm, GroupTaskForm
from .models import Task

def index(request):
    if request.user.is_authenticated:
        return redirect('daily_tasks')
    else:
        return redirect('login')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('daily_tasks')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def add_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.save()
            task.users.add(request.user)
            return redirect('daily_tasks')
    else:
        form = TaskForm()
    return render(request, 'add_task.html', {'form': form})

@login_required
@login_required
def create_group_task(request):
    if request.method == 'POST':
        form = GroupTaskForm(request.POST, current_user=request.user)
        if form.is_valid():
            task = form.save()
            messages.success(request, f"Group task '{task.title}' created successfully.")
            return redirect('daily_tasks')
        else:
            messages.error(request, "There was an error creating the group task.")
    else:
        form = GroupTaskForm(current_user=request.user)
    return render(request, 'group_task.html', {'form': form})

@login_required
def daily_tasks(request):
    now = timezone.localtime(timezone.now())
    tasks = Task.objects.filter(
        users=request.user, 
        due_date__date=now.date(), 
        completed=False
    ).order_by('due_date')  # Sort tasks by due_date ascending
    return render(request, 'daily_tasks.html', {'tasks': tasks})

from datetime import timedelta

from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Task
import calendar

@login_required
def weekly_tasks(request):
    # Get current time in local timezone (IST if Django is configured correctly)
    now = timezone.localtime(timezone.now())  # local timezone-aware datetime

    # Current local date
    today = now.date()

    # Compute the start (Monday) and end (Sunday) of the week
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Retrieve all uncompleted tasks of the current week
    tasks = Task.objects.filter(
        users=request.user,
        completed=False,
        due_date__date__gte=start_of_week,
        due_date__date__lte=end_of_week
    ).order_by('due_date')

    # 24x7 grid for hours x days
    grid = [[[] for _ in range(7)] for _ in range(24)]

    for task in tasks:
        local_due_date = timezone.localtime(task.due_date)  # ensure it's in IST
        task_date = local_due_date.date()
        day_index = (task_date - start_of_week).days
        hour_index = local_due_date.hour

        if 0 <= day_index < 7 and 0 <= hour_index < 24:
            grid[hour_index][day_index].append(task)

    day_names = [
        (start_of_week + timedelta(days=i)).strftime("%a %d/%m") for i in range(7)
    ]

    context = {
        'grid': grid,
        'day_names': day_names,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
    }
    return render(request, 'weekly_tasks.html', context)


import calendar

@login_required
def monthly_tasks(request):
    today = timezone.localtime(timezone.now()).date()
    # Get year and month from GET parameters, default to current year/month
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    cal = calendar.Calendar()
    month_calendar = cal.monthdayscalendar(year, month)
    
    tasks = Task.objects.filter(
        users=request.user, 
        due_date__year=year, 
        due_date__month=month, 
        completed=False
    ).order_by('due_date')
    
    tasks_by_day = {}
    for task in tasks:
        tasks_by_day.setdefault(task.due_date.day, []).append(task)
    
    # Calculate previous month and next month
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1

    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1

    context = {
        'month_calendar': month_calendar,
        'tasks_by_day': tasks_by_day,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
    }
    return render(request, 'monthly_tasks.html', context)

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    # Optionally, verify that the current user is among the task's users.
    if request.user in task.users.all():
        task.completed = True
        task.save()
        messages.success(request, f"Task '{task.title}' marked as completed.")
    else:
        messages.error(request, "You are not authorized to complete this task.")
    return redirect('daily_tasks')










import json
import re
import random
from datetime import datetime, timedelta

import google.generativeai as genai  # For Gemini API
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Task

# A small palette of pastel colors—feel free to expand or tweak!
PALETTE = [
    "#FFB3BA",  # pastel red
    "#FFDFBA",  # pastel orange
    "#FFFFBA",  # pastel yellow
    "#BAFFC9",  # pastel green
    "#BAE1FF",  # pastel blue
    "#E3BAFF",  # pastel purple
]

def extract_json(text):
    """
    Extracts a JSON object from a string, removing any Markdown formatting like ```json ... ```.
    """
    text = text.strip()
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return json.loads(match.group())
    raise ValueError("JSON object not found in Gemini response.")

@csrf_exempt
@login_required
def voice_task(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "error": "POST required"}, status=400)

    data = json.loads(request.body)
    transcript = data.get("transcript", "").strip()
    if not transcript:
        return JsonResponse({"status": "error", "error": "Empty transcript"}, status=400)

    # Configure Gemini
    genai.configure(api_key="AIzaSyAvoamdWIZSSiovbUT1KNlVN082zPXB6L8")
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Current IST time for prompt context
    ist_now = timezone.now() + timedelta(hours=5, minutes=30)

    prompt = f"""You are a task assistant. From this sentence: "{transcript}", extract:
    - A task title
    - A short description
    - A due date in 'YYYY-MM-DD HH:MM' format (assume today's date if not mentioned).
    Today's date and time is {ist_now.strftime('%Y-%m-%d %H:%M')}.
    Reply in JSON format like this:
    {{
        "title": "...",
        "description": "...",
        "due_date": "YYYY-MM-DD HH:MM"
    }}
    Do not wrap it in markdown. Return only JSON."""

    try:
        response = model.generate_content(prompt)
        json_output = extract_json(response.text)

        # Parse and localize due_date
        naive_due_date = datetime.strptime(json_output['due_date'], "%Y-%m-%d %H:%M")
        aware_due_date = timezone.make_aware(naive_due_date)

        # Pick a random pastel color
        color = random.choice(PALETTE)

        # Create the task
        task = Task.objects.create(
            title=json_output['title'],
            description=json_output.get('description', ''),
            due_date=aware_due_date,
            color=color,
        )
        task.users.add(request.user)
        task.save()

        return JsonResponse({"status": "success", "color_assigned": color})

    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)

@login_required
def due_tasks(request):
    now = timezone.localtime(timezone.now())  # Localized time
    tasks = Task.objects.filter(
        users=request.user,
        completed=False,
        due_date__lt=now
    ).order_by('due_date')

    return render(request, 'due_tasks.html', {'tasks': tasks})
@login_required
def completed_tasks(request):
    tasks = Task.objects.filter(
        users=request.user,
        completed=True
    ).order_by('-due_date')  # Show latest completed tasks first

    return render(request, 'completed_tasks.html', {'tasks': tasks})
def due_task_alert(request):
    if request.user.is_authenticated:
        now = timezone.localtime(timezone.now())
        due_tasks = Task.objects.filter(users=request.user, due_date__lt=now, completed=False)
        return {'has_due_tasks': due_tasks.exists()}
    return {}