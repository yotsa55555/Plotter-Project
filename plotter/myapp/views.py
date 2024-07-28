from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
import pandas as pd

def index(request):
    return render(request, 'myapp/index.html')

def about(request):
    return render(request, 'myapp/about.html')

def login(request):
    return render(request, 'myapp/login.html')

def data(request):
    data_html = None
    page_obj = None
    columns = None

    if request.method == 'POST' and 'csv_file' in request.FILES:
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

    elif request.method == 'POST' and 'clear_data' in request.POST:
        request.session.pop('data', None)
        request.session.pop('columns', None)
        return redirect('/data')

    elif request.method == 'POST' and 'clean_data' in request.POST:
        if 'data' in request.session:
            data_dict = request.session['data']
            data = pd.DataFrame.from_dict(data_dict)
            cleaned_data = check_data(data)
            request.session['data'] = cleaned_data.to_dict()
            request.session['columns'] = list(cleaned_data.columns)
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

def check_data(data):
    if data.isnull().any().any():
        df_cleaned = clean_data(data)
        return df_cleaned
    else:
        return data

def clean_data(data):
    try:
        df_cleaned = data.dropna()
        #df_cleaned = data.fillna(0)
        return df_cleaned
    except Exception as e:
        return data
