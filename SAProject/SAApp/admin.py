from django.contrib import admin
from .models import User, University, Program, Application

# Register your models here.
admin.site.register(User)
admin.site.register(University)
admin.site.register(Program)
admin.site.register(Application)