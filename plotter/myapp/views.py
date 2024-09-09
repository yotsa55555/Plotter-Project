from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio


def index(request):
    return render(request, "myapp/index.html")


def about(request):
    return render(request, "myapp/about.html")


def login(request):
    return render(request, "myapp/login.html")


def contact(request):
    return render(request, "myapp/contact.html")


def plot_data(request):
    plot_div = None
    columns = []

    # if request.method == 'POST':
    if "data" in request.session:
        data_dict = request.session["data"]
        data = pd.DataFrame.from_dict(data_dict)
        columns = list(data.columns)

        if not data.empty:
            x_column = request.POST.get("x_column", '')
            y_column = request.POST.get("y_column", '')
            plot_title = request.POST.get("plot_title", "Data Plot")
            plot_color = request.POST.get("plot_color", None)
            plot_style = request.POST.get("plot_style", None)

            if "scatter_plot" in request.POST:
                fig = px.scatter(
                    data, x=x_column, y=y_column, title=plot_title, template=plot_style
                )
                if plot_color:
                    fig.update_traces(marker=dict(color=plot_color))
                plot_div = pio.to_html(fig, full_html=False)

            elif "histogram_plot" in request.POST:
                fig = px.histogram(
                    data, x=x_column, title=plot_title, template=plot_style
                )
                if plot_color:
                    fig.update_traces(marker_color=plot_color)
                plot_div = pio.to_html(fig, full_html=False)

            elif "bar_plot" in request.POST:
                fig = px.bar(
                    data, x=x_column, y=y_column, title=plot_title, template=plot_style
                )
                if plot_color:
                    fig.update_traces(marker_color=plot_color)
                plot_div = pio.to_html(fig, full_html=False)

            elif "line_plot" in request.POST:
                fig = px.line(
                    data, x=x_column, y=y_column, title=plot_title, template=plot_style
                )
                if plot_color:
                    fig.update_traces(line=dict(color=plot_color))
                plot_div = pio.to_html(fig, full_html=False)

            elif "box_plot" in request.POST:
                fig = px.box(
                    data, x=x_column, y=y_column, title=plot_title, template=plot_style
                )
                if plot_color:
                    fig.update_traces(marker_color=plot_color)
                plot_div = pio.to_html(fig, full_html=False)

            elif "pie_plot" in request.POST:
                fig = px.pie(
                    data, names=x_column, title=plot_title, template=plot_style
                )
                if plot_color:
                    fig.update_traces(marker=dict(colors=[plot_color]))
                plot_div = pio.to_html(fig, full_html=False)

    return render(
        request, "myapp/plot.html", {"plot_div": plot_div, "columns": columns}
    )


def data(request):
    # data_html = None
    page_obj = None
    columns = None
    # plot_div = None

    if request.method == "POST":

        if "csv_file" in request.FILES:
            csv_file = request.FILES["csv_file"]
            if not csv_file.name.endswith(".csv"):
                return HttpResponse("This is not a CSV file")

            data = pd.read_csv(csv_file)
            request.session["data"] = data.to_dict()
            request.session["columns"] = list(data.columns)

            paginator = Paginator(data.values.tolist(), 10)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            columns = data.columns

            return redirect("/data")

        elif "clear_data" in request.POST:
            request.session.pop("data", None)
            request.session.pop("columns", None)
            messages.success(request, "Data has been cleared.")
            return redirect("/data")

        elif "clean_data" in request.POST:
            if "data" in request.session:
                data_dict = request.session["data"]
                data = pd.DataFrame.from_dict(data_dict)
                cleaned_data = check_data(data)
                request.session["data"] = cleaned_data.to_dict()
                request.session["columns"] = list(cleaned_data.columns)
                messages.success(request, "Data has been cleaned.")
            return redirect("/data")

        elif "replace_data" in request.POST:
            if "data" in request.session:
                column = request.POST.get("column")
                to_replace = request.POST.get("to_replace")
                if column and to_replace:
                    data_dict = request.session["data"]
                    data = pd.DataFrame.from_dict(data_dict)
                    replaced_data = replace_data(data, column, to_replace)
                    request.session["data"] = replaced_data.to_dict()
                    request.session["columns"] = list(replaced_data.columns)
                    messages.success(
                        request, f"Data in column '{column}' has been replaced."
                    )
            return redirect("/data")

        elif "delete_column" in request.POST:
            column = request.POST.get("column_id")
            data_dict = request.session["data"]
            data = pd.DataFrame.from_dict(data_dict)
            if column in data.columns:
                data = data.drop(columns=[column])
                request.session["data"] = data.to_dict()
                request.session["columns"] = list(data.columns)
                messages.success(request, f"Column '{column}' has been deleted.")
            else:
                messages.error(request, f"Column '{column}' does not exist.")
            return redirect("/data")

    else:
        if "data" in request.session:
            data_dict = request.session["data"]
            data = pd.DataFrame.from_dict(data_dict)
            columns = request.session.get("columns", [])
            paginator = Paginator(data.values.tolist(), 10)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)

    return render(
        request, "myapp/data.html", {"page_obj": page_obj, "columns": columns}
    )


def describe_data(request):
    description = None
    columns = None

    if "data" in request.session:
        data_dict = request.session["data"]
        data = pd.DataFrame.from_dict(data_dict)
        columns = list(data.columns)
        description = data.describe().to_html(classes="table table-striped")

    return render(
        request, "myapp/describe.html", {"description": description, "columns": columns}
    )


def check_data(data):
    if data.isnull().any().any():
        df_cleaned = clean_data(data)
        return df_cleaned
    else:
        return data


def clean_data(data):
    try:
        df_cleaned = data.dropna()
        return df_cleaned
    except Exception as e:
        return data


def replace_data(data, column, to_replace, replacement=np.nan):
    try:
        if to_replace.lower() == "true" or to_replace.lower() == "false":
            to_replace = to_replace.lower() == "true"
        else:
            try:
                to_replace = int(to_replace)
            except ValueError:
                try:
                    to_replace = float(to_replace)
                except ValueError:
                    pass
        data[column] = data[column].replace(to_replace, replacement)
    except Exception as e:
        print(f"Error in replace_data: {e}")
    return data


# def delete_column(data):
# pass


def delete_row(data):
    pass


def edit_value(data):
    pass
