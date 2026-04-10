from shop.auth import auth_bp

from shop.auth.api.login import login_action
from shop.auth.api.signup import signup_action
from shop.auth.api.verify_email import verify_email_action
from shop.auth.api.refresh import refresh_action
from shop.auth.api.profile import profile_action
from shop.auth.api.logout import logout_action
from shop.auth.api.forgot_password import forgot_password_action
from shop.auth.api.reset_password import reset_password_action

@auth_bp.route('/login', methods=['POST'])
def login_route():
    return login_action()

@auth_bp.route('/signup', methods=['POST'])
def signup_route():
    return signup_action()

@auth_bp.route('/verify/<token>', methods=['GET'])
def verify_email_route(token):
    return verify_email_action(token)

@auth_bp.route('/refresh', methods=['POST'])
def refresh_route():
    return refresh_action()

@auth_bp.route('/profile', methods=['GET'])
def profile_route():
    return profile_action()

@auth_bp.route('/logout', methods=['POST'])
def logout_route():
    return logout_action()

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password_route():
    return forgot_password_action()

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password_route():
    return reset_password_action()