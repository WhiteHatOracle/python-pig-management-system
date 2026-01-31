import logging
import os
import uuid
import logging
import datetime
import datetime as dt
from datetime import datetime, date, timedelta
from flask_login import current_user
from flask import has_request_context,current_app
from fpdf import FPDF
from PIL import Image
from werkzeug.utils import secure_filename
from sqlalchemy import func

from models import db, Litter, User, Boars, Sows, ServiceRecords, Invoice, Expense
from dashboard_helpers import (
    get_herd_counts_by_stage, 
    get_upcoming_farrowings
)


def parse_range(range_str):
    """Utility function to parse weight ranges for the invoice generator"""
    try:
        parts = range_str.strip().replace(' ', '').split('-')
        if len(parts) != 2:
            return None, None
        min_weight, max_weight = map(float, parts)
        return min_weight, max_weight
    except (ValueError, AttributeError):
        return None, None


def get_sow_service_records(user_id=None):
    """
    Get upcoming farrowing records for a specific user.
    """
    # Determine which user_id to use
    if user_id is None:
        if has_request_context() and current_user.is_authenticated:
            user_id = current_user.id
        else:
            logging.warning("get_sow_service_records: No user_id available")
            return []
    
    try:
        subquery = db.session.query(
            ServiceRecords.sow_id,
            db.func.max(ServiceRecords.service_date).label("latest_service")
        ).group_by(ServiceRecords.sow_id).subquery()

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
            Sows.user_id == user_id
        ).filter(
            ServiceRecords.due_date >= datetime.date.today()
        ).order_by(
            ServiceRecords.due_date
        )

        records = query.all()
        
        data = [
            {
                "sow_id": record[1],
                "service_date": record[0].service_date.strftime("%d-%b-%Y") if record[0].service_date else "", 
                "litter_guard1_date": record[0].litter_guard1_date.strftime("%d-%b-%Y") if record[0].litter_guard1_date else "",
                "litter_guard2_date": record[0].litter_guard2_date.strftime("%d-%b-%Y") if record[0].litter_guard2_date else "",
                "due_date": record[0].due_date.strftime("%d-%b-%Y") if record[0].due_date else "",
            }
            for record in records
        ]
        return data
        
    except Exception as e:
        logging.error(f"Error in get_sow_service_records: {e}")
        import traceback
        traceback.print_exc()
        return []


def update_dashboard(n_intervals, user_id=None):
    """Update dashboard with current herd data."""
    
    default_return = (0, 0, 0, 0, 0, 0, 0, [])
    
    try:
        if user_id is None:
            if has_request_context() and current_user.is_authenticated:
                user_id = current_user.id
            else:
                return default_return
        
        # Get herd counts
        herd_counts = get_herd_counts_by_stage(user_id)
        
        if herd_counts is None:
            herd_counts = {
                'total_herd': 0, 'sows': 0, 'boars': 0,
                'preweaning': 0, 'weaner': 0, 'grower': 0, 'finisher': 0,
            }
        
        # Get upcoming farrowings (including overdue)
        upcoming = get_upcoming_farrowings(user_id, days_ahead=120)
        
        if upcoming is None:
            upcoming = []
        
        # Format table data - INCLUDE days_until_due for conditional styling
        table_data = [
            {
                'status': row.get('status', ''),
                'sow_id': row.get('sow_id', ''),
                'service_date': row.get('service_date', ''),
                'litter_guard1_date': row.get('litter_guard1_date', ''),
                'litter_guard2_date': row.get('litter_guard2_date', ''),
                'due_date': row.get('due_date', ''),
                'days_until_due': row.get('days_until_due', 999),  # For conditional styling
            }
            for row in upcoming
        ]
        
        return (
            herd_counts.get('total_herd', 0),
            herd_counts.get('sows', 0),
            herd_counts.get('boars', 0),
            herd_counts.get('preweaning', 0),
            herd_counts.get('weaner', 0),
            herd_counts.get('grower', 0),
            herd_counts.get('finisher', 0),
            table_data
        )
        
    except Exception as e:
        logging.error(f"Dashboard update error: {e}")
        import traceback
        traceback.print_exc()
        return default_return


def get_total_counts(user_id=None):
    """Get total counts of all animals."""
    today = date.today()

    if user_id is None:
        if has_request_context() and current_user.is_authenticated:
            user_id = current_user.id
        else:
            return 0, 0, 0, 0, 0, 0, 0, 0

    try:
        total_sows = db.session.query(Sows.id).filter_by(user_id=user_id).count()
        total_boars = db.session.query(Boars.id).filter_by(user_id=user_id).count()

        pre_weaners = db.session.query(func.sum(Litter.bornAlive)) \
            .join(Sows, Sows.id == Litter.sow_id) \
            .filter(Sows.user_id == user_id) \
            .filter(Litter.farrowDate >= today - timedelta(days=20)) \
            .scalar() or 0

        weaners = db.session.query(func.sum(Litter.bornAlive)) \
            .join(Sows, Sows.id == Litter.sow_id) \
            .filter(Sows.user_id == user_id) \
            .filter(Litter.farrowDate >= today - timedelta(days=91)) \
            .filter(Litter.farrowDate < today - timedelta(days=20)) \
            .scalar() or 0

        growers = db.session.query(func.sum(Litter.bornAlive)) \
            .join(Sows, Sows.id == Litter.sow_id) \
            .filter(Sows.user_id == user_id) \
            .filter(Litter.farrowDate >= today - timedelta(days=112)) \
            .filter(Litter.farrowDate < today - timedelta(days=91)) \
            .scalar() or 0

        finishers = db.session.query(func.sum(Litter.bornAlive)) \
            .join(Sows, Sows.id == Litter.sow_id) \
            .filter(Sows.user_id == user_id) \
            .filter(Litter.farrowDate < today - timedelta(days=112)) \
            .scalar() or 0

        total_porkers = pre_weaners + weaners + growers + finishers
        total_pigs = total_sows + total_boars + total_porkers
    
        return total_pigs, total_sows, total_boars, total_porkers, pre_weaners, weaners, growers, finishers
    
    except Exception as e:
        logging.error(f"Error in get_total_counts: {e}")
        return 0, 0, 0, 0, 0, 0, 0, 0

def generate_invoice_pdf(
    user_data: dict,
    buyer_name: str,
    buyer_company: str = None,
    buyer_phone: str = None,
    buyer_address: str = None,
    invoice_number: str = None,
    invoice_data: list = None,
    total_weight: float = 0,
    average_weight: float = 0,
    total_cost: float = 0,
    total_pigs: int = 0,
    currency_symbol: str = "K",
    notes: str = None,
    logo_path: str = None,
    invoice_date: date = None
):
    """
    Generate a professional invoice PDF.
    """
    
    # Default invoice date to today if not provided
    if invoice_date is None:
        invoice_date = date.today()
    
    class InvoicePDF(FPDF):
        def __init__(self, user_data, logo_path=None):
            super().__init__()
            self.user_data = user_data
            self.logo_path = logo_path
            
            # Colors (RGB)
            self.primary_color = (16, 185, 129)
            self.primary_dark = (5, 150, 105)
            self.secondary_color = (31, 41, 55)
            self.light_gray = (243, 244, 246)
            self.medium_gray = (156, 163, 175)
            self.dark_text = (17, 24, 39)
            self.white = (255, 255, 255)
            self.warning_color = (234, 88, 12)
            
        def header(self):
            # Starting position
            start_x = 10
            start_y = 10
            logo_width = 0
            logo_height = 20  # Default logo height
            text_start_x = start_x
            
            # =========================================
            # LOGO - Left side, next to farm name
            # =========================================
            if self.logo_path and os.path.exists(self.logo_path):
                try:
                    # Get image dimensions to maintain aspect ratio
                    from PIL import Image as PILImage
                    with PILImage.open(self.logo_path) as img:
                        img_width, img_height = img.size
                        aspect_ratio = img_width / img_height
                    
                    # Set logo dimensions (max height 20mm, width proportional)
                    logo_height = 18
                    logo_width = logo_height * aspect_ratio
                    
                    # Cap maximum width
                    if logo_width > 35:
                        logo_width = 35
                        logo_height = logo_width / aspect_ratio
                    
                    # Place logo
                    self.image(self.logo_path, start_x, start_y, logo_width)
                    
                    # Text starts after logo with some padding
                    text_start_x = start_x + logo_width + 5
                    
                except Exception as e:
                    logging.warning(f"Could not load logo: {e}")
                    logo_width = 0
                    text_start_x = start_x
            
            # =========================================
            # COMPANY/FARM INFORMATION - Right of logo
            # =========================================
            
            # Farm Name
            self.set_xy(text_start_x, start_y)
            farm_name = self.user_data.get('farm_name') or self._get_full_name() or "My Business"
            self.set_font("Arial", "B", 14)
            self.set_text_color(*self.secondary_color)
            self.cell(80, 6, farm_name, ln=True)
            
            # Contact Details (email | phone)
            self.set_x(text_start_x)
            self.set_font("Arial", "", 9)
            self.set_text_color(*self.medium_gray)
            
            contact_parts = []
            if self.user_data.get('email'):
                contact_parts.append(self.user_data['email'])
            
            phone = self._get_phone()
            if phone:
                contact_parts.append(phone)
                
            if contact_parts:
                self.cell(80, 5, " | ".join(contact_parts), ln=True)
            
            # Address
            if self.user_data.get('address'):
                self.set_x(text_start_x)
                self.cell(80, 5, self.user_data['address'], ln=True)
            
            # =========================================
            # INVOICE TITLE - Right side
            # =========================================
            self.set_xy(140, start_y)
            self.set_font("Arial", "B", 28)
            self.set_text_color(*self.primary_color)
            self.cell(60, 15, "INVOICE", align="R", ln=True)
            
            # Add spacing after header
            # Ensure we're below both the logo and the text
            header_bottom = max(start_y + logo_height + 5, self.get_y() + 5)
            self.set_y(header_bottom + 10)
        
        def footer(self):
            self.set_y(-20)
            self.set_draw_color(*self.light_gray)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            
            self.ln(5)
            self.set_font("Arial", "I", 9)
            self.set_text_color(*self.primary_color)
            self.cell(0, 5, "Thank you for your business!", align="C", ln=True)
            
            self.set_font("Arial", "", 8)
            self.set_text_color(*self.medium_gray)
            self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="C")
        
        def _get_full_name(self):
            first = self.user_data.get('first_name', '')
            last = self.user_data.get('last_name', '')
            return f"{first} {last}".strip()
        
        def _get_phone(self):
            code = self.user_data.get('phone_country_code', '')
            number = self.user_data.get('phone_number', '')
            if code and number:
                return f"{code} {number}"
            return number or None

    # Create PDF instance
    pdf = InvoicePDF(user_data, logo_path)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)
    
    # Generate invoice number if not provided
    if not invoice_number:
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Format invoice date
    if hasattr(invoice_date, 'strftime'):
        formatted_date = invoice_date.strftime('%d %B %Y')
        formatted_date_short = invoice_date.strftime('%d/%m/%Y')
    else:
        formatted_date = str(invoice_date)
        formatted_date_short = str(invoice_date)
    
    # =========================================
    # INVOICE DETAILS SECTION
    # =========================================
    
    start_y = pdf.get_y()
    
    # Left side - Bill To
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(95, 6, "BILL TO:", ln=True)
    
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(*pdf.dark_text)
    pdf.cell(95, 6, buyer_name or "Customer", ln=True)
    
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.medium_gray)
    
    if buyer_company and buyer_company != buyer_name:
        pdf.cell(95, 5, buyer_company, ln=True)
    if buyer_phone:
        pdf.cell(95, 5, buyer_phone, ln=True)
    if buyer_address:
        for line in buyer_address.split('\n'):
            if line.strip():
                pdf.cell(95, 5, line.strip(), ln=True)
    
    left_end_y = pdf.get_y()
    
    # Right side - Invoice Details Box
    pdf.set_fill_color(*pdf.light_gray)
    box_x = 115
    box_width = 85
    box_height = 45
    pdf.rect(box_x - 5, start_y - 2, box_width, box_height, 'F')
    
    pdf.set_xy(box_x, start_y)
    
    # Invoice Number
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.medium_gray)
    pdf.cell(30, 6, "Invoice #:", align="L")
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*pdf.dark_text)
    pdf.cell(45, 6, invoice_number, align="L", ln=True)
    
    pdf.set_x(box_x)
    
    # Invoice Date
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.medium_gray)
    pdf.cell(30, 6, "Date:", align="L")
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.dark_text)
    pdf.cell(45, 6, formatted_date, align="L", ln=True)
    
    pdf.set_x(box_x)
    
    # Due Date
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.medium_gray)
    pdf.cell(30, 6, "Due Date:", align="L")
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.dark_text)
    pdf.cell(45, 6, formatted_date, align="L", ln=True)
    
    pdf.set_x(box_x)
    
    # Total Items/Pigs
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.medium_gray)
    pdf.cell(30, 6, "Total Items:", align="L")
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*pdf.dark_text)
    pdf.cell(45, 6, str(total_pigs), align="L", ln=True)
    
    pdf.set_x(box_x)
    
    # Status
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.medium_gray)
    pdf.cell(30, 6, "Status:", align="L")
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*pdf.warning_color)
    pdf.cell(45, 6, "UNPAID", align="L", ln=True)
    
    # Move to after both columns
    pdf.set_y(max(left_end_y, start_y + box_height + 5) + 5)
    
    # =========================================
    # ITEMS TABLE
    # =========================================
    
    pdf.set_fill_color(*pdf.primary_color)
    pdf.set_text_color(*pdf.white)
    pdf.set_font("Arial", "B", 9)
    
    col_widths = [12, 54, 54, 54]
    headers = ["#", "Weight (kg)", f"Price per Kg ({currency_symbol})", f"Cost ({currency_symbol})"]
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, border=0, align="C", fill=True)
    pdf.ln()
    
    # Table Rows
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.dark_text)
    
    row_fill = False
    for idx, item in enumerate(invoice_data or [], start=1):
        if row_fill:
            pdf.set_fill_color(*pdf.light_gray)
        else:
            pdf.set_fill_color(*pdf.white)
        
        pdf.cell(col_widths[0], 8, str(idx), border=0, align="C", fill=True)
        pdf.cell(col_widths[1], 8, item.get("formatted_weight", ""), border=0, align="C", fill=True)
        pdf.cell(col_widths[2], 8, item.get("formatted_price", ""), border=0, align="C", fill=True)
        pdf.cell(col_widths[3], 8, item.get("formatted_cost", ""), border=0, align="C", fill=True)
        pdf.ln()
        
        row_fill = not row_fill
    
    # Table bottom border
    pdf.set_draw_color(*pdf.medium_gray)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 184, pdf.get_y())
    
    pdf.ln(8)
    
    # =========================================
    # TOTALS SECTION
    # =========================================
    
    totals_x = 110
    
    pdf.set_fill_color(*pdf.light_gray)
    summary_start_y = pdf.get_y()
    pdf.rect(totals_x - 5, summary_start_y, 84, 48, 'F')
    
    # Total Weight
    pdf.set_xy(totals_x, summary_start_y + 3)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.medium_gray)
    pdf.cell(40, 6, "Total Weight:", align="R")
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*pdf.dark_text)
    pdf.cell(35, 6, f"{total_weight:,.2f} kg", align="R", ln=True)
    
    # Average Weight
    pdf.set_x(totals_x)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.medium_gray)
    pdf.cell(40, 6, "Average Weight:", align="R")
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*pdf.dark_text)
    pdf.cell(35, 6, f"{average_weight:,.2f} kg", align="R", ln=True)
    
    # Number of Pigs
    pdf.set_x(totals_x)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*pdf.medium_gray)
    pdf.cell(40, 6, "Number of Pigs:", align="R")
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*pdf.dark_text)
    pdf.cell(35, 6, str(total_pigs), align="R", ln=True)
    
    # Separator line
    pdf.set_draw_color(*pdf.medium_gray)
    pdf.line(totals_x, pdf.get_y() + 2, 184, pdf.get_y() + 2)
    pdf.ln(5)
    
    # Total Cost
    pdf.set_x(totals_x)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*pdf.secondary_color)
    pdf.cell(40, 8, "TOTAL DUE:", align="R")
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(35, 8, f"{currency_symbol}{total_cost:,.2f}", align="R", ln=True)
    
    pdf.ln(10)
    
    # =========================================
    # NOTES SECTION
    # =========================================
    
    if notes:
        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(*pdf.secondary_color)
        pdf.cell(0, 6, "Notes:", ln=True)
        
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(*pdf.medium_gray)
        pdf.multi_cell(0, 5, notes)
        pdf.ln(8)
    
    # =========================================
    # PAYMENT INFORMATION
    # =========================================
    
    has_payment_info = any([
        user_data.get('bank_name'),
        user_data.get('mobile_money'),
        user_data.get('account_number')
    ])
    
    if has_payment_info:
        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(*pdf.secondary_color)
        pdf.cell(0, 6, "Payment Information:", ln=True)
        
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(*pdf.dark_text)
        
        if user_data.get('bank_name'):
            pdf.cell(0, 5, f"Bank: {user_data['bank_name']}", ln=True)
        if user_data.get('account_name'):
            pdf.cell(0, 5, f"Account Name: {user_data['account_name']}", ln=True)
        if user_data.get('account_number'):
            pdf.cell(0, 5, f"Account Number: {user_data['account_number']}", ln=True)
        if user_data.get('mobile_money'):
            phone = f"{user_data.get('phone_country_code', '')} {user_data.get('phone_number', '')}".strip()
            pdf.cell(0, 5, f"Mobile Money: {phone or user_data['mobile_money']}", ln=True)
        
        pdf.ln(8)
    
    # =========================================
    # SIGNATURE SECTION
    # =========================================
    
    if pdf.get_y() > 240:
        pdf.add_page()
    
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*pdf.secondary_color)
    pdf.cell(95, 6, "Received by (Buyer):", ln=False)
    pdf.cell(95, 6, "Supplied by (Seller):", ln=True)
    
    pdf.ln(15)
    
    # Signature lines
    pdf.set_draw_color(*pdf.medium_gray)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 95, pdf.get_y())
    pdf.line(105, pdf.get_y(), 190, pdf.get_y())
    
    pdf.ln(2)
    
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(*pdf.medium_gray)
    
    buyer_display = buyer_name if buyer_name else "____________________"
    pdf.cell(95, 5, f"Name: {buyer_display}", ln=False)
    
    supplier_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
    supplier_display = supplier_name if supplier_name else "____________________"
    pdf.cell(95, 5, f"Name: {supplier_display}", ln=True)
    
    pdf.ln(8)
    
    pdf.cell(95, 5, "Date: ____________________", ln=False)
    pdf.cell(95, 5, f"Date: {formatted_date_short}", ln=True)

    return pdf.output(dest='S').encode('latin1')


def generate_invoice_number(prefix: str = "INV") -> str:
    """Generate a unique invoice number."""
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}-{timestamp}"

def get_litter_stage(farrow_date):
    """Determine the growth stage of a litter based on farrow date."""
    if farrow_date is None:
        return 'unknown'
        
    age_days = (date.today() - farrow_date).days
    
    if age_days < 21:
        return 'pre-weaning'
    elif age_days < 85:
        return 'weaner'
    elif age_days < 113:
        return 'grower'
    else:
        return 'finisher'




def allowed_file(filename):
    """Check if file extension is allowed"""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    allowed = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return ext in allowed


def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent overwrites"""
    ext = original_filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    return secure_filename(unique_name)


def save_and_resize_image(file, folder, size, filename=None):
    """
    Save an image file, resize it, and return the filename
    
    Args:
        file: FileStorage object from request.files
        folder: Directory to save the file
        size: Tuple (width, height) for resizing
        filename: Optional filename (generates unique if not provided)
    
    Returns:
        str: The saved filename, or None if failed
    """
    if not file or not allowed_file(file.filename):
        return None
    
    try:
        # Generate filename
        if not filename:
            filename = generate_unique_filename(file.filename)
        
        filepath = os.path.join(folder, filename)
        
        # Open and process image
        image = Image.open(file)
        
        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Calculate aspect ratio preserving resize
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # For profile pictures, make it square with center crop
        if size[0] == size[1]:  # Square image (profile picture)
            image = crop_to_square(image)
            image = image.resize(size, Image.Resampling.LANCZOS)
        
        # Save optimized image
        image.save(filepath, 'JPEG', quality=85, optimize=True)
        
        return filename
        
    except Exception as e:
        print(f"Error saving image: {e}")
        return None


def crop_to_square(image):
    """Crop image to square from center"""
    width, height = image.size
    
    if width == height:
        return image
    
    # Determine crop box
    if width > height:
        # Landscape - crop sides
        left = (width - height) // 2
        right = left + height
        box = (left, 0, right, height)
    else:
        # Portrait - crop top/bottom
        top = (height - width) // 2
        bottom = top + width
        box = (0, top, width, bottom)
    
    return image.crop(box)


def delete_image(filename, folder):
    """Delete an image file"""
    if filename and folder:
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logging.info(f"Deleted: {filepath}")
                return True
            except Exception as e:
                logging.error(f"Error deleting image: {e}")
    return False

def save_profile_picture(file, user):
    """
    Save profile picture for a user.
    Always saves as JPEG with .jpg extension for compatibility.
    Creates a square cropped image.
    """
    if not file or not file.filename:
        logging.warning("No file provided for profile picture")
        return None
    
    if not allowed_file(file.filename):
        logging.warning(f"File type not allowed: {file.filename}")
        return None
    
    try:
        profile_folder = current_app.config.get('PROFILE_PICTURES_FOLDER')
        profile_size = current_app.config.get('PROFILE_PICTURE_SIZE', (300, 300))
        
        logging.info(f"PROFILE_PICTURES_FOLDER: {profile_folder}")
        
        if not profile_folder:
            logging.error("PROFILE_PICTURES_FOLDER not configured")
            return None
        
        # Create folder if it doesn't exist
        os.makedirs(profile_folder, exist_ok=True)
        
        # Delete old profile picture if exists
        if user.profile_picture:
            old_picture_path = os.path.join(profile_folder, user.profile_picture)
            if os.path.exists(old_picture_path):
                try:
                    os.remove(old_picture_path)
                    logging.info(f"Deleted old profile picture: {old_picture_path}")
                except Exception as e:
                    logging.warning(f"Could not delete old profile picture: {e}")
        
        # Generate unique filename - ALWAYS use .jpg extension
        unique_id = uuid.uuid4().hex
        filename = secure_filename(f"{unique_id}.jpg")
        filepath = os.path.join(profile_folder, filename)
        
        logging.info(f"Saving profile picture to: {filepath}")
        
        # Open and process image
        image = Image.open(file)
        
        # Convert to RGB (required for JPEG)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            if image.mode in ('RGBA', 'LA'):
                background.paste(image, mask=image.split()[-1])
            else:
                background.paste(image)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Crop to square from center
        image = crop_to_square(image)
        
        # Resize to target size
        image = image.resize(profile_size, Image.Resampling.LANCZOS)
        
        # Save as JPEG
        image.save(filepath, 'JPEG', quality=90, optimize=True)
        
        logging.info(f"Profile picture saved successfully: {filepath}")
        return filename
        
    except Exception as e:
        logging.error(f"Error saving profile picture: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_farm_logo(file, user):
    """
    Save farm logo for a user.
    Preserves PNG format for transparency, converts others to JPEG.
    """
    if not file or not file.filename:
        logging.warning("No file provided")
        return None
    
    if not allowed_file(file.filename):
        logging.warning(f"File type not allowed: {file.filename}")
        return None
    
    try:
        logos_folder = current_app.config.get('LOGOS_FOLDER')
        logo_size = current_app.config.get('LOGO_SIZE', (400, 200))
        
        if not logos_folder:
            logging.error("LOGOS_FOLDER not configured")
            return None
        
        # Create folder if it doesn't exist
        os.makedirs(logos_folder, exist_ok=True)
        
        # Delete old logo if exists
        if user.farm_logo:
            old_logo_path = os.path.join(logos_folder, user.farm_logo)
            if os.path.exists(old_logo_path):
                try:
                    os.remove(old_logo_path)
                    logging.info(f"Deleted old logo: {old_logo_path}")
                except Exception as e:
                    logging.warning(f"Could not delete old logo: {e}")
        
        # Open image to determine format
        image = Image.open(file)
        original_format = image.format  # 'PNG', 'JPEG', 'GIF', etc.
        
        logging.info(f"Original image format: {original_format}, mode: {image.mode}")
        
        # Determine output format and extension
        # Keep PNG if original is PNG (for transparency), otherwise use JPEG
        if original_format == 'PNG':
            output_format = 'PNG'
            extension = 'png'
        else:
            output_format = 'JPEG'
            extension = 'jpg'
        
        # Generate unique filename with correct extension
        unique_id = uuid.uuid4().hex
        filename = secure_filename(f"{unique_id}.{extension}")
        filepath = os.path.join(logos_folder, filename)
        
        logging.info(f"Saving logo as {output_format} to: {filepath}")
        
        # Process image based on output format
        if output_format == 'JPEG':
            # Convert to RGB for JPEG (no transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                if image.mode in ('RGBA', 'LA'):
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
        else:
            # For PNG, convert to RGBA if needed to preserve transparency
            if image.mode == 'P':
                image = image.convert('RGBA')
            elif image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGBA')
        
        # Resize while maintaining aspect ratio
        image.thumbnail(logo_size, Image.Resampling.LANCZOS)
        
        # Save with appropriate settings
        if output_format == 'JPEG':
            image.save(filepath, 'JPEG', quality=90, optimize=True)
        else:
            image.save(filepath, 'PNG', optimize=True)
        
        logging.info(f"Logo saved successfully: {filepath}")
        return filename
        
    except Exception as e:
        logging.error(f"Error saving farm logo: {e}")
        import traceback
        traceback.print_exc()
        return None