from shop.auth import auth_bp

# Import APIs
from shop.auth.api.signup import signup_action
from shop.auth.api.login import login_action
from shop.auth.api.logout import logout_action
from shop.auth.api.profile import profile_action
from shop.auth.api.profile_delete import profile_delete_action
from shop.auth.api.refresh import refresh_action
from shop.auth.api.forgot_password import forgot_password_action
from shop.auth.api.reset_password import reset_password_action
from shop.auth.api.verify_email import verify_email_action

@auth_bp.route('/signup', methods=['POST'])
def signup_route():
    """
    User Registration (Signup)
    ---
    tags:
      - 🔐 Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            username: {type: string}
            email: {type: string}
            password: {type: string}
            phone: {type: string}
            role: {type: string, enum: ['user', 'seller']}
    responses:
      201:
        description: User created successfully
    """
    return signup_action()

@auth_bp.route('/login', methods=['POST'])
def login_route():
    """
    User Login
    ---
    tags:
      - 🔐 Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            email: {type: string}
            password: {type: string}
    responses:
      200:
        description: Returns Access & Refresh Tokens
    """
    return login_action()

@auth_bp.route('/refresh-token', methods=['POST'])
def refresh_route():
    """
    Refresh Access Token
    ---
    tags:
      - 🔐 Authentication
    responses:
      200:
        description: New Access Token generated
    """
    return refresh_action()

@auth_bp.route('/profile', methods=['GET'])
def profile_route():
    """
    Get User Profile
    ---
    tags:
      - 👤 User Profile
    responses:
      200:
        description: User details fetched
    """
    return profile_action()

@auth_bp.route('/logout', methods=['POST'])
def logout_route():
    """
    Logout User
    ---
    tags:
      - 🔐 Authentication
    responses:
      200:
        description: Successfully logged out
    """
    return logout_action()

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password_route():
    """
    Forgot Password (Send OTP)
    ---
    tags:
      - 🔐 Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            email: {type: string}
    responses:
      200:
        description: OTP sent to email
    """
    return forgot_password_action()

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password_route():
    """
    Reset Password using OTP
    ---
    tags:
      - 🔐 Authentication
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            email: {type: string}
            otp: {type: string}
            new_password: {type: string}
    responses:
      200:
        description: Password reset successful
    """
    return reset_password_action()

@auth_bp.route('/delete-account', methods=['DELETE'])
def delete_account_route():
    """
    Delete User Account
    ---
    tags:
      - 👤 User Profile
    responses:
      200:
        description: Account deleted
    """
    return profile_delete_action()