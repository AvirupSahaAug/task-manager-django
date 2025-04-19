from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Task

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Enter a valid email address.")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'color']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise forms.ValidationError("Due date and time must be in the future.")
        return due_date

class GroupTaskForm(forms.ModelForm):
    assigned_users = forms.CharField(
        help_text="Enter usernames separated by commas, or '*' to assign to all users."
    )
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'color', 'assigned_users']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Pop current_user from kwargs if provided.
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        from django.utils import timezone
        if due_date and due_date < timezone.now():
            raise forms.ValidationError("Due date and time must be in the future.")
        return due_date

    def clean_assigned_users(self):
        users_input = self.cleaned_data.get('assigned_users')
        from django.contrib.auth.models import User
        if users_input.strip() == "*":
            return User.objects.all()  # Return a queryset with all users.
        usernames = [name.strip() for name in users_input.split(",")]
        users = []
        invalid_users = []
        for username in usernames:
            try:
                user = User.objects.get(username=username)
                users.append(user)
            except User.DoesNotExist:
                invalid_users.append(username)
        if invalid_users:
            raise forms.ValidationError(
                f"The following users do not exist: {', '.join(invalid_users)}"
            )
        return users

    def save(self, commit=True):
        task = super().save(commit=False)
        if commit:
            task.save()
        # Get assigned users from cleaned_data
        assigned = self.cleaned_data['assigned_users']
        # If not all users (i.e. not a queryset), ensure current_user is included.
        if not hasattr(assigned, 'all') and self.current_user and self.current_user not in assigned:
            assigned.append(self.current_user)
        task.users.set(assigned)
        self.save_m2m()
        return task
