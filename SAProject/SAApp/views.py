from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UniversityForm, ProgramForm, CustomUserChangeForm, ApplicationForm
from .models import University, Program, Application, User
from django.db.models import Count, Q

# Predicates for user_passes_test decorator
def is_student(user):
    return user.is_authenticated and user.role == 'student'

def is_admin(user):
    return user.is_authenticated and user.role == 'administrator'

def is_university(user):
    return user.is_authenticated and user.role == 'university'

# --- Public Views ---
def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.role = request.POST.get('role')  # Assign role from form
            user.save()
            
            # Automatically create and link university profile if role is university
            if user.role == 'university':
                # Fill in other required fields, such as name or email, appropriately
                University.objects.create(user=user, name=user.username)
            
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('index')

# --- Dashboard & Role-based Access ---
@login_required
def dashboard(request):
    if request.user.role == 'administrator':
        return redirect('admin_dashboard')
    elif request.user.role == 'university':
        return redirect('university_dashboard')
    elif request.user.role == 'student':
        return redirect('student_dashboard')
    else:
        return redirect('index')

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    student_applications = Application.objects.filter(student=request.user).order_by('-submission_date')
    context = {
        'student_applications': student_applications
    }
    return render(request, 'student_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = User.objects.count()
    total_universities = University.objects.count()
    total_programs = Program.objects.count()
    total_applications = Application.objects.count()
    context = {
        'total_users': total_users,
        'total_universities': total_universities,
        'total_programs': total_programs,
        'total_applications': total_applications
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'university')
def university_dashboard(request):
    try:
        university = request.user.university
    except University.DoesNotExist:
        messages.error(request, "No university profile is linked to your user account. Please contact admin.")
        return redirect('index')
    university = request.user.university
    applications = Application.objects.filter(
                program__university=university
            ).exclude(
                student=university.user  # Exclude applications by the university user themselves
            ).order_by('-submission_date')
    context = {
        'applications': applications,
        'university': university,
    }
    return render(request, 'university_dashboard.html', context)

# --- Public University and Program Listings with Search Filters ---
def universities(request):
    query = request.GET.get('q')
    location = request.GET.get('location')

    university_list = University.objects.all().order_by('name')

    if query:
        university_list = university_list.filter(
            Q(name__icontains=query) | Q(location__icontains=query)
        )
    if location:
        university_list = university_list.filter(location__iexact=location)

    context = {
        'universities': university_list,
        'locations': University.objects.values_list('location', flat=True).distinct()
    }
    return render(request, 'universities.html', context)

def university_detail(request, pk):
    university = get_object_or_404(University, pk=pk)
    return render(request, 'university_detail.html', {'university': university})

def programs(request):
    query = request.GET.get('q')
    university_pk = request.GET.get('university')
    degree_level = request.GET.get('degree')

    # Role-based program filtering
    if request.user.is_authenticated and request.user.role == "university":
        # Only show programs for this university
        program_list = Program.objects.filter(university=request.user.university).order_by('name')
    else:
        # Students and admins see all programs
        program_list = Program.objects.all().order_by('name')
    
    universities_list = University.objects.all().order_by('name')
    
    
    context = {
        'programs': program_list,
        'universities': universities_list,
        'degree_levels': Program.objects.values_list('degree_level', flat=True).distinct()
    }
    return render(request, 'programs.html', context)

def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)
    return render(request, 'program_detail.html', {'program': program})

# --- Student Application Feature ---
@login_required
@user_passes_test(is_student)
def apply_program(request, pk):
    program = get_object_or_404(Program, pk=pk)
    
    # Check if student has already applied
    if Application.objects.filter(student=request.user, program=program).exists():
        messages.warning(request, "You have already applied for this program.")
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.student = request.user
            app.program = program
            app.status = 'under_review'
            app.save()
            messages.success(request, f"Application submitted for {program.name}.")
            return redirect('student_dashboard')
        else:
            messages.error(request, "Please fix the errors in the form.")
    else:
        # Pre-fill convenience fields if desired
        initial = {'full_name': request.user.get_full_name() or request.user.username}
        form = ApplicationForm(initial=initial)


    context = {
        'program': program,
        'form': form,
    }
    return render(request, 'apply_program.html', context)


@login_required
@user_passes_test(is_student)
def withdraw_application(request, pk):
    application = get_object_or_404(Application, pk=pk, student=request.user)
    if request.method == 'POST':
        # To delete:
        # application.delete()
        
        # Or mark as withdrawn:
        application.status = 'withdrawn'
        application.save()
        messages.success(request, "Application withdrawn successfully.")
        return redirect('applications')
    return render(request, 'confirm_withdraw.html', {'application': application})


@login_required
@user_passes_test(is_student)
def edit_application(request, pk):
    application = get_object_or_404(Application, pk=pk, student=request.user)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, "Application updated successfully.")
            return redirect('applications')
        else:
            messages.error(request, "Please fix the errors in the form.")
    else:
        form = ApplicationForm(instance=application)
    return render(request, 'edit_application.html', {'form': form, 'application': application})

@login_required
@user_passes_test(is_student)
def delete_application(request, pk):
    application = get_object_or_404(Application, pk=pk, student=request.user)
    if request.method == 'POST':
        application.delete()
        messages.success(request, "Application deleted successfully.")
        return redirect('applications')
    return render(request, 'confirm_delete.html', {'application': application})



@login_required
def applications(request):
    if request.user.role == 'administrator':
        all_applications = Application.objects.all().order_by('-submission_date')
        context = {'applications': all_applications, 'is_admin': True}
        return render(request, 'applications.html', context)
    else: # student
        student_applications = Application.objects.filter(student=request.user).order_by('-submission_date')
        context = {'applications': student_applications, 'is_admin': False}
        return render(request, 'applications.html', context)

# --- Admin Management Features (CRUD) ---
@login_required
@user_passes_test(is_admin)
def university_list_admin(request):
    universities = University.objects.annotate(program_count=Count('programs')).order_by('name')
    return render(request, 'admin/university_list.html', {'universities': universities})

@login_required
@user_passes_test(is_admin)
def add_university(request):
    if request.method == 'POST':
        form = UniversityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "University added successfully.")
            return redirect('admin_university_list')
    else:
        form = UniversityForm()
    return render(request, 'admin/university_form.html', {'form': form, 'page_title': 'Add New University'})

@login_required
@user_passes_test(is_admin)
def edit_university(request, pk):
    university = get_object_or_404(University, pk=pk)
    if request.method == 'POST':
        form = UniversityForm(request.POST, instance=university)
        if form.is_valid():
            form.save()
            messages.success(request, f"University '{university.name}' updated successfully.")
            return redirect('admin_university_list')
    else:
        form = UniversityForm(instance=university)
    return render(request, 'admin/university_form.html', {'form': form, 'page_title': 'Edit University'})

@login_required
@user_passes_test(is_admin)
def delete_university(request, pk):
    university = get_object_or_404(University, pk=pk)
    if request.method == 'POST':
        university.delete()
        messages.success(request, f"University '{university.name}' deleted successfully.")
        return redirect('admin_university_list')
    return render(request, 'admin/confirm_delete.html', {'object': university, 'object_type': 'University'})

@login_required
@user_passes_test(is_admin)
def program_list_admin(request):
    programs = Program.objects.all().order_by('name')
    return render(request, 'admin/program_list.html', {'programs': programs})

@login_required
@user_passes_test(is_admin)
def add_program(request):
    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Program added successfully.")
            return redirect('admin_program_list')
    else:
        form = ProgramForm()
    return render(request, 'admin/program_form.html', {'form': form, 'page_title': 'Add New Program'})

@login_required
@user_passes_test(is_admin)
def edit_program(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, f"Program '{program.name}' updated successfully.")
            return redirect('admin_program_list')
    else:
        form = ProgramForm(instance=program)
    return render(request, 'admin/program_form.html', {'form': form, 'page_title': 'Edit Program'})

@login_required
@user_passes_test(is_admin)
def delete_program_admin(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        program.delete()
        messages.success(request, f"Program '{program.name}' deleted successfully.")
        return redirect('admin_program_list')
    return render(request, 'admin/confirm_delete.html', {'object': program, 'object_type': 'Program'})

@login_required
@user_passes_test(is_admin)
def user_list_admin(request):
    users = User.objects.all().order_by('username')
    return render(request, 'admin/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def add_user_admin(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' added successfully.")
            return redirect('admin_user_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'admin/user_form.html', {'form': form, 'page_title': 'Add New User'})

@login_required
@user_passes_test(is_admin)
def edit_user_admin(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user_obj.username}' updated successfully.")
            return redirect('admin_user_list')
    else:
        form = CustomUserChangeForm(instance=user_obj)
    return render(request, 'admin/user_form.html', {'form': form, 'page_title': f'Edit User: {user_obj.username}'})

@login_required
@user_passes_test(is_admin)
def delete_user_admin(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user_obj.is_superuser:
            messages.error(request, "Cannot delete the superuser account.")
            return redirect('admin_user_list')
        
        user_obj.delete()
        messages.success(request, f"User '{user_obj.username}' deleted successfully.")
        return redirect('admin_user_list')
    return render(request, 'admin/confirm_delete.html', {'object': user_obj, 'object_type': 'User'})


@login_required
@user_passes_test(lambda u: u.role == 'administrator' or u.role == 'university')
def update_application_status(request, pk):
    if request.user.role == "university":
        application = get_object_or_404(Application, pk=pk, program__university=request.user.university)
    else:  # admin
        application = get_object_or_404(Application, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        # Block updating if application is withdrawn
        if application.status == 'withdrawn':
            messages.error(request, "Cannot update status of a withdrawn application.")
        elif status in [choice[0] for choice in application.STATUS_CHOICES]:
            application.status = status
            application.save()
        else:
            messages.error(request, "Invalid status provided.")
    # Redirect to correct dashboard
    if request.user.role == "university":
        return redirect('university_dashboard')
    else:
        return redirect('admin_dashboard')



@login_required
@user_passes_test(is_university)
def edit_university_profile(request):
    university = request.user.university
    if request.method == 'POST':
        # Handle university profile update form
        university.name = request.POST.get('name')
        university.description = request.POST.get('description')
        university.contact_email = request.POST.get('contact_email')
        # Handle logo if provided
        if 'logo' in request.FILES:
            university.logo = request.FILES['logo']
        university.save()
        return redirect('university_dashboard')
    return render(request, 'edit_university_profile.html', {'university': university})

@login_required  # add appropriate user_passes_test decorator if needed
@user_passes_test(is_university)
def university_program_list(request):
    # Just an example: show all programs for this user's university
    programs = Program.objects.filter(university=request.user.university)
    return render(request, 'university/university_program_list.html', {'programs': programs})

@login_required
@user_passes_test(is_university)
def university_applications(request):
    university = request.user.university
    applications = Application.objects.filter(program__university=university)
    return render(request, 'admin/applications.html', {'applications': applications})

@login_required
@user_passes_test(is_university)
def add_program(request):
    if request.method == 'POST':
        form = ProgramForm(request.POST, user=request.user)
        if form.is_valid():
            program = form.save(commit=False)
            # Auto assign university for university users
            if request.user.role == 'university':
                program.university = request.user.university
            program.save()
            messages.success(request, "Program added successfully.")
            return redirect('university_program_list')
    else:
        form = ProgramForm(user=request.user)
    return render(request, 'university/program_form.html', {'form': form, 'page_title': 'Add New Program'})

@login_required
@user_passes_test(is_university)
def edit_program(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, f"Program '{program.name}' updated successfully.")
            return redirect('admin_program_list')
    else:
        form = ProgramForm(instance=program)
    return render(request, 'admin/program_form.html', {'form': form, 'page_title': 'Edit Program'})

@login_required
@user_passes_test(is_university)
def delete_program_university(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        program.delete()
        messages.success(request, f"Program '{program.name}' deleted successfully.")
        return redirect('admin_program_list')
    return render(request, 'admin/confirm_delete.html', {'object': program, 'object_type': 'Program'})

@login_required
@user_passes_test(is_university)  # Restrict to university users
def university_application_review(request, pk):
    university = request.user.university
    application = get_object_or_404(Application, pk=pk, program__university=university)
    return render(request, 'university/application_review.html', {'application': application})

def contact(request):
    if request.method == 'POST':
        pass 
    return render(request, 'contact.html')

def about(request):
    return render(request, 'about.html')

