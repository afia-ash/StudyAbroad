from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.core.validators import RegexValidator
from .models import User, University, Program, Application

# Custom UserCreationForm for registration (Student/Admin initial creation)
class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('administrator', 'Administrator'),
        ('university', 'University'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial='student', widget=forms.RadioSelect)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'role',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput, forms.NumberInput, forms.Textarea, forms.Select)):
                field.widget.attrs.update({'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50'})
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'form-radio h-4 w-4 text-primary transition duration-150 ease-in-out'})
            
            if field_name == 'username':
                field.help_text = None # Remove default help text if desired

# Custom UserChangeForm for admin to edit users (e.g., change roles, username, email)
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'is_active', 'is_staff', 'is_superuser') # Include fields admin can modify

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Tailwind classes to new fields as well
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput, forms.NumberInput, forms.Textarea, forms.Select)):
                field.widget.attrs.update({'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50'})
            # For boolean fields (checkboxes), you might need different styling
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-checkbox h-4 w-4 text-primary transition duration-150 ease-in-out rounded'})
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'form-radio h-4 w-4 text-primary transition duration-150 ease-in-out'})

# NEW: Custom Authentication Form for login page styling
class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50', 'placeholder': 'Enter your username'})
        self.fields['password'].widget.attrs.update({'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50', 'placeholder': 'Enter your password'})

# Form for University Model
class UniversityForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['name', 'location', 'description', 'contact_email', 'website', 'image_url']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Harvard University'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Cambridge, MA, USA'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Brief description of the university...'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'email@university.edu'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://www.university.edu'}),
            'image_url': forms.URLInput(attrs={'placeholder': 'https://example.com/image.jpg'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50'


# Form for Program Model
class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['university', 'name', 'degree_level', 'duration', 'requirements', 'application_deadline']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Computer Science Masters'}),
            'degree_level': forms.TextInput(attrs={'placeholder': 'e.g., Bachelor, Master, PhD'}),
            'duration': forms.TextInput(attrs={'placeholder': 'e.g., 2 years, 4 semesters'}),
            'requirements': forms.Textarea(attrs={'rows': 4, 'placeholder': 'List admission requirements...'}),
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Grab user object
        super().__init__(*args, **kwargs)
        
        # For university users, fix the university and hide the field
        if user and user.role == 'university':
            # Set initial university if instance is None
            if not self.instance.pk:
                self.fields['university'].initial = user.university
            self.fields['university'].widget = forms.HiddenInput()
        else:
            # For admin, keep the dropdown and add styling
            self.fields['university'].widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50'
            })

        # Apply generic styling to other fields
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ != 'HiddenInput':
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50'
                })

class ApplicationForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=10,
        min_length=10,
        required=True,
        validators=[RegexValidator(r'^\d{10}$', message="Enter a valid 10-digit phone number.")],
    )
    email = forms.EmailField(
        required=True,
        max_length=254,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )

    full_name = forms.CharField(
        max_length=100,
        required=True,
        validators=[RegexValidator(r'^[a-zA-Z ]+$', message="Name can contain only letters and spaces.")],
    )
    statement_of_purpose = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        min_length=10,
        max_length=1000,
        required=True,
    )
    dob = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = Application
        fields = [
            'full_name',
            'dob',
            'phone',
            'email',
            'current_education',
            'statement_of_purpose',
            'resume',
            'passport_copy',
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'statement_of_purpose': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_dob(self):
        dob = self.cleaned_data['dob']
        import datetime
        if dob > datetime.date.today():
            raise forms.ValidationError("DOB cannot be in the future.")
        return dob
