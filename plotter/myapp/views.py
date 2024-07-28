# myapp/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
import pandas as pd

def index(request):
    return render(request, 'myapp/index.html')

def about(request):
    return render(request, 'myapp/about.html')

def data(request):
    data_html = None
    page_obj = None
    columns = None

    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            return HttpResponse("This is not a CSV file")

        data = pd.read_csv(csv_file)
        request.session['data'] = data.to_dict()
        request.session['columns'] = list(data.columns)

        paginator = Paginator(data.values.tolist(), 10)  
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        columns = data.columns

        return redirect('/data')

    else:

        if 'data' in request.session:
            data_dict = request.session['data']
            data = pd.DataFrame.from_dict(data_dict)
            columns = request.session.get('columns', [])
            paginator = Paginator(data.values.tolist(), 10) 
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

    return render(request, 'myapp/data.html', {'page_obj': page_obj, 'columns': columns})
