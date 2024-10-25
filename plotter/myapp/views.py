from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.models import User
from .models import CSVFile, SavedPlot
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
import json

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
                return redirect('index')
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
        return render(request, "myapp/selectPlot.html")
    else:
        messages.error(request, "Data is empty")
        return redirect('data')



class PlotViz:
    def __init__(self, request):
        self.request = request
        self.plot_div = None
        self.plot_div_type = None
        self.columns = []
        self.data = self.get_user_data()
        self.load_from_session()
 
    def get_user_data(self):
        user = self.request.user
        if user.is_authenticated:
            try:
                csv_file = CSVFile.objects.filter(user=user).latest('uploaded_at') 
                data = pd.read_csv(csv_file.file.path)
                if 'Index' not in data.columns:
                    data['Index'] = data.index
                    cols = ['Index'] + [col for col in data.columns if col != 'Index']
                    data = data[cols]
                self.columns = list(data.columns)
                return data
            except CSVFile.DoesNotExist:
                return pd.DataFrame()
        return pd.DataFrame()
    
    def load_from_session(self):
        session = self.request.session
        self.x_column = session.get("x_column", "")
        self.y_column = session.get("y_column", "")
        self.plot_title = session.get("plot_title", "Data Plot")
        self.plot_color = session.get("plot_color", None)
        self.plot_style = session.get("plot_style", None)
        self.x_axis_label = session.get("x_axis_label", "x")
        self.y_axis_label = session.get("y_axis_label", "y")
        self.title_font_size_input = session.get("title_font_size", 24)
        self.show_grid = session.get("show_grid", False)
        self.show_legend = session.get("show_legend", False)

    def save_to_session(self):
        session = self.request.session
        session["x_column"] = self.x_column
        session["y_column"] = self.y_column
        session["plot_title"] = self.plot_title
        session["plot_color"] = self.plot_color
        session["plot_style"] = self.plot_style
        session["x_axis_label"] = self.x_axis_label
        session["y_axis_label"] = self.y_axis_label
        session["title_font_size"] = self.title_font_size_input
        session["show_grid"] = self.show_grid
        session["show_legend"] = self.show_legend

    def update_from_post(self):
        self.x_column = self.request.POST.get("x_column", self.x_column)
        self.y_column = self.request.POST.get("y_column", self.y_column)
        self.plot_title = self.request.POST.get("plot_title", self.plot_title)
        self.plot_color = self.request.POST.get("plot_color", self.plot_color)
        self.plot_style = self.request.POST.get("plot_style", self.plot_style)
        self.x_axis_label = self.request.POST.get("x_axis_label", self.x_axis_label)
        self.y_axis_label = self.request.POST.get("y_axis_label", self.y_axis_label)
        self.title_font_size_input = int(self.request.POST.get("title_font_size", self.title_font_size_input))
        self.show_grid = "show_grid" in self.request.POST
        self.show_legend = "show_legend" in self.request.POST
        self.save_to_session()

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

    def save_plot(self, title, plot_type, fig):
        try:
            print(fig)
            if fig is None:
                return False, "No plot to save. Please create a plot first."

            plot_data = pio.to_json(fig)

            plot = SavedPlot(
                user=self.request.user,
                title=title,
                plot_type=plot_type,
                plot_data=plot_data,
            )

            plot.uploaded_at = timezone.now()
            print(plot.uploaded_at)
            plot.save()
            return True, "Plot saved successfully."
            
        except Exception as e:
            return False, f"Error saving plot: {str(e)}"

    def create_plot(self):
        raise NotImplementedError("Subclasses should implement this method")


class BarViz(PlotViz):
    template_name = "myapp/plot/bar.html"

    def __init__(self, request):
        super().__init__(request)
        # Initialize fig from session if it exists
        self.fig = None
        plot_data = self.request.session.get('plot_bar')
        if plot_data:
            try:
                self.fig = pio.from_json(plot_data)
            except Exception:
                pass

    def create_plot(self):
        if "bar_plot" in self.request.POST and not self.data.empty:
            self.update_from_post()
            plot_type = self.request.POST.get('plot_type', 'bar')
            
            self.bar_mode = self.request.POST.get("bar_mode", "group")
            self.orientation = self.request.POST.get("orientation", "v")
            self.bar_width = float(self.request.POST.get("bar_width", 0.8))
            self.opacity = float(self.request.POST.get("opacity", 1.0))

            self.request.session["bar_mode"] = self.bar_mode
            self.request.session["orientation"] = self.orientation
            self.request.session["bar_width"] = self.bar_width
            self.request.session["opacity"] = self.opacity

            self.title_font_fix()

            x_axis_label = self.x_axis_label or self.x_column
            y_axis_label = self.y_axis_label or self.y_column

            self.fig = px.bar(
                self.data,
                x=self.x_column,
                y=self.y_column,
                title=self.plot_title,
                template=self.plot_style,
                orientation=self.orientation,
            )

            if self.plot_color:
                self.fig.update_traces(marker_color=self.plot_color)

            self.fig.update_traces(
                marker_color=self.plot_color, opacity=self.opacity, width=self.bar_width
            )

            self.fig.update_layout(
                xaxis_title=x_axis_label,
                yaxis_title=y_axis_label,
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                title=dict(text=self.plot_title, font_size=self.title_font_size),
            )

            self.fig.update_layout(barmode=self.bar_mode)

            self.request.session['plot_bar'] = pio.to_json(self.fig)
            self.plot_div = pio.to_html(self.fig, full_html=False)

            plot_div_dict = self.request.session.get('plot_div', {})
            if not isinstance(plot_div_dict, dict):
                plot_div_dict = {}
            plot_div_dict[plot_type] = self.plot_div
            self.request.session['plot_div'] = plot_div_dict
            self.request.session.modified = True

        plot_div_dict = self.request.session.get('plot_div', {})
        self.plot_div = plot_div_dict.get('bar') if isinstance(plot_div_dict, dict) else None

        if self.fig is None and self.request.session.get('plot_bar'):
            try:
                self.fig = pio.from_json(self.request.session['plot_bar'])
            except Exception:
                pass

        return self.render_plot()


class BoxViz(PlotViz):
    template_name = "myapp/plot/box.html"

    def __init__(self, request):
        super().__init__(request)
        # Initialize fig from session if it exists
        self.fig = None
        plot_data = self.request.session.get('plot_box')
        if plot_data:
            try:
                self.fig = pio.from_json(plot_data)
            except Exception:
                pass

    def create_plot(self):
        if "box_plot" in self.request.POST and not self.data.empty:
            self.update_from_post()
            plot_type = self.request.POST.get('plot_type', 'box')

            show_boxpoints = "show_boxpoints" in self.request.POST
            self.request.session["show_boxpoints"] = show_boxpoints
            boxpoints_value = "all" if show_boxpoints else False

            self.title_font_fix()

            x_axis_label = self.x_axis_label or self.x_column
            y_axis_label = self.y_axis_label or self.y_column

            self.fig = px.box(
                self.data,
                x=self.x_column,
                y=self.y_column,
                title=self.plot_title,
                template=self.plot_style,
                points=boxpoints_value,
            )

            if self.plot_color:
                self.fig.update_traces(marker_color=self.plot_color)

            self.fig.update_layout(
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                xaxis_title=x_axis_label,
                yaxis_title=y_axis_label,
                title=dict(text=self.plot_title, font_size=self.title_font_size),
            )

            self.request.session['plot_box'] = pio.to_json(self.fig)
            self.plot_div = pio.to_html(self.fig, full_html=False)

            plot_div_dict = self.request.session.get('plot_div', {})
            if not isinstance(plot_div_dict, dict):
                plot_div_dict = {}
            plot_div_dict[plot_type] = self.plot_div
            self.request.session['plot_div'] = plot_div_dict
            self.request.session.modified = True

        plot_div_dict = self.request.session.get('plot_div', {})
        self.plot_div = plot_div_dict.get('box') if isinstance(plot_div_dict, dict) else None

        if self.fig is None and self.request.session.get('plot_box'):
            try:
                self.fig = pio.from_json(self.request.session['plot_box'])
            except Exception:
                pass

        return self.render_plot()


class HistogramViz(PlotViz):
    template_name = "myapp/plot/histogram.html"

    def __init__(self, request):
        super().__init__(request)
        # Initialize fig from session if it exists
        self.fig = None
        plot_data = self.request.session.get('plot_histogram')
        if plot_data:
            try:
                self.fig = pio.from_json(plot_data)
            except Exception:
                pass

    def create_plot(self):
        if "histogram_plot" in self.request.POST and not self.data.empty:
            self.update_from_post()
            plot_type = self.request.POST.get('plot_type', 'histogram')

            num_bins_str = self.request.POST.get("num_bins", "")
            bin_width_str = self.request.POST.get("bin_width", "")


            num_bins = int(num_bins_str) if num_bins_str.isdigit() else None
            bin_width = (
                float(bin_width_str)
                if bin_width_str.replace(".", "", 1).isdigit()
                else None
            )

            self.request.session["num_bins"] = num_bins
            self.request.session["bin_width"] = bin_width

            self.title_font_fix()

            x_axis_label = self.x_axis_label or self.x_column
            y_axis_label = self.y_axis_label or self.y_column

            if num_bins is not None:
                self.fig = px.histogram(
                    self.data,
                    x=self.x_column,
                    nbins=num_bins,
                    title=self.plot_title,
                    template=self.plot_style,
                )
            elif bin_width is not None:

                self.fig = px.histogram(
                    self.data,
                    x=self.x_column,
                    nbins=int(10 / bin_width),
                    title=self.plot_title,
                    template=self.plot_style,
                )
            else:
                self.fig = px.histogram(
                    self.data,
                    x=self.x_column,
                    title=self.plot_title,
                    template=self.plot_style,
                )

            if self.plot_color:
                self.fig.update_traces(marker_color=self.plot_color)

            self.fig.update_layout(
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                xaxis_title=x_axis_label,
                yaxis_title=y_axis_label,
                title=dict(text=self.plot_title, font_size=self.title_font_size),
            )
            
            self.request.session['plot_histogram'] = pio.to_json(self.fig)
            self.plot_div = pio.to_html(self.fig, full_html=False)

            plot_div_dict = self.request.session.get('plot_div', {})
            if not isinstance(plot_div_dict, dict):
                plot_div_dict = {}
            plot_div_dict[plot_type] = self.plot_div
            self.request.session['plot_div'] = plot_div_dict
            self.request.session.modified = True

        plot_div_dict = self.request.session.get('plot_div', {})
        self.plot_div = plot_div_dict.get('histogram') if isinstance(plot_div_dict, dict) else None

        if self.fig is None and self.request.session.get('plot_histogram'):
            try:
                self.fig = pio.from_json(self.request.session['plot_histogram'])
            except Exception:
                pass

        return self.render_plot()


class LineViz(PlotViz):
    template_name = "myapp/plot/line.html"

    def __init__(self, request):
        super().__init__(request)
        # Initialize fig from session if it exists
        self.fig = None
        plot_data = self.request.session.get('plot_line')
        if plot_data:
            try:
                self.fig = pio.from_json(plot_data)
            except Exception:
                pass

    def create_plot(self):
        if "line_plot" in self.request.POST and not self.data.empty:
            self.update_from_post()
            plot_type = self.request.POST.get('plot_type', 'line')

            self.line_width = int(self.request.POST.get("line_width", 2))
            self.legend_position = self.request.POST.get("legend_position", "top")

            self.request.session["line_width"] = self.line_width
            self.request.session["legend_position"] = self.legend_position

            x_axis_label = self.x_axis_label or self.x_column
            y_axis_label = self.y_axis_label or self.y_column

            self.title_font_fix()

            self.fig = px.line(
                self.data,
                x=self.x_column,
                y=self.y_column,
                title=self.plot_title,
                template=self.plot_style,
            )

            if self.plot_color:
                self.fig.update_traces(
                    line=dict(color=self.plot_color, width=self.line_width)
                )
            
            self.fig.update_layout(
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                xaxis_title=x_axis_label,
                yaxis_title=y_axis_label,
                legend=dict(yanchor="top", y=1.02, xanchor="center", x=0.5),
                title=dict(text=self.plot_title, font_size=self.title_font_size),
            )

            if self.legend_position == "bottom":
                self.fig.update_layout(
                    legend=dict(yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
            elif self.legend_position == "left":
                self.fig.update_layout(
                    legend=dict(yanchor="middle", y=0.5, xanchor="left", x=-0.1)
                )
            elif self.legend_position == "right":
                self.fig.update_layout(
                    legend=dict(yanchor="middle", y=0.5, xanchor="right", x=1.1)
                )

            self.request.session['plot_line'] = pio.to_json(self.fig)
            self.plot_div = pio.to_html(self.fig, full_html=False)

            plot_div_dict = self.request.session.get('plot_div', {})
            if not isinstance(plot_div_dict, dict):
                plot_div_dict = {}
            plot_div_dict[plot_type] = self.plot_div
            self.request.session['plot_div'] = plot_div_dict
            self.request.session.modified = True

        plot_div_dict = self.request.session.get('plot_div', {})
        self.plot_div = plot_div_dict.get('line') if isinstance(plot_div_dict, dict) else None

        if self.fig is None and self.request.session.get('plot_line'):
            try:
                self.fig = pio.from_json(self.request.session['plot_line'])
            except Exception:
                pass

        return self.render_plot()


class PieViz(PlotViz):
    template_name = "myapp/plot/pie.html"

    def __init__(self, request):
        super().__init__(request)
        # Initialize fig from session if it exists
        self.fig = None
        plot_data = self.request.session.get('plot_pie')
        if plot_data:
            try:
                self.fig = pio.from_json(plot_data)
            except Exception:
                pass

    def create_plot(self):
        if "pie_plot" in self.request.POST and not self.data.empty:
            self.update_from_post()
            plot_type = self.request.POST.get('plot_type', 'pie')

            self.hole_size = float(self.request.POST.get("hole_size", 0)) 
            self.label_position = self.request.POST.get("label_position", "inside")

            self.request.session["hole_size"] = self.hole_size
            self.request.session["label_position"] = self.label_position

            self.title_font_fix()

            self.fig = px.pie(
                self.data,
                names=self.x_column,
                values=self.y_column, 
                title=self.plot_title,
                template=self.plot_style,
            )

            if self.hole_size > 0:
                self.fig.update_traces(hole=self.hole_size)

            self.fig.update_traces(textposition=self.label_position) 
            self.fig.update_layout(
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                title=dict(text=self.plot_title, font_size=self.title_font_size)
            )

            self.request.session['plot_pie'] = pio.to_json(self.fig)
            self.plot_div = pio.to_html(self.fig, full_html=False)

            plot_div_dict = self.request.session.get('plot_div', {})
            if not isinstance(plot_div_dict, dict):
                plot_div_dict = {}
            plot_div_dict[plot_type] = self.plot_div
            self.request.session['plot_div'] = plot_div_dict
            self.request.session.modified = True

        plot_div_dict = self.request.session.get('plot_div', {})
        self.plot_div = plot_div_dict.get('pie') if isinstance(plot_div_dict, dict) else None

        if self.fig is None and self.request.session.get('plot_pie'):
            try:
                self.fig = pio.from_json(self.request.session['plot_pie'])
            except Exception:
                pass

        return self.render_plot()
    

class ScatterViz(PlotViz):
    template_name = "myapp/plot/scatter.html"

    def __init__(self, request):
        super().__init__(request)
        # Initialize fig from session if it exists
        self.fig = None
        plot_data = self.request.session.get('plot_scatter')
        if plot_data:
            try:
                self.fig = pio.from_json(plot_data)
            except Exception:
                pass

    def create_plot(self):
        if "scatter_plot" in self.request.POST and not self.data.empty:
            self.update_from_post()
            plot_type = self.request.POST.get('plot_type', 'scatter')

            self.marker_type = self.request.POST.get("marker_type", None)

            try:
                self.marker_size = int(self.request.POST.get("marker_size", "5"))
            except (ValueError, TypeError):
                self.marker_size = 5

            self.request.session["marker_type"] = self.marker_type
            self.request.session["marker_size"] = self.marker_size

            self.title_font_fix()

            x_axis_label = self.x_axis_label or self.x_column
            y_axis_label = self.y_axis_label or self.y_column


            self.fig = px.scatter(
                self.data,
                x=self.x_column,
                y=self.y_column,
                title=self.plot_title,
                template=self.plot_style,
            )

            if self.marker_type:
                self.fig.update_traces(marker=dict(symbol=self.marker_type))

            self.fig.update_traces(marker=dict(size=self.marker_size, color=self.plot_color))

            self.fig.update_layout(
                xaxis_title=x_axis_label,
                yaxis_title=y_axis_label,
                xaxis_showgrid=self.show_grid,
                yaxis_showgrid=self.show_grid,
                showlegend=self.show_legend,
                title=dict(text=self.plot_title, font_size=self.title_font_size),
            )

            self.request.session['plot_scatter'] = pio.to_json(self.fig)
            self.plot_div = pio.to_html(self.fig, full_html=False)

            plot_div_dict = self.request.session.get('plot_div', {})
            if not isinstance(plot_div_dict, dict):
                plot_div_dict = {}
            plot_div_dict[plot_type] = self.plot_div
            self.request.session['plot_div'] = plot_div_dict
            self.request.session.modified = True

        plot_div_dict = self.request.session.get('plot_div', {})
        self.plot_div = plot_div_dict.get('scatter') if isinstance(plot_div_dict, dict) else None

        if self.fig is None and self.request.session.get('plot_scatter'):
            try:
                self.fig = pio.from_json(self.request.session['plot_scatter'])
            except Exception:
                pass

        return self.render_plot()
    
    
def bar_viz(request):
    viz = BarViz(request)

    if viz.data.empty:
        messages.error(request, "Data is empty")
        return redirect('data')
    
    # Create plot
    plot_created = viz.create_plot()
    try:
        fig = pio.from_json(viz.request.session['plot_bar'])
    except:
        fig = None
    
    # Handle save request
    if 'save' in request.POST and plot_created:
        title = request.POST.get('plot_title', "Bar Plot")
        success, message = viz.save_plot(title, "Bar", fig)
        if success:
            messages.success(request, message)
            return redirect('/bar')
        else:
            messages.error(request, message)
    
    return viz.render_plot()


def box_viz(request):
    viz = BoxViz(request)

    if viz.data.empty:
        messages.error(request, "Data is empty")
        return redirect('data')
    
    # Create plot
    plot_created = viz.create_plot()
    try:
        fig = pio.from_json(viz.request.session['plot_box'])
    except:
        fig = None
    
    # Handle save request
    if 'save' in request.POST and plot_created:
        title = request.POST.get('plot_title', "Box Plot")
        success, message = viz.save_plot(title, "Box", fig)
        if success:
            messages.success(request, message)
            return redirect('/box')
        else:
            messages.error(request, message)
    
    return viz.render_plot()

def histogram_viz(request):
    viz = HistogramViz(request)

    if viz.data.empty:
        messages.error(request, "Data is empty")
        return redirect('data')
    
    # Create plot
    plot_created = viz.create_plot()
    try:
        fig = pio.from_json(viz.request.session['plot_histogram'])
    except:
        fig = None
    
    # Handle save request
    if 'save' in request.POST and plot_created:
        title = request.POST.get('plot_title', "Histogram Plot")
        success, message = viz.save_plot(title, "Histogram", fig)
        if success:
            messages.success(request, message)
            return redirect('/histogram')
        else:
            messages.error(request, message)
    
    return viz.render_plot()


def line_viz(request):
    viz = LineViz(request)

    if viz.data.empty:
        messages.error(request, "Data is empty")
        return redirect('data')
    
    # Create plot
    plot_created = viz.create_plot()
    try:
        fig = pio.from_json(viz.request.session['plot_line'])
    except:
        fig = None
    
    # Handle save request
    if 'save' in request.POST and plot_created:
        title = request.POST.get('plot_title', "Line Plot")
        success, message = viz.save_plot(title, "Line", fig)
        if success:
            messages.success(request, message)
            return redirect('/line')
        else:
            messages.error(request, message)
    
    return viz.render_plot()


def pie_viz(request):
    viz = PieViz(request)
    
    if viz.data.empty:
        messages.error(request, "Data is empty")
        return redirect('data')
    
    # Create plot
    plot_created = viz.create_plot()
    try:
        fig = pio.from_json(viz.request.session['plot_pie'])
    except:
        fig = None
    
    # Handle save request
    if 'save' in request.POST and plot_created:
        title = request.POST.get('plot_title', "Pie Plot")
        success, message = viz.save_plot(title, "Pie", fig)
        if success:
            messages.success(request, message)
            return redirect('/pie')
        else:
            messages.error(request, message)
    
    return viz.render_plot()


def scatter_viz(request):
    viz = ScatterViz(request)
    
    if viz.data.empty:
        messages.error(request, "Data is empty")
        return redirect('data')
    
    # Create plot
    plot_created = viz.create_plot()
    try:
        fig = pio.from_json(viz.request.session['plot_scatter'])
    except:
        fig = None
    
    # Handle save request
    if 'save' in request.POST and plot_created:
        title = request.POST.get('plot_title', "Scatter Plot")
        success, message = viz.save_plot(title, "Scatter", fig)
        if success:
            messages.success(request, message)
            return redirect('/scatter')
        else:
            messages.error(request, message)
    else:
        pass
    
    return viz.render_plot()


class DataHandler:
    def __init__(self, request):
        self.request = request
        self.page_obj = None
        self.columns = None
        self.user = request.user
        self.data = self.get_user_data()
        self.data_display = None 
        self.columns_display = None

    def format_number(self, value):
        if isinstance(value, (int, float)) and abs(value) >= 1000:
            return f"{value:,}"
        return value

    def data_for_display(self):
        if self.data.empty:
            return pd.DataFrame()

        self.data_display = self.data.copy()

        for column in self.data_display.columns:
            self.data_display[column] = self.data_display[column].apply(self.format_number)
        self.columns_display = list(self.data_display.columns)

        return self.data_display

    def get_user_data(self):
        if self.user.is_authenticated:
            try:
                csv_file = CSVFile.objects.filter(user=self.user).latest('uploaded_at') 
                data = pd.read_csv(csv_file.file.path)
                if 'Index' not in data.columns:
                    data['Index'] = data.index
                    cols = ['Index'] + [col for col in data.columns if col != 'Index']
                    data = data[cols]
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
            paginator = Paginator(self.data_display.values.tolist(), 10)
            page_number = self.request.GET.get("page")
            self.page_obj = paginator.get_page(page_number)
            if not self.columns_display:
                self.columns_display = list(self.data_display.columns)
    
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
    
class DeleteRowHandler(DataHandler):
    def process_request(self):
        row = self.request.POST.get("row_id")
        try:
            row = int(row)
        except ValueError:
            messages.error(self.request, f"Row must be integer.")
        if row in self.data["Index"].values:
            row_index = self.data[self.data['Index'] == row].index[0]
            self.data = self.data.drop(index=row_index)
            self.set_user_data(self.data)
            messages.success(self.request, f"Row with ID '{row}' has been deleted.")
        else:
            messages.error(self.request, f"Row '{row}' does not exist.")
        return redirect("/data")
    
class EditValueHandler(DataHandler):
    def process_request(self):
        column = self.request.POST.get("column")
        row = self.request.POST.get("row_id")
        value =  self.request.POST.get("new_value")
        try:
            row = int(row)
        except ValueError:
            messages.error(self.request, f"Row must be integer.")
        if row in self.data["Index"].values and column in self.data.columns:
            try:
                # Get the actual index where Index column matches row
                row_index = self.data[self.data['Index'] == row].index[0]
                
                # Try to convert value to appropriate type based on column data
                original_type = self.data[column].dtype
                if pd.api.types.is_numeric_dtype(original_type):
                    try:
                        if original_type == 'int64':
                            value = int(value)
                        else:
                            value = float(value)
                    except ValueError:
                        messages.error(self.request, f"Value must be a number for column '{column}'.")
                        return redirect("/data")
                elif original_type == 'bool':
                    value = value.lower() == 'true'
                
                # Update the value
                self.data.at[row_index, column] = value
                self.set_user_data(self.data)
                messages.success(self.request, f"Value in column '{column}' at row {row} has been updated.")
            
            except Exception as e:
                messages.error(self.request, f"Error updating value: {str(e)}")
        else:
            if row not in self.data["Index"].values:
                messages.error(self.request, f"Row '{row}' does not exist.")
            if column not in self.data.columns:
                messages.error(self.request, f"Column '{column}' does not exist.")
                
        return redirect("/data")

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
        elif "delete_row" in request.POST:
            handler = DeleteRowHandler(request)
        elif "edit_value" in request.POST:
            handler = EditValueHandler(request)

        if handler:
            response = handler.process_request()
            if response:
                return response

    handler = DataHandler(request)
    handler.data_for_display()
    handler.paginate_data()

    return render(
        request,
        "myapp/data.html",
        {
            "page_obj": handler.page_obj,  # Keep the page_obj for pagination controls
            "columns": handler.columns_display,
        },
    )


class DescribeData(DataHandler):
    def process_request(self):
        description = None
        description_display = None
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

                description_display = description.copy()

                for column in description_display.columns:
                    if pd.api.types.is_numeric_dtype(data[column]):
                        description_display[column] = description_display[column].apply(self.format_number)
                
                
                description_display = description_display.to_html(classes="table table-striped table-hover")
                
                column_info = []
                for column in columns:
                    info = {
                        'name': column,
                        'dtype': str(data[column].dtype),
                        'null_count': self.format_number(data[column].isnull().sum()),
                        'unique_count': self.format_number(data[column].nunique()),
                    }
                    if data[column].dtype in ['int64', 'float64']:
                        info['top_values'] = data[column].value_counts().head(3).to_dict()
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
            "description": description_display,
            "columns": columns,
            "column_info": column_info,
        }
        
        return render(self.request, "myapp/describe.html", context)
    
@login_required
def describe_data(request):
    handler = DescribeData(request)
    return handler.process_request()

@login_required
def export_plots(request):
    saved_plots = SavedPlot.objects.filter(user=request.user)
    
    # Serialize plots data
    plots_data = []
    for plot in saved_plots:
        plots_data.append({
            'id': plot.id,
            'title': plot.title,
            'plot_data': plot.plot_data,  # Assuming this is already JSON-serializable
            'uploaded_at': plot.uploaded_at,
        })
        print(plot.uploaded_at)
    context = {
        'saved_plots': saved_plots,  # For template iteration
        'saved_plots_json': json.dumps(plots_data, cls=DjangoJSONEncoder)  # For JavaScript
    }
    return render(request, 'myapp/export.html', context)