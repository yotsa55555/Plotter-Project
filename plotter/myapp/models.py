from django.db import models
from django.contrib.auth.models import User

class CSVFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    file = models.FileField(upload_to='csv_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
    
class SavedPlot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    plot_type = models.CharField(max_length=50)
    plot_data = models.JSONField()
    uploaded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
