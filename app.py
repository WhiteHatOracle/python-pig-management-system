# =========================
# Standard Library Imports
# =========================
import os
import re
import uuid
import logging
import secrets
import traceback
import datetime as dt
from datetime import datetime, timedelta, timezone, date

# =========================
# Third-Party Libraries
# =========================
from dotenv import load_dotenv
from flask import (
    Flask, render_template, url_for, redirect, flash,
    make_response, request, jsonify, session, abort,
    get_flashed_messages, Blueprint
)
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from sqlalchemy import func, event, extract
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from authlib.integrations.flask_client import OAuth

# =========================
# Dash / Plotly
# =========================
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# =========================
# Application Modules
# =========================
from models import (
    db, Litter, User, Boars, Sows,
    ServiceRecords, Invoice, Expense,
    LitterManagement, VaccinationRecord, 
    WeightRecord, MortalityRecord, SaleRecord
)
from forms import (
    ResetPasswordForm, ForgotPasswordForm, LitterForm, SowForm,
    BoarForm, RegisterForm, LoginForm, FeedCalculatorForm,
    InvoiceGeneratorForm, ServiceRecordForm, ExpenseForm,
    CompleteFeedForm, ChangePasswordForm
)
from utils import (
    get_sow_service_records, parse_range, update_dashboard,
    get_total_counts, generate_invoice_pdf, get_litter_stage
)
from extensions import (
    db, login_manager, migrate
)
from dashboard_helpers import (
    get_herd_counts_by_stage, 
    get_upcoming_farrowings,
    get_active_litters_summary,
    get_theme_colors,
    get_sales_summary,
    get_financial_data,
    get_mortality_summary,
)


# =========================
# Logging & Environment Setup
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()   # Load environment variables from .env


# =========================
# Flask Application Setup
# =========================
app = Flask(__name__)

# Secret key (prefer ENV value in production)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

# Database & Mail Configuration
app.config.update(
    SQLALCHEMY_DATABASE_URI="sqlite:///database.db",
    SECRET_KEY=os.getenv("SECRET_KEY", "supercalifragilisticexpialidocious"),
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
)

# Make enumerate usable inside Jinja templates
app.jinja_env.globals.update(enumerate=enumerate)


# =========================
# SQLite Foreign Key Support
# =========================
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    """Ensure SQLite enforces foreign-key constraints."""
    if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()


# =========================
# Extension Initialization
# =========================
bcrypt = Bcrypt(app)
mail = Mail(app)

db.init_app(app)
login_manager.init_app(app)
migrate.init_app(app, db)

# Login Manager
login_manager.login_view = "signin"   # Redirect when auth is required

# =========================
# Import Models AFTER db.init_app()
# =========================
from models import User, Boars, Sows, ServiceRecords, Invoice, Expense, Litter

# =========================
# User Loader for Flask-Login
# =========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =========================
# OAuth Configuration (Google)
# =========================
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    userinfo_endpoint="https://openidconnect.googleapis.com/userinfo",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)


# =========================
# Dash Application (Internal Dashboard)
# =========================
dash_app = dash.Dash(
    __name__,
    server=app,
    url_base_pathname="/dashboard_internal/",
    external_stylesheets=[dbc.themes.BOOTSTRAP, "/static/css/dashboard.css"],
)

# Load user for login management
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Dashboard Layout with Charts
dash_app.layout = html.Div([
    html.Div([
        # Welcome Section (same as before)
        html.Div([
            html.Div([
                html.Div([
                    html.Span("👋", className="welcome-emoji"),
                    html.Div([
                        html.H1("Farm Dashboard", className="welcome-title"),
                        html.P("Monitor your herd and farm finances", className="welcome-subtitle"),
                    ], className="welcome-text"),
                ], className="welcome-content"),
                html.Div([
                    html.Span(id="current-date", className="current-date"),
                ], className="welcome-date"),
            ], className="welcome-header"),
        ], className="welcome-section"),

        # Herd Stats Section (condensed version)
        html.Div([
            html.Div([
                html.Div([
                    html.Span("🐷", className="section-icon"),
                    html.Span("Herd Overview", className="section-title"),
                ], className="section-header"),
            ], className="section-title-wrapper"),
            
            html.Div([
                # Total Herd
                html.Div([
                    html.Div([
                        html.H3(id="total-pigs", className="herd-value"),
                        html.P("Total Herd", className="herd-label"),
                    ], className="herd-inner"),
                ], className="herd-card featured"),

                # Sows
                html.Div([
                    html.Div([
                        html.H3(id="total-sows", className="herd-value"),
                        html.P("Sows", className="herd-label"),
                    ], className="herd-inner"),
                ], className="herd-card"),

                # Boars
                html.Div([
                    html.Div([
                        html.H3(id="total-boars", className="herd-value"),
                        html.P("Boars", className="herd-label"),
                    ], className="herd-inner"),
                ], className="herd-card"),

                # Growth Stages (combined)
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span(id="pre_weaners", className="stage-num"),
                            html.Span("Pre-W", className="stage-abbr"),
                        ], className="stage-item pre-weaning"),
                        html.Div([
                            html.Span(id="weaners", className="stage-num"),
                            html.Span("Wean", className="stage-abbr"),
                        ], className="stage-item weaner"),
                        html.Div([
                            html.Span(id="growers", className="stage-num"),
                            html.Span("Grow", className="stage-abbr"),
                        ], className="stage-item grower"),
                        html.Div([
                            html.Span(id="finishers", className="stage-num"),
                            html.Span("Fin", className="stage-abbr"),
                        ], className="stage-item finisher"),
                    ], className="stages-compact"),
                ], className="herd-card stages-card"),
            ], className="herd-grid"),
        ], className="herd-section"),

        # Upcoming Farrowings Section (same as before)
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.Span("📅", className="section-icon"),
                        html.Span("Upcoming Farrowings", className="section-title"),
                    ], className="section-header"),
                    html.Div([
                        html.Span(id="farrowing-count", className="count-badge"),
                    ], className="section-badge"),
                ], className="section-header-row"),
            ], className="table-section-header"),

            html.Div([
                dash_table.DataTable(
                    id="sow-service-table",
                    columns=[
                        {"name": "Sow ID", "id": "sow_id"},
                        {"name": "Service Date", "id": "service_date"},
                        {"name": "Litter Guard 1", "id": "litter_guard1_date"},
                        {"name": "Litter Guard 2", "id": "litter_guard2_date"},
                        {"name": "Due Date", "id": "due_date"},
                    ],
                    sort_action="native",
                    page_size=100,
                    style_table={'overflowX': 'auto', 'borderRadius': '12px'},
                    style_header={
                        'backgroundColor': '#059669',
                        'color': 'white',
                        'textAlign': 'center',
                        'fontWeight': '600',
                        'fontSize': '11px',
                        'textTransform': 'uppercase',
                        'padding': '12px 8px',
                    },
                    style_cell={
                        'padding': '12px 8px',
                        'textAlign': 'center',
                        'fontSize': '13px',
                        'border': 'none',
                        'borderBottom': '1px solid var(--border-light)',
                    },
                    style_data={
                        'backgroundColor': 'var(--bg-lighter)',
                        'color': 'var(--text-dark)',
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': 'var(--bg-lightest)'},
                        {'if': {'column_id': 'due_date'}, 'fontWeight': '600', 'color': '#059669'},
                    ],
                ),
            ], className="table-wrapper compact"),
        ], className="table-section compact"),

        # Financial Summary Cards
        html.Div([
            html.Div([
                html.Div([
                    html.Span("💰", className="section-icon"),
                    html.Span("Financial Overview", className="section-title"),
                ], className="section-header"),
                html.Div([
                    # Period selector
                    dcc.Dropdown(
                        id='period-selector',
                        options=[
                            {'label': 'Last 30 Days', 'value': '30'},
                            {'label': 'Last 3 Months', 'value': '90'},
                            {'label': 'Last 6 Months', 'value': '180'},
                            {'label': 'This Year', 'value': '365'},
                            {'label': 'All Time', 'value': 'all'},
                        ],
                        value='all',
                        clearable=False,
                        className='period-dropdown'
                    ),
                ], className="period-selector-wrapper"),
            ], className="section-header-row financial-header"),
        ], className="section-title-wrapper"),

        # Financial Stats Cards
        html.Div([
            # Total Revenue Card
            html.Div([
                html.Div([
                    html.Div([
                        html.Span("📈", className="finance-emoji"),
                    ], className="finance-icon-wrapper revenue"),
                    html.Div([
                        html.H2(id="total-revenue", className="finance-value revenue-value"),
                        html.P("Total Revenue", className="finance-label"),
                        html.Span(id="revenue-change", className="finance-change positive"),
                    ], className="finance-content"),
                ], className="finance-inner"),
            ], className="finance-card"),

            # Total Expenses Card
            html.Div([
                html.Div([
                    html.Div([
                        html.Span("📉", className="finance-emoji"),
                    ], className="finance-icon-wrapper expenses"),
                    html.Div([
                        html.H2(id="total-expenses", className="finance-value expenses-value"),
                        html.P("Total Expenses", className="finance-label"),
                        html.Span(id="expenses-change", className="finance-change negative"),
                    ], className="finance-content"),
                ], className="finance-inner"),
            ], className="finance-card"),

            # Net Profit Card
            html.Div([
                html.Div([
                    html.Div([
                        html.Span("💵", className="finance-emoji"),
                    ], className="finance-icon-wrapper profit"),
                    html.Div([
                        html.H2(id="net-profit", className="finance-value profit-value"),
                        html.P("Net Profit", className="finance-label"),
                        html.Span(id="profit-margin", className="finance-change"),
                    ], className="finance-content"),
                ], className="finance-inner"),
            ], className="finance-card highlight"),

            # Profit Margin Card
            html.Div([
                html.Div([
                    html.Div([
                        html.Span("📊", className="finance-emoji"),
                    ], className="finance-icon-wrapper margin"),
                    html.Div([
                        html.H2(id="profit-margin-pct", className="finance-value margin-value"),
                        html.P("Profit Margin", className="finance-label"),
                        html.Span(id="margin-status", className="finance-change"),
                    ], className="finance-content"),
                ], className="finance-inner"),
            ], className="finance-card"),
        ], className="finance-grid"),

        # Charts Section
        html.Div([
            # Secondary Charts Row
            html.Div([
                # Expense Breakdown Pie Chart
                html.Div([
                    html.Div([
                        html.Span("🥧", className="section-icon"),
                        html.Span("Expense Breakdown", className="section-title"),
                    ], className="chart-header"),
                    html.Div([
                        dcc.Graph(
                            id='expense-breakdown-chart',
                            config={
                                'displayModeBar': False,
                                'responsive': True,
                                'scrollZoom': False,
                                'doubleClick': False,
                                'staticPlot': True
                            },
                            className='pie-chart'
                        ),
                    ], className="chart-container"),
                ], className="chart-card"),

                # Revenue vs Expenses Chart (Main Chart)
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span("📊", className="section-icon"),
                            html.Span("Revenue vs Expenses", className="section-title"),
                        ], className="section-header"),
                        html.Div([
                            dcc.RadioItems(
                                id='chart-type-selector',
                                options=[
                                    {'label': ' Bar', 'value': 'bar'},
                                    {'label': ' Line', 'value': 'line'},
                                    {'label': ' Area', 'value': 'area'},
                                ],
                                value='bar',
                                className='chart-type-radio',
                                inputClassName='chart-radio-input',
                                labelClassName='chart-radio-label',
                            ),
                        ], className="chart-type-wrapper"),
                    ], className="chart-header"),
                    html.Div([
                        dcc.Graph(
                            id='revenue-expenses-chart',
                            config={
                                'displayModeBar': False,
                                'responsive': True,
                                'scrollZoom': False,
                                'doubleClick': False,
                                'staticPlot': True
                            },
                            className='main-chart'
                        ),
                    ], className="chart-container"),
                ], className="chart-card main-chart-card"),
            ], className="charts-row"),
        ], className="charts-section"),

        # Intervals and Location
        dcc.Interval(id="interval-update", interval=30 * 1000, n_intervals=0),
        dcc.Interval(id="chart-interval", interval=60 * 1000, n_intervals=0),
        dcc.Location(id='url', refresh=True),
        dcc.Store(id='theme-store', data='light'),
        html.Div(id='theme-detector', style={'display': 'none'}),

    ], className="dashboard-container"),
], className="dashboard-app")

# Add this after your dash_app.layout definition
dash_app.clientside_callback(
    """
    function(n) {
        // Check various ways theme might be set
        const html = document.documentElement;
        const body = document.body;
        
        const isDark = html.classList.contains('dark-theme') || 
                       html.classList.contains('dark-mode') ||
                       html.classList.contains('dark') ||
                       body.classList.contains('dark-theme') ||
                       body.classList.contains('dark-mode') ||
                       body.classList.contains('dark') ||
                       html.getAttribute('data-theme') === 'dark' ||
                       body.getAttribute('data-theme') === 'dark';
        
        return isDark ? 'dark' : 'light';
    }
    """,
    dash.Output('theme-store', 'data'),
    dash.Input('interval-update', 'n_intervals'),
)

# Callback for financial summary cards
@dash_app.callback(
    [
        dash.Output("total-revenue", "children"),
        dash.Output("total-expenses", "children"),
        dash.Output("net-profit", "children"),
        dash.Output("profit-margin-pct", "children"),
        dash.Output("revenue-change", "children"),
        dash.Output("expenses-change", "children"),
        dash.Output("profit-margin", "children"),
        dash.Output("margin-status", "children"),
        dash.Output("net-profit", "className"),
        dash.Output("profit-margin-pct", "className"),
    ],
    [dash.Input("period-selector", "value")],
)

def update_financial_summary(period):
    data = get_financial_data(period)
    
    total_revenue = f"K{data['total_revenue']:,.2f}"
    total_expenses = f"K{data['total_expenses']:,.2f}"
    net_profit = f"K{data['net_profit']:,.2f}"
    profit_margin = f"{data['profit_margin']:.1f}%"
    
    # Determine profit status
    if data['net_profit'] > 0:
        profit_class = "finance-value profit-value positive"
        margin_class = "finance-value margin-value positive"
        profit_status = "↑ Profitable"
        margin_status = "Healthy"
    elif data['net_profit'] < 0:
        profit_class = "finance-value profit-value negative"
        margin_class = "finance-value margin-value negative"
        profit_status = "↓ Loss"
        margin_status = "At Risk"
    else:
        profit_class = "finance-value profit-value"
        margin_class = "finance-value margin-value"
        profit_status = "Break Even"
        margin_status = "Neutral"
    
    # Calculate period change (simplified)
    revenue_change = f"↑ {len([v for v in data['revenue_by_month'].values() if v > 0])} months with sales"
    expenses_change = f"{len(data['expense_by_category'])} categories"
    
    return (
        total_revenue,
        total_expenses,
        net_profit,
        profit_margin,
        revenue_change,
        expenses_change,
        profit_status,
        margin_status,
        profit_class,
        margin_class,
    )

# Callback for Revenue vs Expenses chart
@dash_app.callback(
    dash.Output("revenue-expenses-chart", "figure"),
    [
        dash.Input("period-selector", "value"),
        dash.Input("chart-type-selector", "value"),
        dash.Input("chart-interval", "n_intervals"),
        dash.Input("theme-store", "data"),  # Add theme input
    ],
)

def update_revenue_expenses_chart(period, chart_type, n, theme):
    colors = get_theme_colors(theme)
    data = get_financial_data(period)
    
    # Combine all months
    all_months = sorted(set(list(data['revenue_by_month'].keys()) + list(data['expense_by_month'].keys())))
    
    if not all_months:
        # Return empty chart with theme-aware colors
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for selected period",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=colors['text_secondary'])
        )
        fig.update_layout(
            plot_bgcolor=colors['chart_bg'],
            paper_bgcolor=colors['chart_bg'],
            height=350,
        )
        return fig
    
    # Create dataframe
    df = pd.DataFrame({
        'Month': all_months,
        'Revenue': [data['revenue_by_month'].get(m, 0) for m in all_months],
        'Expenses': [data['expense_by_month'].get(m, 0) for m in all_months],
    })
    
    # Format month labels
    df['Month_Label'] = pd.to_datetime(df['Month']).dt.strftime('%b %Y')
    
    # Create chart based on type
    if chart_type == 'bar':
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Revenue',
            x=df['Month_Label'],
            y=df['Revenue'],
            marker_color=colors['revenue'],
            marker_line_width=0,
        ))
        fig.add_trace(go.Bar(
            name='Expenses',
            x=df['Month_Label'],
            y=df['Expenses'],
            marker_color=colors['expenses'],
            marker_line_width=0,
        ))
        fig.update_layout(barmode='group')
        
    elif chart_type == 'line':
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            name='Revenue',
            x=df['Month_Label'],
            y=df['Revenue'],
            mode='lines+markers',
            line=dict(color=colors['revenue'], width=3),
            marker=dict(size=8),
        ))
        fig.add_trace(go.Scatter(
            name='Expenses',
            x=df['Month_Label'],
            y=df['Expenses'],
            mode='lines+markers',
            line=dict(color=colors['expenses'], width=3),
            marker=dict(size=8),
        ))
        
    else:  # area
        fig = go.Figure()
        # Adjust fill colors based on theme
        revenue_fill = 'rgba(72, 187, 120, 0.3)' if theme == 'dark' else 'rgba(16, 185, 129, 0.3)'
        expense_fill = 'rgba(252, 129, 129, 0.3)' if theme == 'dark' else 'rgba(239, 68, 68, 0.3)'
        
        fig.add_trace(go.Scatter(
            name='Revenue',
            x=df['Month_Label'],
            y=df['Revenue'],
            fill='tozeroy',
            mode='lines',
            line=dict(color=colors['revenue'], width=2),
            fillcolor=revenue_fill,
        ))
        fig.add_trace(go.Scatter(
            name='Expenses',
            x=df['Month_Label'],
            y=df['Expenses'],
            fill='tozeroy',
            mode='lines',
            line=dict(color=colors['expenses'], width=2),
            fillcolor=expense_fill,
        ))
    
    # Update layout with theme-aware colors
    fig.update_layout(
        plot_bgcolor=colors['chart_bg'],
        paper_bgcolor=colors['chart_bg'],
        height=350,
        margin=dict(l=20, r=20, t=20, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, color=colors['text_primary']),
            bgcolor='rgba(0,0,0,0)',
        ),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor=colors['border_color'],
            tickfont=dict(size=11, color=colors['text_secondary']),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=colors['grid_color'],
            showline=False,
            tickfont=dict(size=11, color=colors['text_secondary']),
            tickprefix='K',
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor=colors['bg_secondary'],
            font_color=colors['text_primary'],
            bordercolor=colors['border_color'],
        ),
    )
    
    return fig

# Pie Chart Callback
@dash_app.callback(
    dash.Output("expense-breakdown-chart", "figure"),
    [
        dash.Input("period-selector", "value"),
        dash.Input("chart-interval", "n_intervals"),
        dash.Input("theme-store", "data"),  # Add theme input
    ],
)

# Pie Chart Update
def update_expense_breakdown(period, n, theme):
    colors = get_theme_colors(theme)
    data = get_financial_data(period)
    
    categories = list(data['expense_by_category'].keys())
    values = list(data['expense_by_category'].values())
    
    if not categories:
        fig = go.Figure()
        fig.add_annotation(
            text="No expenses recorded",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=colors['text_secondary'])
        )
        fig.update_layout(
            plot_bgcolor=colors['chart_bg'],
            paper_bgcolor=colors['chart_bg'],
            height=300,
        )
        return fig
    
    # Color palette - slightly adjusted for dark theme visibility
    if theme == 'dark':
        pie_colors = ['#48BB78', '#63B3ED', '#F6AD55', '#FC8181', '#B794F4', '#F687B3', '#4FD1C5', '#9AE6B4']
    else:
        pie_colors = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16']
    
    fig = go.Figure(data=[go.Pie(
        labels=categories,
        values=values,
        hole=0.55,
        marker=dict(colors=pie_colors[:len(categories)]),
        textinfo='percent',
        textposition='outside',
        textfont=dict(size=11, color=colors['text_primary']),
        hovertemplate="<b>%{label}</b><br>K%{value:,.2f}<br>%{percent}<extra></extra>",
        outsidetextfont=dict(color=colors['text_primary']),
    )])
    
    # Add center text with theme-aware colors
    total = sum(values)
    fig.add_annotation(
        text=f"K{total:,.0f}",
        x=0.5, y=0.55,
        font=dict(size=18, color=colors['pie_center_text'], family='Poppins'),
        showarrow=False,
    )
    fig.add_annotation(
        text="Total",
        x=0.5, y=0.45,
        font=dict(size=12, color=colors['text_secondary']),
        showarrow=False,
    )
    
    fig.update_layout(
        plot_bgcolor=colors['chart_bg'],
        paper_bgcolor=colors['chart_bg'],
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color=colors['text_primary']),
            bgcolor='rgba(0,0,0,0)',
        ),
        hoverlabel=dict(
            bgcolor=colors['bg_secondary'],
            font_color=colors['text_primary'],
            bordercolor=colors['border_color'],
        ),
    )
    
    return fig

@dash_app.callback(
    dash.Output("monthly-profit-chart", "figure"),  # If you have this chart
    [
        dash.Input("period-selector", "value"),
        dash.Input("chart-interval", "n_intervals"),
        dash.Input("theme-store", "data"),  # Add theme input
    ],
)

def update_monthly_profit(period, n, theme):
    colors = get_theme_colors(theme)
    data = get_financial_data(period)
    
    all_months = sorted(set(list(data['revenue_by_month'].keys()) + list(data['expense_by_month'].keys())))
    
    if not all_months:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=colors['text_secondary'])
        )
        fig.update_layout(
            plot_bgcolor=colors['chart_bg'],
            paper_bgcolor=colors['chart_bg'],
            height=300,
        )
        return fig
    
    # Calculate profit/loss for each month
    profits = []
    bar_colors = []
    for m in all_months:
        rev = data['revenue_by_month'].get(m, 0)
        exp = data['expense_by_month'].get(m, 0)
        profit = rev - exp
        profits.append(profit)
        bar_colors.append(colors['positive'] if profit >= 0 else colors['negative'])
    
    month_labels = [datetime.strptime(m, '%Y-%m').strftime('%b %Y') for m in all_months]
    
    fig = go.Figure(data=[go.Bar(
        x=month_labels,
        y=profits,
        marker_color=bar_colors,
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>K%{y:,.2f}<extra></extra>",
    )])
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color=colors['text_muted'], line_width=1)
    
    fig.update_layout(
        plot_bgcolor=colors['chart_bg'],
        paper_bgcolor=colors['chart_bg'],
        height=300,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor=colors['border_color'],
            tickfont=dict(size=10, color=colors['text_secondary']),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=colors['grid_color'],
            showline=False,
            tickfont=dict(size=10, color=colors['text_secondary']),
            tickprefix='K',
            zeroline=False,
        ),
        hoverlabel=dict(
            bgcolor=colors['bg_secondary'],
            font_color=colors['text_primary'],
            bordercolor=colors['border_color'],
        ),
    )
    
    return fig

# Main callback to update herd data and table
@dash_app.callback(
    [
        dash.Output("total-pigs", "children"),
        dash.Output("total-sows", "children"),
        dash.Output("total-boars", "children"),
        dash.Output("pre_weaners", "children"),
        dash.Output("weaners", "children"),
        dash.Output("growers", "children"),
        dash.Output("finishers", "children"),
        dash.Output("sow-service-table", "data"),
        dash.Output("farrowing-count", "children"),
        dash.Output("current-date", "children"),
    ],
    [dash.Input("interval-update", "n_intervals")],
)

def callback_update_dashboard(n_intervals):
    from datetime import datetime
    
    # Get dashboard data
    (
        total_pigs,
        total_sows,
        total_boars,
        pre_weaners,
        weaners,
        growers,
        finishers,
        table_data
    ) = update_dashboard(n_intervals)
    
    # Calculate farrowing count
    farrowing_count = len(table_data) if table_data else 0
    farrowing_text = f"{farrowing_count} sow{'s' if farrowing_count != 1 else ''}"
    
    # Current date
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    
    return (
        total_pigs,
        total_sows,
        total_boars,
        pre_weaners,
        weaners,
        growers,
        finishers,
        table_data,
        farrowing_text,
        current_date,
    )

# Flask Route for Dash App
@app.route("/dashboard/")
def dashboard():
    return render_template("dashboard.html")

@app.route('/home', methods=['GET','POST'])
def home():
    return render_template('home.html')

# login route
@app.route('/')
def login():
    return render_template('login.html')  # Displays Homepage

#payement route
@app.route('/payment_plans', methods=['GET','POST'])
def payment_plans():
    return render_template('payment_plans.html')

# Sign in route
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.identifier.data.strip()

        if re.match(r"[^@]+@[^@]+\.[^@]+", username):
            user = User.query.filter_by(email=username).first()
        else:
            user =User.query.filter_by(username=username).first()
            
        if user:
            if not user.is_verified:
                flash("Please verify your email before logging in.", "Error")
                return render_template('signin.html', form=form)
            if user.password is not None:
                # Check password for local users
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user, remember=form.remember.data)
                    return redirect(url_for('dashboard'))
                else:
                    flash("Invalid Password, Please try again.", "Error")
            else:
                # Handle Google users
                flash("This account is set up for Google login. Please use Google to log in.", "Error")
        else:
            flash("User does not exist. Please register.","Error")
    return render_template('signin.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        # check for an existing username
        existing_user =User.query.filter_by(username=form.username.data.strip()).first()
        if existing_user:
            flash("The username already exists. Try something different, maybe your farm name?? :)", "Error")
            return render_template('signup.html', form=form)
        
        # check if email already exists
        existing_email = User.query.filter_by(email=form.email.data.strip()).first()
        if existing_email:
            flash("Looks like that email is already registered. Forgotten your password?", "Error")
            return render_template('signup.html', form = form)

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        token = str(uuid.uuid4())
        expiry_time = datetime.now(dt.timezone.utc) + timedelta(minutes=5)  # Link expires in 24 hours

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            verification_token=token,
            verification_expiry=expiry_time,
            is_verified=False
        )
        try:
            db.session.add(new_user)
            db.session.commit()

            # Create verification email
            verify_url = url_for('verify_email', token=token, _external=True)
            msg = Message(
                subject="Welcome to Pig Management System – Verify Your Email",
                sender=("Pig Management System", app.config['MAIL_USERNAME']),
                recipients=[form.email.data]
            )

            # Plain text version
            msg.body = f"""Hi {form.username.data},

            Thanks for signing up for Pig Management System!

            Please confirm your email address by clicking the link below:
            {verify_url}

            This link will expire in 24 hours.

            If you didn’t sign up, you can ignore this message.

            Cheers,
            The Pig Management System Team
            """

            # HTML version
            msg.html = f"""
            <p>Hi {form.username.data},</p>
            <p>Thanks for signing up for <strong>Pig Management System</strong>!</p>
            <p>Please confirm your email address by clicking the link below:</p>
            <p><a href="{verify_url}" style="color: #1a73e8;">Verify My Email</a></p>
            <p><strong>This link will expire in 24 hours.</strong></p>
            <p>If you didn’t sign up, you can ignore this message.</p>
            <p>Cheers,<br>The Pig Management System Team</p>
            """

            # Send email
            email_sent = False
            try:
                mail.send(msg)
                email_sent = True
            except Exception as e:
                app.logger.error("Email send failed:\n" + traceback.format_exc())
                flash(f"Registration successful, but we couldn't send the verification email.", "Error")

            if email_sent:
                flash("Registration successful! Please check your email to verify your account.", "Success")

            return redirect(url_for('signin'))

        except Exception as e:
            db.session.rollback()
            app.logger.error("Database error:\n" + traceback.format_exc())
            flash("An error occurred during registration. Please try again.", "Error")

    return render_template('signup.html', form=form)

@app.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()

    if user:
        if user.verification_expiry:
            expiry = user.verification_expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) > expiry:
                db.session.delete(user)
                db.session.commit()
                flash("Verification link expired. Please register again","Error")
                return redirect(url_for('signup'))

        # If the token is valid and not expired, verify the user
        user.is_verified = True
        user.verification_token = None
        user.verification_expiry = None
        db.session.commit()
        flash("Your email has been verified. You can now log in.", "Success")
    else:
        flash("Invalid or expired verification link.", "Error")
    return redirect(url_for('signin'))

# Google login route
@app.route('/google-login')
def google_login():
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)

#google auth callback route
@app.route('/auth')
def google_auth():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()

    email = user_info['email']
    google_id = user_info.get('id')

    # Check if user already exists by email OR google_id
    user = User.query.filter(
        (User.email == email) | (User.google_id == google_id)
    ).first()

    if user is None:
        # Create a new user with Google info
        user = User(
            username=email,
            email=email,
            google_id=google_id,
            name=user_info.get('name'),
            profile_pic=user_info.get('picture'),
            password=None,  # No password for Google users
            is_verified=True  # Google emails are verified
        )
        db.session.add(user)
    else:
        # Update user info so it's always current
        user.google_id = google_id
        user.name = user_info.get('name')
        user.profile_pic = user_info.get('picture')

    db.session.commit()

    # Log the user in
    login_user(user)
    flash("Logged in successfully with Google!", "success")
    return redirect(url_for('dashboard'))

# Logout route
@app.route('/logout', methods=['POST','GET'])
@login_required
def logout():
    logout_user() # Logout the current user
    flash("You have been logged out.","Success")
    return redirect(url_for('login'))

@app.route('/complete-feeds-calculator', methods=['GET','POST'])
@login_required
def complete_feeds():
    #Get input from the front end
    form = CompleteFeedForm()
    result = None #initialize result

    if form.validate_on_submit():
        # Validate inputs for non-negative values
        if form.numberOfPigs.data <= 0 or form.consumption.data <= 0 or form.costOfFeed.data <= 0 or form.numberOfDays.data <= 0:
            flash("Please enter positive values for all fields.", "error")
            return redirect(url_for('complete_feeds'))
        
        #perfom calculations
        dailyConsumption = form.numberOfPigs.data * float(form.consumption.data)
        total_feed = dailyConsumption * form.numberOfDays.data
        num_of_bags = round(total_feed/50)
        total_cost = num_of_bags*form.costOfFeed.data

        result={
            "totalFeed": total_feed,
            "numOfBags": num_of_bags,
            "totalCost": total_cost,
            "numOfDays": form.numberOfDays.data,
            "numOfPigs": form.numberOfPigs.data,
            "feed": form.feedName.data
        }

    return render_template('complete-feeds.html', form=form, result=result)

# Feed management route
@app.route('/calculate', methods=['GET','POST'])
@login_required
def calculate():
    # Get input data from the frontend
    form = FeedCalculatorForm()
    result = None #initialize result
    if form.validate_on_submit():
        # validate inputs are non negative numbers
        if form.days.data <= 0 or form.pigs.data <= 0 or form.feed_consumption.data <= 0 or form.feed_cost.data <= 0 or form.num3_meal_cost.data <= 0:
            flash("Please enter positive values for all fields.", "error")
            return redirect(url_for('calculate'))

        # Perform calculations
        total_feed = form.days.data * form.pigs.data * float(form.feed_consumption.data)

        concentrates = round(0.4 * total_feed)
        num_of_bags = round(concentrates / 50)
        conc_cost = num_of_bags * float(form.feed_cost.data)

        num3_meal = round(0.6 * total_feed, 2)
        num3_meal_total_cost = num3_meal * float(form.num3_meal_cost.data)

        total_cost = conc_cost + num3_meal_total_cost

        # Prepare the result
        result = {
            "totalFeed": total_feed,
            "numOfBags": num_of_bags,
            "concCost": conc_cost,
            "num3Meal": num3_meal,
            "num3MealTotalCost": num3_meal_total_cost,
            "totalCost": total_cost,
            "feed": form.feed.data,
            "pigs": form.pigs.data,
            "days": form.days.data
        }
    return render_template('feed-calculator.html', form = form, result = result)

# Invoice Generator route
@app.route('/invoice-generator', methods=['GET','POST'])
@login_required
def invoice_Generator():
    form = InvoiceGeneratorForm()
    if form.validate_on_submit():
        company_name = form.company.data
        invoice_date = form.invoice_date.data if form.invoice_date.data else date.today()
        weights = [float(w.strip()) for w in form.weights.data.split(',')if w.strip() != '']


        #Ensure there are weights provided
        if not weights:
            flash("Please enter valid weights.", "Error")
            return redirect(url_for('invoice_Generator'))

        # Parse weight ranges and prices
        first_min, first_max = parse_range(form.firstBandRange.data)
        first_price = form.firstBandPrice.data

        second_min, second_max = parse_range(form.secondBandRange.data)
        second_price = form.secondBandPrice.data

        third_min, third_max = parse_range(form.thirdBandRange.data)
        third_price = form.thirdBandPrice.data

        # Calculate prices based on weights
        invoice_data = []
        total_cost = 0
        total_weight = sum(weights)
        average_weight = total_weight / len(weights) if weights else 0
        total_pigs = len(weights)
        print(total_pigs)

        for weight in weights:
            if first_min <= weight <= first_max:
                price = float(first_price)
            elif second_min <= weight <= second_max:
                price = float(second_price)
            elif third_min <= weight <= third_max:
                price = float(third_price)
            else:
                price = 0  # Weight falls outside defined ranges

            cost = weight * price
            total_cost += cost
            invoice_data.append({
                    "weight": round(weight, 2),
                    "formatted_weight": f"{weight}kg",
                    "price": price,  # Keep raw price
                    "formatted_price": f"K{price:,.2f}",  # Format price as currency
                    "cost": cost,  # Keep raw cost
                    "formatted_cost": f"K{cost:,.2f}",  # Format cost as currency
                    "Number_of_Pigs": f"{total_pigs}",
                })
        return render_template('invoiceGenerator.html', 
                               form=form, 
                               company_name=company_name,
                               invoice_data=invoice_data, 
                               total_pigs=total_pigs,
                               total_cost=f"K{total_cost:,.2f}",
                               total_weight=f"{total_weight:,.2f}Kg",
                               average_weight = f"{average_weight:,.2f}Kg",
                               invoice_date = invoice_date.strftime('%B %d, %Y')
                               )

    return render_template('invoiceGenerator.html', form=form)

@app.route('/download-invoice', methods=['POST'])
@login_required
def download_invoice():
    invoice_data = eval(request.form.get("invoice_data"))  # Parse invoice data passed from the form
    company_name = request.form.get("company_name")
    total_weight = float(request.form.get("total_weight").replace("Kg", "").replace(",", ""))
    average_weight = float(request.form.get("average_weight").replace("Kg", "").replace(",",""))
    total_cost = float(request.form.get("total_cost").replace("K", "").replace(",", ""))
    total_pigs = int(request.form.get("total_pigs"))

     # Get invoice_date from form and parse it
    invoice_date_str = request.form.get("invoice_date")
    try:
        # Parse the formatted date string (e.g., "January 15, 2025")
        invoice_date = datetime.strptime(invoice_date_str, '%B %d, %Y').date()
    except (ValueError, TypeError):
        # Fallback to today's date if parsing fails
        invoice_date = date.today()

    #generate unique invoice number
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    #store invoice data in db just before downloading
    new_invoice = Invoice(
        invoice_number=invoice_number,
        num_of_pigs=total_pigs,
        company_name=company_name,
        date=invoice_date,
        total_weight=total_weight,
        average_weight=average_weight,
        total_price=total_cost,
        user_id=current_user.id
    )
    db.session.add(new_invoice)
    db.session.commit()

    pdf = generate_invoice_pdf(company_name, invoice_number, invoice_data, total_weight, average_weight, total_cost)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={invoice_number}.pdf'
    return response

@app.route('/invoices', methods=['GET','POST'])
@login_required
def invoices():
    # Pagination setup
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of invoices per page
    invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.date.desc()).paginate(page=page,per_page=per_page, error_out=False)
    invoices_list = invoices.items

    return render_template('invoices.html', invoices=invoices_list, pagination=invoices)

@app.route('/invoice_totals', methods=['GET'])
@login_required
def invoice_totals():
    total_weight    = db.session.query(db.func.sum(Invoice.total_weight))   .filter(Invoice.user_id == current_user.id).scalar() or 0
    total_revenue   = db.session.query(db.func.sum(Invoice.total_price))    .filter(Invoice.user_id == current_user.id).scalar() or 0
    avg_weight      = db.session.query(db.func.avg(Invoice.average_weight)) .filter(Invoice.user_id == current_user.id).scalar() or 0
    total_pigs      = db.session.query(db.func.sum(Invoice.num_of_pigs))    .filter(Invoice.user_id == current_user.id).scalar() or 0

    return jsonify({
        'total_weight': f"{total_weight:,.2f}Kg",
        'total_revenue': f"K{total_revenue:,.2f}",
        'average_weight': f"{avg_weight:,.2f}Kg",
        'total_pigs': f"{total_pigs:,.0f}"
    })

# Delete Invoice Route
@app.route('/delete-invoice/<int:invoice_id>', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(invoice)
        db.session.commit()
        flash('Invoice deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting invoice: {str(e)}', 'error')

    return redirect(url_for('invoices'))    

@app.route('/boar-manager', methods=['GET','POST'])
@login_required
def boars():
    form = BoarForm()

    if form.validate_on_submit():
        boar_id = re.sub(r'\s+', '', form.BoarId.data).upper()
        breed = re.sub(r'\s+', '', form.Breed.data).upper()
        boar_dob = form.DOB.data

        #add boar to the database
        try:
            new_boar = Boars(
                BoarId = boar_id,
                DOB = boar_dob,
                Breed=breed,
                user_id=current_user.id
                )
            db.session.add(new_boar)
            db.session.commit()
            flash(f'{boar_id} added successfully!', 'success')
            return redirect(url_for('boars'))
        except IntegrityError:
            db.session.rollback()
            flash(f'{boar_id} already exists!', 'error')
            return redirect(url_for('boars'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            
    page =request.args.get('page',1,type=int)
    per_page = 20
    boars = Boars.query.filter_by(user_id=current_user.id).order_by(Boars.DOB).paginate(page=page, per_page=per_page,error_out=False)  # Only show the boars owned by the current user
    return render_template('boars.html', boars=boars, form=form, pagination=boars)  
  
@app.route('/delete-boar/<string:BoarId>', methods=['POST'])
@login_required
def delete_boar(BoarId):
    boar = Boars.query.filter_by(BoarId = BoarId.upper(), user_id=current_user.id).first_or_404()
    if not boar:
        flash('Boar not found!', 'error')
        return redirect(url_for('boars'))

    try:
        db.session.delete(boar)
        db.session.commit()
        flash('Boar deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting boar: {str(e)}', 'error')

    return redirect(url_for('boars'))

@app.route('/edit-boar/<int:boar_id>', methods=['GET', 'POST'])
@login_required
def edit_boar(boar_id):

    boar = Boars.query.filter_by(id = boar_id, user_id=current_user.id).first_or_404()
    form = BoarForm(obj=boar)  # Pre-fill form with existing data
    form.boar_id = boar.id #prevents false validation errors

    if form.validate_on_submit():

        # Update the boar with new values
        boar.BoarId = form.BoarId.data.upper()
        boar.Breed = form.Breed.data.upper()
        boar.DOB = form.DOB.data

        try:
            db.session.commit()
            flash('Updated successfully!', 'success')
            return redirect(url_for('boars'))  # Redirect to the main boar manager
        except IntegrityError:
            db.session.rollback()
            flash(f'{form.BoarId.data.upper()} already exists!', 'error')
            # Render the template to show the error message
            return render_template('edit_boar.html', form=form, boar=boar)
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            # Render the template to show the error message
            return render_template('edit_boar.html', form=form, boar=boar)

    return render_template('edit_boar.html', form=form, boar=boar)

@app.route('/sow-manager', methods=['GET', 'POST'])
@login_required
def sows():
    form = SowForm()

    if form.validate_on_submit():
        sow_id = re.sub(r'\s+', '', form.sowID.data).upper()
        breed = re.sub(r'\s+', '', form.Breed.data).upper()
        dob_str = form.DOB.data       

        try:
            # Add sow to the database
            new_sow = Sows(
                sowID=sow_id,
                DOB=dob_str,
                Breed=breed,
                user_id=current_user.id)
            db.session.add(new_sow)
            db.session.commit()
            flash(f'{sow_id} successfully added!', 'success')
            return redirect(url_for('sows'))
        except IntegrityError:
            db.session.rollback()
            flash(f'{sow_id} already exists!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
    
    page = request.args.get('page',1,type=int)
    per_page = 20
    sows = Sows.query.filter_by(user_id=current_user.id).order_by(Sows.DOB).paginate(page=page, per_page=per_page,error_out=False)
    return render_template('sows.html', sows=sows, form=form, pagination=sows)

@app.route('/edit-sow/<int:sow_id>', methods=['GET', 'POST'])
@login_required
def edit_sow(sow_id):

    sow = Sows.query.filter_by(id=sow_id, user_id=current_user.id).first_or_404()
    form = SowForm(sow_id=sow.id, obj=sow)  # Pre-fill form with existing data
    form.sow_id = sow.id #prevents false validation errors

    if form.validate_on_submit():

        # Update the sow with new values
        sow.sowID = form.sowID.data.upper()
        sow.Breed = form.Breed.data.upper()
        sow.DOB = form.DOB.data

        try:
            db.session.commit()
            flash('Updated successfully!', 'success')
            return redirect(url_for('sows'))
        except IntegrityError:
            db.session.rollback()
            flash(f'{sow.sowID} already exists!', 'error')
            return redirect(url_for('edit_sow', sow_id=sow.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('edit_sow', sow_id=sow.id))

    return render_template('edit_sow.html', form=form, sow=sow)

@app.route('/delete-sow/<string:sow_id>', methods=['POST','GET'])
@login_required
def delete_sow(sow_id):
    sow = Sows.query.filter_by(sowID=sow_id.upper(), user_id=current_user.id).first_or_404()
    if not sow:
        flash('Sow not found!', 'error')
        return redirect(url_for('sows'))

    db.session.delete(sow)
    db.session.commit()
    flash('Sow deleted successfully!', 'success')
    return redirect(url_for('sows'))

@app.route('/sows/<int:sow_id>', methods=['GET', 'POST'])
@login_required
def sow_service_records(sow_id):
    sow = Sows.query.filter_by(id=sow_id, user_id=current_user.id).first_or_404()
    boars = Boars.query.filter_by(user_id=current_user.id).all()  # Only show the boars owned by the current user
    form = ServiceRecordForm()

    if not boars:
        form.boar_used.choices = [('ai','Artificial Insemination')]
    else:
        boar_choices = [(str(boar.id),boar.BoarId)for boar in boars]
        boar_choices.append(('ai','Artificial Insemination'))
        form.boar_used.choices = boar_choices

    if form.validate_on_submit():  # Checks if the form was submitted and is valid
        
        boar_used_value = form.boar_used.data  # string, e.g. "3" or "ai"
        service_date = form.service_date.data

        if boar_used_value.lower() == "ai":
            boar_used = "ARTIFICIAL INSEMINATION"
        else:
            boar = Boars.query.filter_by(id=int(boar_used_value), user_id=current_user.id).first_or_404()
            boar_used = boar.BoarId.upper()


        # Calculate other dates
        checkup_date = service_date         + timedelta(days=21)
        litter_guard1_date = service_date   + timedelta(days=68)
        feed_up_date = service_date         + timedelta(days=90)
        litter_guard2_date = service_date   + timedelta(days=100)
        action_date = service_date          + timedelta(days=109)
        due_date = service_date             + timedelta(days=114)

        # Create and add new service record
        new_record = ServiceRecords(
            sow_id=sow.id,
            service_date=service_date,
            boar_used=boar_used,
            checkup_date=checkup_date,
            litter_guard1_date=litter_guard1_date,
            litter_guard2_date=litter_guard2_date,
            feed_up_date=feed_up_date,
            due_date=due_date,
            action_date=action_date
        )
        db.session.add(new_record)
        db.session.commit()        
        flash('Service record added successfully!', 'success')
        return redirect(url_for('sow_service_records', sow_id=sow.id))
       

    return render_template('sow_service_records.html', sow=sow, form=form)

# Helper function to parse dates from form
def parse_date(date_string):
    """Parse date string in dd-mm-YYYY format"""
    if date_string:
        try:
            return datetime.strptime(date_string, '%d-%m-%Y').date()
        except ValueError:
            return None
    return None

# Helper function to determine litter stage
def get_litter_stage(farrow_date):
    """Determine the growth stage based on age"""
    if not farrow_date:
        return 'unknown'
    
    age_days = (date.today() - farrow_date).days
    
    if age_days < 0:
        return 'unknown'
    elif age_days <= 21:
        return 'preweaning'
    elif age_days <= 56:
        return 'weaner'
    elif age_days <= 98:
        return 'grower'
    else:
        return 'finisher'

# ==================== MAIN LITTER RECORDS ROUTE ====================
@app.route('/litter-records/<int:service_id>', methods=['GET', 'POST'])
@login_required
def litter_records(service_id):
    form = LitterForm()
    serviceRecord = ServiceRecords.query.get_or_404(service_id)

    # Authorization check
    if serviceRecord.sow.user_id != current_user.id:
        abort(403)

    sow_id = serviceRecord.sow_id
    existing_litter = serviceRecord.litter
    sow = Sows.query.filter_by(id=sow_id, user_id=current_user.id).first_or_404()

    # Prepare litters list with stage
    litters = [existing_litter] if existing_litter else []

    # Get related records if litter exists
    management_records = []
    vaccination_records = []
    weight_records = []
    mortality_records = []
    sale_records = []
    upcoming_vaccinations = []
    total_revenue = 0

    if existing_litter:
        management_records = existing_litter.management_records
        vaccination_records = sorted(existing_litter.vaccination_records, key=lambda x: x.date, reverse=True)
        weight_records = sorted(existing_litter.weight_records, key=lambda x: x.date, reverse=True)
        mortality_records = sorted(existing_litter.mortality_records, key=lambda x: x.date, reverse=True)
        sale_records = sorted(existing_litter.sale_records, key=lambda x: x.date, reverse=True)
        
        # Get upcoming vaccinations
        upcoming_vaccinations = [v for v in vaccination_records if v.next_due_date and v.next_due_date >= date.today()]
        
        # Calculate total revenue
        total_revenue = sum(s.total_amount or 0 for s in sale_records)

    # Handle POST for adding new litter
    if form.validate_on_submit():
        if existing_litter:
            flash("This service record already has an associated litter. You can't add another.", "error")
            return redirect(url_for('litter_records', service_id=service_id))

        farrowDate = form.farrowDate.data
        totalBorn = form.totalBorn.data
        bornAlive = form.bornAlive.data
        stillBorn = form.stillBorn.data
        mummified = form.mummified.data if hasattr(form, 'mummified') else 0

        # Parse weights
        try:
            weights = [float(w.strip()) for w in form.weights.data.split(',') if w.strip()]
        except ValueError:
            flash('Please enter valid numeric weight values separated by commas.', 'error')
            return redirect(url_for('litter_records', service_id=service_id))

        # Validate weights count
        if not weights or len(weights) != bornAlive:
            flash('Number of weights must match the number of piglets born alive!', 'error')
            return redirect(url_for('litter_records', service_id=service_id))
        
        # Validate totals
        if stillBorn + bornAlive != totalBorn:
            flash('The total number of piglets born must equal still born plus born alive!', 'error')
            return redirect(url_for('litter_records', service_id=service_id))

        averageWeight = round(sum(weights) / len(weights), 1)

        # Calculate procedure dates
        iron_injection_date = farrowDate + timedelta(days=3)
        tail_docking_date = farrowDate + timedelta(days=3)
        castration_date = farrowDate + timedelta(days=3)
        teeth_clipping_date = farrowDate + timedelta(days=3)
        wean_date = farrowDate + timedelta(days=28)

        new_litter = Litter(
            sow_id=sow_id,
            service_id=serviceRecord.id,
            farrowDate=farrowDate,
            totalBorn=totalBorn,
            bornAlive=bornAlive,
            stillBorn=stillBorn,
            mummified=mummified,
            averageWeight=averageWeight,
            weights=form.weights.data,  # Store original weights string
            iron_injection_date=iron_injection_date,
            tail_docking_date=tail_docking_date,
            castration_date=castration_date,
            wean_date=wean_date,
            teeth_clipping_date=teeth_clipping_date
        )

        try:
            db.session.add(new_litter)
            db.session.commit()
            flash('Litter recorded successfully!', 'success')
            return redirect(url_for('litter_records', service_id=service_id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while saving the litter: {str(e)}', 'error')

    return render_template(
        'litterRecord.html',
        form=form,
        sow=sow,
        serviceRecord=serviceRecord,
        litters=litters,
        sow_id=sow_id,
        existing_litter=existing_litter,
        service_id=service_id,
        # New data for tabs
        management_records=management_records,
        vaccination_records=vaccination_records,
        weight_records=weight_records,
        mortality_records=mortality_records,
        sale_records=sale_records,
        upcoming_vaccinations=upcoming_vaccinations,
        total_revenue=total_revenue
    )

# ==================== LITTER MANAGEMENT ROUTES ====================
@app.route('/litter/<int:litter_id>/management', methods=['POST'])
@login_required
def litter_management(litter_id):
    litter = Litter.query.get_or_404(litter_id)
    
    # Authorization check
    if litter.sow.user_id != current_user.id:
        abort(403)
    
    record = LitterManagement(
        litter_id=litter_id,
        date=parse_date(request.form.get('management_date')),
        management_type=request.form.get('management_type'),
        other_litter_id=request.form.get('other_litter_id'),
        piglets_moved=request.form.get('piglets_moved', type=int),
        notes=request.form.get('management_notes')
    )
    
    try:
        db.session.add(record)
        db.session.commit()
        flash('Management record added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding management record: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=litter.service_id))

# ==================== VACCINATION ROUTES ====================
@app.route('/litter/<int:litter_id>/vaccination', methods=['POST'])
@login_required
def add_vaccination(litter_id):
    litter = Litter.query.get_or_404(litter_id)
    
    # Authorization check
    if litter.sow.user_id != current_user.id:
        abort(403)
    
    vaccine_type = request.form.get('vaccine_type')
    if vaccine_type == 'other':
        vaccine_type = request.form.get('other_vaccine_name')
    
    record = VaccinationRecord(
        litter_id=litter_id,
        date=parse_date(request.form.get('vaccination_date')),
        vaccine_type=vaccine_type,
        piglets_vaccinated=request.form.get('piglets_vaccinated', type=int),
        dosage=request.form.get('dosage', type=float),
        next_due_date=parse_date(request.form.get('next_due_date')),
        administered_by=request.form.get('administered_by'),
        batch_number=request.form.get('batch_number'),
        notes=request.form.get('vaccination_notes')
    )
    
    try:
        db.session.add(record)
        db.session.commit()
        flash('Vaccination record added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding vaccination record: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=litter.service_id))

# ==================== WEIGHT RECORD ROUTES ====================
@app.route('/litter/<int:litter_id>/weight', methods=['POST'])
@login_required
def add_weight_record(litter_id):
    litter = Litter.query.get_or_404(litter_id)
    
    # Authorization check
    if litter.sow.user_id != current_user.id:
        abort(403)
    
    weight_type = request.form.get('weight_type')
    individual_weights = request.form.get('individual_weights', '')
    
    # Calculate average weight based on type
    if weight_type == 'individual' and individual_weights:
        try:
            weights = [float(w.strip()) for w in individual_weights.split(',') if w.strip()]
            average_weight = sum(weights) / len(weights) if weights else 0
            piglets_weighed = len(weights)
        except ValueError:
            flash('Please enter valid numeric weight values.', 'error')
            return redirect(url_for('litter_records', service_id=litter.service_id))
    else:
        average_weight = request.form.get('average_weight', type=float)
        piglets_weighed = request.form.get('piglets_weighed', type=int)
    
    record = WeightRecord(
        litter_id=litter_id,
        date=parse_date(request.form.get('weight_date')),
        weight_type=weight_type,
        piglets_weighed=piglets_weighed,
        average_weight=average_weight,
        individual_weights=individual_weights if weight_type == 'individual' else None,
        total_weight=request.form.get('total_weight', type=float),
        notes=request.form.get('weight_notes')
    )
    
    try:
        db.session.add(record)
        db.session.commit()
        flash('Weight record added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding weight record: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=litter.service_id))

# ==================== MORTALITY ROUTES ====================
@app.route('/litter/<int:litter_id>/mortality', methods=['POST'])
@login_required
def add_mortality(litter_id):
    litter = Litter.query.get_or_404(litter_id)
    
    # Authorization check
    if litter.sow.user_id != current_user.id:
        abort(403)
    
    cause = request.form.get('cause_of_death')
    if cause == 'other':
        cause = request.form.get('other_cause', 'other')
    
    number_died = request.form.get('number_died', type=int)
    
    # Validate: can't record more deaths than currently alive
    if number_died and number_died > litter.current_alive:
        flash(f'Cannot record {number_died} deaths. Only {litter.current_alive} piglets currently alive.', 'error')
        return redirect(url_for('litter_records', service_id=litter.service_id))
    
    record = MortalityRecord(
        litter_id=litter_id,
        date=parse_date(request.form.get('mortality_date')),
        number_died=number_died,
        cause=cause,
        age_at_death=request.form.get('age_at_death', type=int),
        weight_at_death=request.form.get('weight_at_death', type=float),
        notes=request.form.get('mortality_notes')
    )
    
    try:
        db.session.add(record)
        db.session.commit()
        flash('Mortality record added.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding mortality record: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=litter.service_id))

# ==================== SALE ROUTES ====================
@app.route('/litter/<int:litter_id>/sale', methods=['POST'])
@login_required
def add_sale(litter_id):
    litter = Litter.query.get_or_404(litter_id)
    
    # Authorization check
    if litter.sow.user_id != current_user.id:
        abort(403)
    
    number_sold = request.form.get('number_sold', type=int)
    
    # Validate: can't sell more than currently alive
    if number_sold and number_sold > litter.current_alive:
        flash(f'Cannot sell {number_sold} pigs. Only {litter.current_alive} currently available.', 'error')
        return redirect(url_for('litter_records', service_id=litter.service_id))
    
    record = SaleRecord(
        litter_id=litter_id,
        date=parse_date(request.form.get('sale_date')),
        number_sold=number_sold,
        average_weight=request.form.get('average_sale_weight', type=float),
        total_weight=request.form.get('total_weight_sold', type=float),
        price_per_kg=request.form.get('price_per_kg', type=float),
        total_amount=request.form.get('total_sale_amount', type=float),
        buyer_name=request.form.get('buyer_name'),
        buyer_contact=request.form.get('buyer_contact'),
        sale_type=request.form.get('sale_type'),
        notes=request.form.get('sale_notes')
    )
    
    try:
        db.session.add(record)
        db.session.commit()
        flash('Sale record added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding sale record: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=litter.service_id))

# ==================== DELETE ROUTES ====================
@app.route('/management/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_management_record(record_id):
    record = LitterManagement.query.get_or_404(record_id)
    
    # Authorization check
    if record.litter.sow.user_id != current_user.id:
        abort(403)
    
    service_id = record.litter.service_id
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Management record deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting record: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=service_id))

@app.route('/vaccination/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_vaccination(record_id):
    record = VaccinationRecord.query.get_or_404(record_id)
    
    # Authorization check
    if record.litter.sow.user_id != current_user.id:
        abort(403)
    
    service_id = record.litter.service_id
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Vaccination record deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting record: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=service_id))

@app.route('/weight/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_weight_record(record_id):
    record = WeightRecord.query.get_or_404(record_id)
    
    # Authorization check
    if record.litter.sow.user_id != current_user.id:
        abort(403)
    
    service_id = record.litter.service_id
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Weight record deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting record: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=service_id))

@app.route('/mortality/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_mortality(record_id):
    record = MortalityRecord.query.get_or_404(record_id)
    
    # Authorization check
    if record.litter.sow.user_id != current_user.id:
        abort(403)
    
    service_id = record.litter.service_id
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Mortality record deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting record: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=service_id))

@app.route('/sale/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_sale(record_id):
    record = SaleRecord.query.get_or_404(record_id)
    
    # Authorization check
    if record.litter.sow.user_id != current_user.id:
        abort(403)
    
    service_id = record.litter.service_id
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Sale record deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting record: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=service_id))

# ==================== LITTER DELETE ROUTE ====================
@app.route('/litter/<int:litter_id>/delete', methods=['POST'])
@login_required
def delete_litter(litter_id):
    litter = Litter.query.get_or_404(litter_id)
    
    # Authorization check
    if litter.sow.user_id != current_user.id:
        abort(403)
    
    service_id = litter.service_id
    
    try:
        db.session.delete(litter)
        db.session.commit()
        flash('Litter record deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting litter: {str(e)}', 'error')
    
    return redirect(url_for('litter_records', service_id=service_id)) 

@app.route('/delete-service-record/<int:record_id>', methods=['POST'])
@login_required
def delete_service_record(record_id):
    # Query the record by ID
    record = (
        db.session.query(ServiceRecords)
        .join(Sows, ServiceRecords.sow_id == Sows.id)
        .filter(ServiceRecords.id == record_id, Sows.user_id == current_user.id)
        .first_or_404()
    )

    if not record:
        abort(403) # Unauthorized access

    try:
        # Delete the record
        db.session.delete(record)
        db.session.commit()
        flash('Service record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the record: {str(e)}', 'error')
    
    # Redirect back to the sow's service records page
    return redirect(url_for('sow_service_records', sow_id=record.sow_id))

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    form = ExpenseForm()

    if form.validate_on_submit():
        expense = Expense(
            date=form.date.data,
            amount=form.amount.data,
            invoice_number=form.invoice_number.data,
            category=form.category.data,
            vendor=form.vendor.data,
            description=form.description.data,
            user_id = current_user.id
        )
        try:
            db.session.add(expense)
            db.session.commit()
            flash('Expense logged successfully!', 'success')
            return redirect(url_for('expenses'))
        except IntegrityError:
            db.session.rollback()
            flash('An expense with the same invoice is available','error')
    
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of Exepenses per page
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).paginate(page=page,per_page=per_page, error_out=False)
    expenses_list = expenses.items
    return render_template('expenses.html', form=form, expenses=expenses_list, pagination=expenses)

@app.route('/edit_expense/<int:expense_id>', methods=['GET','POST'])
@login_required
def edit_expense(expense_id):
    
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    form = ExpenseForm(obj=expense) #pre fill the data
    form.expense_id = expense.id

    if form.validate_on_submit():
        expense.date = form.date.data
        expense.amount = form.amount.data
        expense.invoice_number = form.invoice_number.data
        expense.category = form.category.data
        expense.vendor = form.vendor.data
        expense.description = form.description.data

        try:
            db.session.commit()
            flash('Expense Updated','success')
            return redirect(url_for('expenses'))
        except IntegrityError:
            db.session.rollback()
            flash(f'you already have an expense with that Reciept number', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
    return render_template('edit_expense.html', form=form, expense=expense)

@app.route('/expense_totals', methods=['GET'])
@login_required
def expense_totals():
    total_expenses = (
        db.session.query(db.func.sum(Expense.amount))
        .filter_by(user_id = current_user.id)
        .scalar()
    ) or 0
    return jsonify({'total_expenses': f"K{total_expenses:,.2f}"})

@app.route('/delete-expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    #Query the expense id
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()

    try:
        #Delete the record
        db.session.delete(expense)
        db.session.commit()
        flash('Expense record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the record: {str(e)}', 'error')

    #Redirect back to the expenses record page
    return redirect(url_for('expenses'))

@app.route('/settings',methods=['POST','GET'])
@login_required
def settings():
    return render_template('settings.html')

# change password route
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Verify current password
        if not bcrypt.check_password_hash(current_user.password, form.current_password.data):
            flash("Current password is incorrect.", "error")
            return redirect(url_for('change_password'))

        new_password = form.new_password.data.strip()

        # Ensure new password is not empty or same as current
        if not new_password:
            flash("New password cannot be empty.", "error")
            return redirect(url_for('change_password'))

        if bcrypt.check_password_hash(current_user.password, new_password):
            flash("New password cannot be the same as the current password.", "error")
            return redirect(url_for('change_password'))

        # Update password
        current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()

        flash("Password changed successfully!", "success")
        return redirect(url_for('settings'))
    if form.is_submitted() and not form.validate():
        flash("There seems to have been a problem, please try again", "error")
    return render_template('change_password.html', form=form)

@app.route("/delete_account", methods=["POST","GET"])
@login_required
def delete_account():
    is_google_user = current_user.password is None
    if request.method == "POST":
        if is_google_user:
            user_id = current_user.id
            logout_user()
            session.clear()
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                flash("Your account has been permanently deleted.", "info")
            else:
                flash("User not found.", "danger")
            return redirect(url_for("goodbye"))
        else:
            password = request.form.get("password")
            if not bcrypt.check_password_hash(current_user.password, password):
                flash("Incorrect password. Account not deleted.", "danger")
                return redirect(url_for("delete_account"))
            user_id = current_user.id
            logout_user()
            session.clear()
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                flash("Your account has been permanently deleted.", "info")
            else:
                flash("User not found.", "danger")
            return redirect(url_for("goodbye"))
    return render_template("delete_account.html", is_google_user=is_google_user)

@app.route("/goodbye")
def goodbye():
    return "<h3>We're sorry to see you go. Your account has been deleted.</h3>"

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate a password reset token
            token = secrets.token_urlsafe(32)
            user.password_reset_token = token
            user.password_reset_expiry = datetime.now(dt.timezone.utc) + timedelta(hours=1)  # Token valid for 1 hour
            db.session.commit()

            reset_url = url_for('reset_password', token=token, _external=True)

            # Send email with reset link
            msg = Message(
                subject     = "Password Reset Request - Pig Management System",
                sender      = ("Pig Management System", app.config['MAIL_USERNAME']),
                recipients  = [user.email]
            )
            msg.body = f"""
                Hi {user.username},

                You requested to reset your password.

                Click the link below to reset your password (expires in 1 hour):
                {reset_url}

                If you didn’t request this, ignore this email.

                Cheers,
                Pig Management System Team
                """
            msg.html = f"""
                <p>Hi {user.username},</p>
                <p>You requested to reset your password.</p>
                <p>Click the link below to reset your password (expires in 1 hour):</p>
                <p><a href="{reset_url}" style="color: #1a73e8;">Reset Password</a></p>
                <p>If you didn’t request this, ignore this email.</p>
                <p>Cheers,<br>Pig Management System Team</p>
                """
            try:
                mail.send(msg)
                flash("A password reset link has been sent to your email.", "success")
            except Exception as e:
                flash(f"We ran into a problem trying to send the email. Please try again later. Error: {str(e)}", "error")
        else:
            flash("No account found with that email address.", "error")
            return redirect(url_for('sign_in'))
    return render_template('forgot_password.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(password_reset_token=token).first()
    if not user or user.password_reset_expiry < datetime.now(dt.timezone.utc).replace(tzinfo=None):  # Now both are naive
        flash("Invalid or expired password reset link.", "error")
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        new_password = form.new_password.data.strip()
        confirm_password = form.confirm_password.data.strip()

        if not new_password:
            flash("The password can't be empty.", "error")
            return redirect(url_for('reset_password', token=token))
        
        if new_password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return redirect(url_for('reset_password', token=token))
        
        # Hash the new password and update the user record
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        user.password_reset_token = None  # Clear the token
        user.password_reset_expiry = None  # Clear the expiry time

        db.session.commit()

        flash("Your password has been reset successfully. You can now log in with your new password.", "success")
        return redirect(url_for('signin'))
    return render_template('reset_password.html', form=form, token=token)

# Run the Dashboard
if dash_app.layout is None:
    raise Exception("Dash layout must be set before running the server.")

# Run the app
if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)