
from django.apps import AppConfig
import threading

class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        from .notification import task_notification_loop
        # Start the notification thread as daemon so it stops with the server.
        threading.Thread(target=task_notification_loop, daemon=True).start()
