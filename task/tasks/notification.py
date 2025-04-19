import time
from django.db import connection
from django.utils import timezone
from django.core.mail import send_mail
from .models import Task
from django.conf import settings

def table_exists():
    return 'tasks_task' in connection.introspection.table_names()

def task_notification_loop():
    # Wait until the tasks_task table exists
    while not table_exists():
        time.sleep(1)
    while True:
        # Use the local time (e.g., IST, as set in settings.py)
        now = timezone.localtime(timezone.now())
        print("wee")
        # "soon" is set to 50 minutes from now for testing purposes;
        # change to 5 minutes if desired: timezone.timedelta(minutes=5)
        soon = now + timezone.timedelta(minutes=5)
        # Filter tasks that are due between now and soon
        tasks_due = Task.objects.filter(completed=False, due_date__gte=now, due_date__lte=soon)
        # print(now, soon, tasks_due)
        for task in tasks_due:
            print(task.users.all(),"wee")
            for user in task.users.all():
                print(user,user.email)
                if user.email:
                    subject = f"Reminder: Task '{task.title}' due soon"
                    message = (
                        f"Dear {user.username},\n\nYour task '{task.title}' is due at {task.due_date}.\n"
                        "Please take necessary action.\n\nRegards,\nTask Manager"
                    )
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                    print(f"Email sent to {user.email} for task '{task.title}'")
                else:
                    print(f"User {user.username} has no email for task '{task.title}'.")
        # Sleep for 60 seconds before checking again
        time.sleep(60*5)
