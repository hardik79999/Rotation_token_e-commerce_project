from flask import current_app, render_template_string
from shop.extensions import db
from shop.models import User
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

def verify_email_action(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-confirm', max_age=600) 
        user = User.query.filter_by(email=email).first()
        
        if user:
            if user.is_verified:
                return render_template_string("<h1 style='color:#4CAF50; text-align:center;'>✅ Already Verified! You can login.</h1>")
                
            user.is_verified = True 
            db.session.commit()
            return render_template_string("<h1 style='color:#4CAF50; text-align:center;'>🎉 Success! Your email is verified.</h1>")
            
    except (SignatureExpired, BadSignature):
        return render_template_string("<h1 style='color:red; text-align:center;'>❌ Verification link is invalid or expired!</h1>")

    return "User not found", 404