from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.models import User
from .models import CSVFile

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        email = request.POST.get('email')

        if not username or not password or not confirm_password or not email:
            messages.error(request, "All fields are required")
            return render(request, 'myapp/register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'myapp/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken")
            return render(request, 'myapp/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered")
            return render(request, 'myapp/register.html')

        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()

        messages.success(request, "Account created successfully")
        return redirect('login') 

    return render(request, 'myapp/register.html')

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('data')
            else:
                messages.error(request, 'Invalid credentials')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'myapp/login.html')

def user_logout(request):
    logout(request)
    return redirect('index')


def index(request):
    return render(request, "myapp/index.html")


def about(request):
    return render(request, "myapp/about.html")

def contact(request):
    return render(request, "myapp/contact.html")


def select_viz(request):
    viz = PlotViz(request)
    if not viz.data.empty:
        viz.create_plot()
        return render(request, "myapp/selectPlot.html")
    else:
        messages.error(request, "Data is empty")
        return redirect('data')



class PlotViz:
    def __init__(self, request):
        self.request = request
        self.plot_div = None
        self.columns = []
        self.data = self.get_user_data()
        self.x_column = self.request.POST.get("x_column", "")
        self.y_column = self.request.POST.get("y_column", "")
        self.plot_title = self.request.POST.get("plot_title", "Data Plot")
        self.plot_color = self.request.POST.get("plot_color", None)
        self.plot_style = self.request.POST.get("plot_style", None)
        self.x_axis_label = self.request.POST.get("x_axis_label", "x")
        self.y_axis_label = self.request.POST.get("y_axis_label", "y")
        self.title_font_size_input = self.request.POST.get("title_font_size", "24")
        self.show_grid = "show_grid" in self.request.POST
        self.show_legend = "show_legend" in self.request.POST

    def get_user_data(self):
        user = self.request.user
        if user.is_authenticated:
            try:
                csv_file = CSVFile.objects.filter(user=user).latest('uploaded_at') 
                data = pd.read_csv(csv_file.file.path)
                self.columns = list(data.columns)
                return data
            except CSVFile.DoesNotExist:
                return pd.DataFrame()
        return pd.DataFrame()

    def render_plot(self):
        return render(
            self.request,
            self.template_name,
            {"plot_div": self.plot_div, "columns": self.columns},
        )
    
    def title_font_fix(self):
        try:
            self.title_font_size = int(self.title_font_size_input) if self.title_font_size_input else 24
        except (ValueError, TypeError):
            self.title_font_size = 24


    def create_plot(self):
        raise NotImplementedError("Subclasses should implement this method")


class BarViz(PlotViz):
    template_name = "myapp/plot/bar.html"

    def create_plot(self):
        if "bar_plot" in self.request.POST and not self.data.empty:

            self.bar_mode = self.request.POST.get("bar_mode", "group")
            self.orientation = self.request.POST.get("orientation", "v")
            self.bar_width = float(self.request.POST.get("bar_width", 0.8))
            self.opacity = float(self.request.POST.get("opacity", 1.0))

            self.title_font_fix()

            x_axis_label = self.x_axis_label or self.x_column
            y_axis_label = self.y_axis_label or self.y_column

            fig = px.bar(
                self.data,
                x=self.x_column,
                y=self.y_column,
                title=self.plot_title,
                template=self.plot_style,
                orientation=self.orientation,
            )

            if self.plot_color:
                fig.update_traces(marker_color=self.plot_color)

            fig.update_traces(
                marker_color=self.plot_color, opacity=self.opacity, width=self.bar_width
            )

            fig.update_layout(
                xaxis_title=x_axis_label,
                yaxis_title=y_axis_label,
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                title=dict(text=self.plot_title, font_size=self.title_font_size),
            )

            fig.update_layout(barmode=self.bar_mode)

            self.plot_div = pio.to_html(fig, full_html=False)

        return self.render_plot()


class BoxViz(PlotViz):
    template_name = "myapp/plot/box.html"

    def create_plot(self):
        if "box_plot" in self.request.POST and not self.data.empty:

            show_boxpoints = "show_boxpoints" in self.request.POST
            boxpoints_value = "all" if show_boxpoints else False

            self.title_font_fix()

            x_axis_label = self.x_axis_label or self.x_column
            y_axis_label = self.y_axis_label or self.y_column

            fig = px.box(
                self.data,
                x=self.x_column,
                y=self.y_column,
                title=self.plot_title,
                template=self.plot_style,
                points=boxpoints_value,
            )

            if self.plot_color:
                fig.update_traces(marker_color=self.plot_color)

            fig.update_layout(
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                xaxis_title=x_axis_label,
                yaxis_title=y_axis_label,
                title=dict(text=self.plot_title, font_size=self.title_font_size),
            )

            self.plot_div = pio.to_html(fig, full_html=False)

        return self.render_plot()


class HistogramViz(PlotViz):
    template_name = "myapp/plot/histogram.html"

    def create_plot(self):
        if "histogram_plot" in self.request.POST and not self.data.empty:

            num_bins_str = self.request.POST.get("num_bins", "")
            bin_width_str = self.request.POST.get("bin_width", "")

            num_bins = int(num_bins_str) if num_bins_str.isdigit() else None
            bin_width = (
                float(bin_width_str)
                if bin_width_str.replace(".", "", 1).isdigit()
                else None
            )

            self.title_font_fix()

            x_axis_label = self.x_axis_label or self.x_column
            y_axis_label = self.y_axis_label or self.y_column

            if num_bins is not None:
                fig = px.histogram(
                    self.data,
                    x=self.x_column,
                    nbins=num_bins,
                    title=self.plot_title,
                    template=self.plot_style,
                )
            elif bin_width is not None:

                fig = px.histogram(
                    self.data,
                    x=self.x_column,
                    nbins=int(10 / bin_width),
                    title=self.plot_title,
                    template=self.plot_style,
                )
            else:
                fig = px.histogram(
                    self.data,
                    x=self.x_column,
                    title=self.plot_title,
                    template=self.plot_style,
                )

            if self.plot_color:
                fig.update_traces(marker_color=self.plot_color)

            fig.update_layout(
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                xaxis_title=x_axis_label,
                yaxis_title=y_axis_label,
                title=dict(text=self.plot_title, font_size=self.title_font_size),
            )

            self.plot_div = pio.to_html(fig, full_html=False)

        return self.render_plot()


class LineViz(PlotViz):
    template_name = "myapp/plot/line.html"

    def create_plot(self):
        if "line_plot" in self.request.POST and not self.data.empty:
            self.line_width = int(self.request.POST.get("line_width", 2))
            self.legend_position = self.request.POST.get("legend_position", "top")

            x_axis_label = self.x_axis_label or self.x_column
            y_axis_label = self.y_axis_label or self.y_column

            self.title_font_fix()

            fig = px.line(
                self.data,
                x=self.x_column,
                y=self.y_column,
                title=self.plot_title,
                template=self.plot_style,
            )

            if self.plot_color:
                fig.update_traces(
                    line=dict(color=self.plot_color, width=self.line_width)
                )
            
            fig.update_layout(
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                xaxis_title=x_axis_label,
                yaxis_title=y_axis_label,
                legend=dict(yanchor="top", y=1.02, xanchor="center", x=0.5),
                title=dict(text=self.plot_title, font_size=self.title_font_size),
            )

            if self.legend_position == "bottom":
                fig.update_layout(
                    legend=dict(yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
            elif self.legend_position == "left":
                fig.update_layout(
                    legend=dict(yanchor="middle", y=0.5, xanchor="left", x=-0.1)
                )
            elif self.legend_position == "right":
                fig.update_layout(
                    legend=dict(yanchor="middle", y=0.5, xanchor="right", x=1.1)
                )

            self.plot_div = pio.to_html(fig, full_html=False)

        return self.render_plot()

class PieViz(PlotViz):
    template_name = "myapp/plot/pie.html"

    def create_plot(self):
        if "pie_plot" in self.request.POST and not self.data.empty:
            self.hole_size = float(self.request.POST.get("hole_size", 0)) 
            self.label_position = self.request.POST.get("label_position", "inside")  

            self.title_font_fix()

            fig = px.pie(
                self.data,
                names=self.x_column,
                values=self.y_column, 
                title=self.plot_title,
                template=self.plot_style,
            )

            if self.hole_size > 0:
                fig.update_traces(hole=self.hole_size)

            fig.update_traces(textposition=self.label_position) 
            fig.update_layout(
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                title=dict(text=self.plot_title, font_size=self.title_font_size)
            )

            self.plot_div = pio.to_html(fig, full_html=False)

        return self.render_plot()



class ScatterViz(PlotViz):
    template_name = "myapp/plot/scatter.html"

    def create_plot(self):
        if "scatter_plot" in self.request.POST and not self.data.empty:

            self.marker_type = self.request.POST.get("marker_type", None)

            try:
                self.marker_size = int(self.request.POST.get("marker_size", "5"))
            except (ValueError, TypeError):
                self.marker_size = 5

            self.title_font_fix()

            x_axis_label = self.x_axis_label or self.x_column
            y_axis_label = self.y_axis_label or self.y_column


            fig = px.scatter(
                self.data,
                x=self.x_column,
                y=self.y_column,
                title=self.plot_title,
                template=self.plot_style,
            )

            if self.marker_type:
                print(self.marker_type)
                fig.update_traces(marker=dict(symbol=self.marker_type))

            fig.update_traces(marker=dict(size=self.marker_size, color=self.plot_color))

            fig.update_layout(
                xaxis_title=x_axis_label,
                yaxis_title=y_axis_label,
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                title=dict(text=self.plot_title, font_size=self.title_font_size),
            )

            self.plot_div = pio.to_html(fig, full_html=False)

        return self.render_plot()

    
def bar_viz(request):
    viz = BarViz(request)
    if not viz.data.empty:
        viz.create_plot()
        return viz.render_plot()
    else:
        messages.error(request, "Data is empty")
        return redirect('data')


def box_viz(request):
    viz = BoxViz(request)
    if not viz.data.empty:
        viz.create_plot()
        return viz.render_plot()
    else:
        messages.error(request, "Data is empty")
        return redirect('data')


def histogram_viz(request):
    viz = HistogramViz(request)
    if not viz.data.empty:
        viz.create_plot()
        return viz.render_plot()
    else:
        messages.error(request, "Data is empty")
        return redirect('data')



def line_viz(request):
    viz = LineViz(request)
    if not viz.data.empty:
        viz.create_plot()
        return viz.render_plot()
    else:
        messages.error(request, "Data is empty")
        return redirect('data')


def pie_viz(request):
    viz = PieViz(request)
    if not viz.data.empty:
        viz.create_plot()
        return viz.render_plot()
    else:
        messages.error(request, "Data is empty")
        return redirect('data')


def scatter_viz(request):
    viz = ScatterViz(request)
    if not viz.data.empty:
        viz.create_plot()
        return viz.render_plot()
    else:
        messages.error(request, "Data is empty")
        return redirect('data')


class DataHandler:
    def __init__(self, request):
        self.request = request
        self.page_obj = None
        self.columns = None
        self.user = request.user
        self.data = self.get_user_data()

    def get_user_data(self):
        if self.user.is_authenticated:
            try:
                csv_file = CSVFile.objects.filter(user=self.user).latest('uploaded_at') 
                data = pd.read_csv(csv_file.file.path)
                self.columns = list(data.columns)
                return data
            except CSVFile.DoesNotExist:
                return pd.DataFrame()
        return pd.DataFrame()

    def set_user_data(self, data):
        csv_file = CSVFile.objects.filter(user=self.user).latest('uploaded_at')
        data.to_csv(csv_file.file.path, index=False)
        self.columns = list(data.columns)
        self.data = data

    def clear_user_data(self):
        self.request.session.pop("csv_file_id", None)
        self.request.session.pop("columns", None)

    def paginate_data(self):
        if not self.data.empty:
            paginator = Paginator(self.data.values.tolist(), 10)
            page_number = self.request.GET.get("page")
            self.page_obj = paginator.get_page(page_number)
            if not self.columns:
                self.columns = list(self.data.columns)

    def process_request(self):
        raise NotImplementedError("Subclasses must implement this method")
    
class CSVUploadHandler(DataHandler):
    def process_request(self):
        csv_file = self.request.FILES.get("csv_file")
        if not csv_file.name.endswith(".csv"):
            return HttpResponse("This is not a CSV file")
        
        user = self.request.user

        try:
            csv_file_model = CSVFile.objects.create(file=csv_file, user=user)
            self.set_user_data(csv_file_model)
        except Exception as e:
            messages.error(self.request, f"Failed to process the CSV file: {e}")
            return redirect("/data")

        return redirect("/data")
    
class ClearDataHandler(DataHandler):
    def process_request(self):
        self.clear_user_data()
        messages.success(self.request, "Data has been cleared.")
        return redirect("/data")


class CleanDataHandler(DataHandler):
    def process_request(self):
        if not self.data.empty:
            cleaned_data = self.check_data(self.data)
            self.set_user_data(cleaned_data)
            messages.success(self.request, "Data has been cleaned.")
        return redirect("/data")
    
    @staticmethod
    def check_data(data):
        if data.isnull().any().any():
            df_cleaned = data.dropna()
            return df_cleaned
        else:
            return data
        
class DeleteColumnHandler(DataHandler):
    def process_request(self):
        column = self.request.POST.get("column_id")
        if column in self.data.columns:
            self.data = self.data.drop(columns=[column])
            self.set_user_data(self.data)
            messages.success(self.request, f"Column '{column}' has been deleted.")
        else:
            messages.error(self.request, f"Column '{column}' does not exist.")
        return redirect("/data")

class ReplaceDataHandler(DataHandler):
    def process_request(self):
        column = self.request.POST.get("column")
        to_replace = self.request.POST.get("to_replace")
        value = self.request.POST.get("value")
        
        if column and to_replace and not self.data.empty:
            try:
                self.data = self.replace_data(self.data, column, to_replace, value)
                self.set_user_data(self.data)
                messages.success(
                    self.request, f"Data in column '{column}' has been replaced."
                )
            except Exception as e:
                messages.error(
                    self.request, f"An error occurred while replacing data: {str(e)}"
                )
        else:
            messages.warning(
                self.request, "Missing required fields or empty data."
            )
        
        return redirect("/data")
    
    @staticmethod
    def replace_data(data, column, to_replace, replacement):
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
            
            if replacement.lower() == "nan":
                replacement = np.nan
            
            data[column] = data[column].replace(to_replace, replacement)
        except Exception as e:
            raise Exception(f"Error in replace_data: {e}")
        
        return data

@login_required
def data(request):
    handler = None

    if request.method == "POST":
        if "csv_file" in request.FILES:
            handler = CSVUploadHandler(request)
        elif "clear_data" in request.POST:
            handler = ClearDataHandler(request)
        elif "clean_data" in request.POST:
            handler = CleanDataHandler(request)
        elif "replace_data" in request.POST:
            handler = ReplaceDataHandler(request)
        elif "delete_column" in request.POST:
            handler = DeleteColumnHandler(request)

        if handler:
            response = handler.process_request()
            if response:
                return response

    handler = DataHandler(request)
    handler.paginate_data()

    return render(
        request,
        "myapp/data.html",
        {"page_obj": handler.page_obj, "columns": handler.columns},
    )


class DescribeData(DataHandler):
    def process_request(self):
        description = None
        columns = None
        user = self.request.user

        if not self.data.empty:
            try:
                csv_file = CSVFile.objects.filter(user=user).latest('uploaded_at')
                data = pd.read_csv(csv_file.file.path)
                
                columns = list(data.columns)
                
                description = data.describe().round(2)
                
                additional_info = pd.DataFrame(index=['dtype', 'null_count', 'unique_count'], columns=columns)
                
                for column in columns:
                    additional_info.loc['dtype', column] = str(data[column].dtype)
                    additional_info.loc['null_count', column] = data[column].isnull().sum()
                    additional_info.loc['unique_count', column] = data[column].nunique()
                
                description = pd.concat([description, additional_info])
                
                description = description.to_html(classes="table table-striped table-hover")
                
                column_info = []
                for column in columns:
                    info = {
                        'name': column,
                        'dtype': str(data[column].dtype),
                        'null_count': data[column].isnull().sum(),
                        'unique_count': data[column].nunique(),
                    }
                    if data[column].dtype in ['object', 'category']:
                        info['top_values'] = data[column].value_counts().head(5).to_dict()
                    column_info.append(info)
                
            except CSVFile.DoesNotExist:
                messages.error(self.request, "CSV file not found. Please upload a file first.")
                return redirect('data')
            except Exception as e:
                messages.error(self.request, f"An error occurred while processing the data: {str(e)}")
                return redirect('data')
        else:
            messages.info(self.request, "No CSV file has been uploaded yet.")
            return redirect('data')

        context = {
            "description": description,
            "columns": columns,
            "column_info": column_info
        }
        
        return render(self.request, "myapp/describe.html", context)
    
@login_required
def describe_data(request):
    handler = DescribeData(request)
    return handler.process_request()


# def delete_column(data):
# pass


def delete_row(data):
    pass


def edit_value(data):
    pass
