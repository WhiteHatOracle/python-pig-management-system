from models import db, Litter, User, Boars, Sows, ServiceRecords, Invoice, Expense
from forms import LitterForm, SowForm, BoarForm, RegisterForm, LoginForm, FeedCalculatorForm, InvoiceGeneratorForm, ServiceRecordForm, ExpenseForm, CompleteFeedForm
from flask_login import current_user
from datetime import date, timedelta
import datetime
from sqlalchemy import func, event
from fpdf import FPDF
import logging

# Utility function to parse weight ranges/ this is for the invoice generator
def parse_range(range_str):
    try:
        parts = range_str.strip().replace(' ', '').split('-')
        if len(parts) != 2:
            return None, None
        min_weight, max_weight = map(float, parts)
        return min_weight, max_weight
    except (ValueError, AttributeError):
        return None, None

# Function to Fetch Sow Service Records for Table
def get_sow_service_records():
    # Get latest service record for each sow
    subquery = db.session.query(
        ServiceRecords.sow_id,
        db.func.max(ServiceRecords.service_date).label("latest_service")
    ).group_by(ServiceRecords.sow_id).subquery()

    # Query service_records and join with sows to get the actual sowID
    query = db.session.query(
        ServiceRecords, 
        Sows.sowID
    ).join(
        subquery,
        (ServiceRecords.sow_id == subquery.c.sow_id) & 
        (ServiceRecords.service_date == subquery.c.latest_service)
    ).join(
        Sows, 
        ServiceRecords.sow_id == Sows.id
    ).filter(
        Sows.user_id == current_user.id
    ).filter(
        ServiceRecords.due_date >= datetime.date.today()
    ).order_by(
        ServiceRecords.due_date
    )


    # Optionally filter records based on due_date
    records = query.all()
    # Convert query results into a list of dictionaries for Dash DataTable
    data = [
        {
            "sow_id":               record[1],  # Sow's actual sowID from the sows table
            "service_date":         record[0].service_date.strftime("%d-%b-%Y") if record[0].service_date else "", 
            "litter_guard1_date":   record[0].litter_guard1_date.strftime("%d-%b-%Y") if record[0].litter_guard1_date else "",
            "litter_guard2_date":   record[0].litter_guard2_date.strftime("%d-%b-%Y") if record[0].litter_guard2_date else "",
            "due_date":             record[0].due_date.strftime("%d-%b-%Y") if record[0].due_date else "",
        }
        for record in records
    ]    
    return data

def update_dashboard(n):
    try:
        total_pigs, total_sows, total_boars, total_porkers, pre_weaners, weaners, growers, finishers = get_total_counts()
        service_records = get_sow_service_records()
        return (
            str(total_pigs),
            str(total_sows),
            str(total_boars),
            str(pre_weaners),
            str(weaners),
            str(growers),
            str(finishers),
            service_records
        )
    
    except Exception as e:
        print("Error updating dashboard:", e)
        return "Error", "Error", "Error", "Error", "Error", "Error", "Error", []

def get_total_counts():
    today=date.today()

    try:
        # Count total sows and boars
        total_sows = db.session.query(Sows.id).filter_by(user_id=current_user.id).count()
        total_boars = db.session.query(Boars.id).filter_by(user_id=current_user.id).count()

        # Calculate pigs by age group with user filtering
        pre_weaners = db.session.query(func.sum(Litter.bornAlive)) \
            .join(Sows, Sows.id == Litter.sow_id) \
            .filter(Sows.user_id == current_user.id) \
            .filter(Litter.farrowDate >= today - timedelta(days=20)) \
            .scalar() or 0

        weaners = db.session.query(func.sum(Litter.bornAlive)) \
            .join(Sows, Sows.id == Litter.sow_id) \
            .filter(Sows.user_id == current_user.id) \
            .filter(Litter.farrowDate >= today - timedelta(days=91)) \
            .filter(Litter.farrowDate < today - timedelta(days=20)) \
            .scalar() or 0

        growers = db.session.query(func.sum(Litter.bornAlive)) \
            .join(Sows, Sows.id == Litter.sow_id) \
            .filter(Sows.user_id == current_user.id) \
            .filter(Litter.farrowDate >= today - timedelta(days=112)) \
            .filter(Litter.farrowDate < today - timedelta(days=91)) \
            .scalar() or 0

        finishers = db.session.query(func.sum(Litter.bornAlive)) \
            .join(Sows, Sows.id == Litter.sow_id) \
            .filter(Sows.user_id == current_user.id) \
            .filter(Litter.farrowDate < today - timedelta(days=112)) \
            .scalar() or 0

        # Sum all piglets from age groups
        total_porkers = pre_weaners + weaners + growers + finishers
        total_pigs = total_sows + total_boars + total_porkers
    
        return total_pigs, total_sows, total_boars, total_porkers, pre_weaners, weaners, growers, finishers
    except Exception as e:
        logging.error(f"Error in get_total_counts: {e}")
        return 0, 0, 0, 0, 0, 0, 0 # Return zeroes if there is an error
    
def generate_invoice_pdf(company_name, invoice_number, invoice_data, total_weight, average_weight, total_cost):
    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 20)
            self.cell(0, 10, "Invoice", align="C", ln=True)
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title and Header Section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Invoice Number: {invoice_number}", ln=True)
    pdf.cell(0, 10, f"Company Name: {company_name}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%d-%b-%Y')}", ln=True)
    pdf.ln(10)

    # Table Header
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(10, 10, "#", border=1, align="C", fill=True)
    pdf.cell(60, 10, "Weight (kg)", border=1, align="C", fill=True)
    pdf.cell(60, 10, "Price per Kg (K)", border=1, align="C", fill=True)
    pdf.cell(60, 10, "Cost (K)", border=1, align="C", fill=True)
    pdf.ln()

    # Table Data
    pdf.set_font("Arial", size=10)
    for idx, item in enumerate(invoice_data, start=1):
        pdf.cell(10, 10, str(idx), border=1, align="C")
        pdf.cell(60, 10, item["formatted_weight"], border=1, align="C")
        pdf.cell(60, 10, item["formatted_price"], border=1, align="C")
        pdf.cell(60, 10, item["formatted_cost"], border=1, align="C")
        pdf.ln()

    # Total weight
    pdf.set_font("Arial","B", 12)
    pdf.ln(5)
    pdf.cell(130,10,"Total Weight:", border=0,align="R")
    pdf.cell(60, 10, f"{total_weight:,.2f}Kg", border=1, align="C")
    pdf.ln(8)

    #Average weight
    pdf.set_font("Arial","B",12)
    pdf.ln(5)
    pdf.cell(130, 10,"Average Weight:", border=0, align="R")
    pdf.cell(60,10,f"{average_weight:,.2f}Kg",border=1,align="C")
    pdf.ln(5)

    # Total Cost
    pdf.set_font("Arial", "B", 12)
    pdf.ln(8)
    pdf.cell(130, 10, "Total Cost:", border=0, align="R")
    pdf.cell(60, 10, f"K{total_cost:,.2f}", border=1, align="C")
    pdf.ln(20)


    # Signatures Section
    pdf.set_font("Arial", "B", 10)
    pdf.cell(90, 10, "Received by: ____________________________", border=0, ln=0)
    pdf.cell(90, 10, "Supplied by: ____________________________", border=0, ln=1)
    pdf.ln(10)
    pdf.cell(90, 10, "Signature: ____________________________", border=0, ln=0)
    pdf.cell(90, 10, "Signature: ____________________________", border=0, ln=1)

    # Footer Section
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, "Thank you for your business!", align="C", ln=True)

    return pdf.output(dest='S').encode('latin1')

def get_litter_stage(farrow_date):
    age_days = (date.today() - farrow_date).days
    if age_days < 21:
        return 'pre-weaning'
    elif age_days < 85:
        return 'weaner'
    elif age_days < 113:
        return 'grower'
    else:
        return 'finisher'
    
