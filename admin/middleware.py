from flask import request, g
from datetime import datetime, timezone
import time
import re
from user_agents import parse as parse_user_agent

def track_page_view(app, db, PageView):
    """Middleware to track page views"""
    
    # Paths to exclude from tracking
    EXCLUDED_PATHS = [
        r'^/static/',
        r'^/admin/api/',
        r'^/_dash',
        r'^/favicon.ico',
        r'\.js$',
        r'\.css$',
        r'\.png$',
        r'\.jpg$',
        r'\.ico$',
        r'\.woff',
        r'\.ttf$',
    ]
    
    def should_track(path):
        for pattern in EXCLUDED_PATHS:
            if re.search(pattern, path):
                return False
        return True
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        # Skip if path should not be tracked
        if not should_track(request.path):
            return response
        
        try:
            # Calculate response time
            response_time = None
            if hasattr(g, 'start_time'):
                response_time = (time.time() - g.start_time) * 1000  # Convert to ms
            
            # Parse user agent
            user_agent_string = request.headers.get('User-Agent', '')
            device_type = None
            browser = None
            
            try:
                ua = parse_user_agent(user_agent_string)
                if ua.is_mobile:
                    device_type = 'mobile'
                elif ua.is_tablet:
                    device_type = 'tablet'
                else:
                    device_type = 'desktop'
                browser = ua.browser.family
            except:
                pass
            
            # Get user ID if logged in
            user_id = None
            try:
                from flask_login import current_user
                if current_user.is_authenticated and hasattr(current_user, 'id'):
                    # Make sure it's a regular user, not admin
                    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
                        user_id = current_user.id
            except:
                pass
            
            # Create page view record
            page_view = PageView(
                path=request.path,
                method=request.method,
                user_id=user_id,
                ip_address=request.remote_addr,
                user_agent=user_agent_string[:500] if user_agent_string else None,
                referrer=request.referrer[:500] if request.referrer else None,
                device_type=device_type,
                browser=browser,
                response_time=response_time,
                status_code=response.status_code,
                timestamp=datetime.now(timezone.utc)
            )
            
            db.session.add(page_view)
            db.session.commit()
            
        except Exception as e:
            # Don't let tracking errors break the app
            db.session.rollback()
            app.logger.error(f"Error tracking page view: {e}")
        
        return response