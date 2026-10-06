from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # A custom user model with a role to distinguish between students and admins
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('administrator', 'Administrator'),
        ('university', 'University'),
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='student')
    
    # Add related_name to avoid clashes with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='saapp_users',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='saapp_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username

class University(models.Model):
    # Model to store information about universities
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='university_logos/', blank=True)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    contact_email = models.EmailField()
    website = models.URLField()
    image_url = models.URLField(blank=True, null=True)

    # --- NEW PROPERTIES FOR TEMPLATE FILTERING ---
    @property
    def has_bachelors(self):
        """Checks if the university offers at least one Bachelor's program."""
        return self.programs.filter(degree_level__icontains="bachelor").exists()

    @property
    def has_masters(self):
        """Checks if the university offers at least one Master's program."""
        return self.programs.filter(degree_level__icontains="master").exists()

    @property
    def has_phd(self):
        """Checks if the university offers at least one PhD program."""
        # Use 'phd' or 'doctoral' for flexibility in degree_level field
        return self.programs.filter(degree_level__icontains="phd").exists() or \
               self.programs.filter(degree_level__icontains="doctoral").exists()
    # ---------------------------------------------

    def __str__(self):
        return self.name

class Program(models.Model):
    # Model to store information about programs offered by universities
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='programs')
    name = models.CharField(max_length=255)
    
    # It's highly recommended to use choices here for consistency, 
    # but based on your current model, it is left as CharField.
    degree_level = models.CharField(max_length=100) 
    
    duration = models.CharField(max_length=100)
    requirements = models.TextField()
    application_deadline = models.DateField()

    def __str__(self):
        return f"{self.name} at {self.university.name}"

class Application(models.Model):
    # Model to track a student's application to a program
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submission_date = models.DateTimeField(auto_now_add=True)
    documents = models.JSONField(default=list, blank=True, null=True, help_text="JSON field to store a list of documents and their status")

    full_name = models.CharField(max_length=255, blank=True)
    dob = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    current_education = models.CharField(max_length=255, blank=True)
    statement_of_purpose = models.TextField(blank=True)
    resume = models.FileField(upload_to='applications/resumes/', null=True, blank=True)
    passport_copy = models.FileField(upload_to='applications/passports/', null=True, blank=True)

    def __str__(self):
        return f"Application by {self.student.username} for {self.program.name}"