from django.urls import path
from . import views

urlpatterns = [
    # Public & Authentication
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Role-based Dashboard Redirect (main dashboard URL)
    path('dashboard/', views.dashboard, name='dashboard'), 
    
    # Specific Dashboard URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('university/dashboard/', views.university_dashboard, name='university_dashboard'),

    # Public Listings (accessible by all)
    path('universities/', views.universities, name='universities'),
    path('universities/<int:pk>/', views.university_detail, name='university_detail'),
    path('programs/', views.programs, name='programs'),
    path('programs/<int:pk>/', views.program_detail, name='program_detail'),
    
    # Application (Student)
    path('programs/<int:pk>/apply/', views.apply_program, name='apply_program'),
    path('applications/', views.applications, name='applications'), # Student and Admin view
    path('applications/<int:pk>/withdraw/', views.withdraw_application, name='withdraw_application'),
    path('applications/<int:pk>/edit/', views.edit_application, name='edit_application'),
    path('applications/<int:pk>/delete/', views.delete_application, name='delete_application'),

    # Admin Management (Universities)
    path('admin/universities/', views.university_list_admin, name='admin_university_list'),
    path('admin/universities/add/', views.add_university, name='add_university'),
    path('admin/universities/edit/<int:pk>/', views.edit_university, name='edit_university'),
    path('admin/universities/delete/<int:pk>/', views.delete_university, name='delete_university'),

    # Admin Management (Programs)
    path('admin/programs/', views.program_list_admin, name='admin_program_list'),
    path('admin/programs/add/', views.add_program, name='add_program'),
    path('admin/programs/edit/<int:pk>/', views.edit_program, name='edit_program'),
    path('admin/programs/delete/<int:pk>/', views.delete_program_admin, name='delete_program_admin'),

    # Admin Management (Users)
    path('admin/users/', views.user_list_admin, name='admin_user_list'),
    path('admin/users/add/', views.add_user_admin, name='add_user_admin'),
    path('admin/users/edit/<int:pk>/', views.edit_user_admin, name='edit_user_admin'),
    path('admin/users/delete/<int:pk>/', views.delete_user_admin, name='delete_user_admin'),

    # Admin Application Review
    path('admin/applications/update_status/<int:pk>/', views.update_application_status, name='update_application_status'),

    # University role paths
    path('university/dashboard/', views.university_dashboard, name='university_dashboard'),
    path('university/application/<int:pk>/update/', views.update_application_status, name='update_application_status'),
    path('admin/university/application/<int:pk>/review/', views.university_application_review, name='university_application_review'),
    path('university/profile/edit/', views.edit_university_profile, name='edit_university_profile'),
    path('university/programs/', views.university_program_list, name='university_program_list'),
    path('university/applications/', views.university_applications, name='university_applications'),
    path('university/programs/add/', views.add_program, name='add_program'),
    path('university/programs/edit/<int:pk>/', views.edit_program, name='edit_program'),
    path('university/programs/delete/<int:pk>/', views.delete_program_university, name='delete_program_university'),
    
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'), 

]