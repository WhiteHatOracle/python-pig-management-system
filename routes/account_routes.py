import os
import uuid
import re
from models import db, User
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from utils import save_farm_logo, delete_image, allowed_file

account_bp = Blueprint('account', __name__, url_prefix='/account')


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file, folder, size=None):
    """Save an uploaded image file"""
    if not file or not allowed_file(file.filename):
        return None
    
    try:
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Ensure folder exists
        upload_folder = os.path.join(current_app.root_path, 'uploads', folder)
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        filepath = os.path.join(upload_folder, filename)
        
        # Try to resize with PIL if available
        try:
            from PIL import Image
            image = Image.open(file)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            if size:
                image.thumbnail(size, Image.Resampling.LANCZOS)
            
            image.save(filepath, 'JPEG', quality=85, optimize=True)
        except ImportError:
            # PIL not installed, save directly
            file.save(filepath)
        
        return filename
        
    except Exception as e:
        print(f"Error saving image: {e}")
        return None


def delete_image(filename, folder):
    """Delete an image file"""
    if filename:
        filepath = os.path.join(current_app.root_path, 'uploads', folder, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"Error deleting image: {e}")
    return False


def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# ==========================================
# PROFILE VIEW
# ==========================================

@account_bp.route('/profile')
@login_required
def profile():
    """View user profile"""
    return render_template('account/profile.html', user=current_user)


# ==========================================
# EDIT PERSONAL INFO
# ==========================================

# routes/account.py

@account_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone_country_code = request.form.get('phone_country_code', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        phone_country_iso = request.form.get('phone_country_iso', '').strip()
        full_phone_number = request.form.get('full_phone_number', '').strip()
        
        # Validation
        if not email:
            flash('Email is required.', 'error')
            return redirect(url_for('account.edit_profile'))
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(
            User.email == email, 
            User.id != current_user.id
        ).first()
        
        if existing_user:
            flash('This email is already registered to another account.', 'error')
            return redirect(url_for('account.edit_profile'))
        
        # Update user
        current_user.first_name = first_name or None
        current_user.last_name = last_name or None
        current_user.email = email
        current_user.phone_country_code = phone_country_code or None
        current_user.phone_number = phone_number or None
        current_user.phone_country_iso = phone_country_iso or None
        
        # Optionally store the full E.164 formatted number
        # current_user.full_phone_number = full_phone_number or None
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('account.profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('account.edit_profile'))
    
    return render_template('account/edit_profile.html', user=current_user)


# ==========================================
# EDIT FARM INFO
# ==========================================

@account_bp.route('/farm', methods=['GET', 'POST'])
@login_required
def edit_farm():
    """Edit farm/business information"""
    if request.method == 'POST':
        try:
            current_user.farm_name = request.form.get('farm_name', '').strip()
            current_user.farm_address = request.form.get('farm_address', '').strip()
            current_user.farm_city = request.form.get('farm_city', '').strip()
            current_user.farm_state = request.form.get('farm_state', '').strip()
            current_user.farm_country = request.form.get('farm_country', '').strip()
            current_user.farm_postal_code = request.form.get('farm_postal_code', '').strip()
            current_user.tax_id = request.form.get('tax_id', '').strip()
            
            db.session.commit()
            flash('Farm information updated successfully!', 'success')
            return redirect(url_for('account.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating farm information: {str(e)}', 'error')
    
    return render_template('account/edit_farm.html', user=current_user)


# ==========================================
# UPLOAD PROFILE PICTURE
# ==========================================

@account_bp.route('/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    """Handle profile picture upload"""
    
    print("=" * 50)
    print("FILES:", request.files)
    print("PROFILE_PICTURES_FOLDER:", current_app.config.get('PROFILE_PICTURES_FOLDER'))
    print("=" * 50)
    
    if 'profile_picture' not in request.files:
        flash('No file part in request', 'error')
        return redirect(url_for('account.profile'))
    
    file = request.files['profile_picture']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('account.profile'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP.', 'error')
        return redirect(url_for('account.profile'))
    
    # Check file size
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024)
    if file_size > max_size:
        flash(f'File too large. Maximum size is {max_size // (1024*1024)}MB.', 'error')
        return redirect(url_for('account.profile'))
    
    try:
        from utils import save_profile_picture
        filename = save_profile_picture(file, current_user)
        
        if filename:
            current_user.profile_picture = filename
            db.session.commit()
            flash('Profile picture updated successfully!', 'success')
        else:
            flash('Error processing image. Please try again.', 'error')
            
    except Exception as e:
        db.session.rollback()
        print(f"Profile picture upload error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error uploading profile picture: {str(e)}', 'error')
    
    return redirect(url_for('account.profile'))

# ==========================================
# UPLOAD FARM LOGO
# ==========================================

@account_bp.route('/upload-farm-logo', methods=['POST'])
@login_required
def upload_farm_logo():
    """Handle farm logo upload"""
    
    # Debug output
    print("=" * 50)
    print("FILES:", request.files)
    print("LOGOS_FOLDER:", current_app.config.get('LOGOS_FOLDER'))
    print("=" * 50)
    
    # Check if file was sent
    if 'logo' not in request.files:
        flash('No file part in request', 'error')
        return redirect(url_for('account.profile'))
    
    file = request.files['logo']
    
    # Check if a file was actually selected
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('account.profile'))
    
    # Check file extension
    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP.', 'error')
        return redirect(url_for('account.profile'))
    
    # Check file size
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024)
    if file_size > max_size:
        flash(f'File too large. Maximum size is {max_size // (1024*1024)}MB.', 'error')
        return redirect(url_for('account.profile'))
    
    try:
        filename = save_farm_logo(file, current_user)
        
        if filename:
            current_user.farm_logo = filename
            db.session.commit()
            flash('Logo uploaded successfully!', 'success')
        else:
            flash('Error processing image. Please try again.', 'error')
            
    except Exception as e:
        db.session.rollback()
        print(f"Logo upload error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error uploading logo: {str(e)}', 'error')
    
    return redirect(url_for('account.profile'))


# ==========================================
# DELETE PROFILE PICTURE
# ==========================================

@account_bp.route('/delete-profile-picture', methods=['POST'])
@login_required
def delete_profile_picture():
    """Delete profile picture"""
    if current_user.profile_picture:
        try:
            from utils import delete_image
            profile_folder = current_app.config.get('PROFILE_PICTURES_FOLDER')
            if profile_folder:
                delete_image(current_user.profile_picture, profile_folder)
            
            current_user.profile_picture = None
            db.session.commit()
            flash('Profile picture removed successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error removing profile picture: {str(e)}', 'error')
    else:
        flash('No profile picture to remove', 'info')
    
    return redirect(url_for('account.profile'))


# ==========================================
# DELETE FARM LOGO
# ==========================================

@account_bp.route('/delete-farm-logo', methods=['POST'])
@login_required
def delete_farm_logo():
    """Delete farm logo"""
    if current_user.farm_logo:
        try:
            logos_folder = current_app.config.get('LOGOS_FOLDER')
            if logos_folder:
                delete_image(current_user.farm_logo, logos_folder)
            
            current_user.farm_logo = None
            db.session.commit()
            flash('Logo removed successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error removing logo: {str(e)}', 'error')
    else:
        flash('No logo to remove', 'info')
    
    return redirect(url_for('account.profile'))


# ==========================================
# API ENDPOINTS
# ==========================================

@account_bp.route('/api/profile', methods=['GET'])
@login_required
def api_get_profile():
    """Get user profile as JSON"""
    return jsonify(current_user.to_dict())


@account_bp.route('/api/profile', methods=['PUT'])
@login_required
def api_update_profile():
    """Update user profile via API"""
    data = request.get_json()
    
    try:
        if 'first_name' in data:
            current_user.first_name = data['first_name']
        if 'last_name' in data:
            current_user.last_name = data['last_name']
        if 'phone_number' in data:
            current_user.phone_number = re.sub(r'\D', '', data['phone_number']) if data['phone_number'] else None
        if 'phone_country_code' in data:
            current_user.phone_country_code = data['phone_country_code']
        if 'farm_name' in data:
            current_user.farm_name = data['farm_name']
        if 'farm_address' in data:
            current_user.farm_address = data['farm_address']
        if 'farm_city' in data:
            current_user.farm_city = data['farm_city']
        if 'farm_state' in data:
            current_user.farm_state = data['farm_state']
        if 'farm_country' in data:
            current_user.farm_country = data['farm_country']
        if 'farm_postal_code' in data:
            current_user.farm_postal_code = data['farm_postal_code']
        
        db.session.commit()
        return jsonify({'success': True, 'user': current_user.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400