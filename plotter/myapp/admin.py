from django.contrib import admin
from .models import CSVFile, SavedPlot

# Register your models here.
admin.site.register(CSVFile)
admin.site.register(SavedPlot)