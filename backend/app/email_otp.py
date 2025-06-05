# backend/app/email_otp.py

import logging
from backend.app.otp import generate_otp, store_otp, verify_otp
from backend.app.email_utils import send_otp_email

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def generate_and_send_otp(email: str) -> tuple[bool, str]:
    """
    Generate a 6‐digit OTP, store it in Redis, and send it via SendGrid.
    Returns (True, "Success message") or (False, "Error message").
    """
    otp = generate_otp()
    store_otp(email, otp)

    # send_otp_email returns True/False
    sent = send_otp_email(email, otp)
    if sent:
        return True, "OTP sent successfully!"
    else:
        return False, "Failed to send OTP."


def verify_user_otp(email: str, user_input_otp: str) -> bool:
    """
    Verify the user‐provided OTP against the one stored in Redis.
    If valid, returns True (and deletes the stored OTP). Otherwise, returns False.
    """
    return verify_otp(email, user_input_otp)


# Example CLI‐style testing (run with `python email_otp.py`)
if __name__ == "__main__":
    print("OTP Email Testing System")
    print("-" * 30)

    # Prompt for receiver email
    receiver_email = input("Enter the recipient's email address: ").strip()

    # Generate and send OTP
    success, msg = generate_and_send_otp(receiver_email)
    print(msg)
    if not success:
        exit(1)

    # Prompt user to enter received OTP
    print("\nOTP Verification")
    print("-" * 30)
    user_input_code = input("Enter the OTP you received: ").strip()

    if verify_user_otp(receiver_email, user_input_code):
        print("OTP verified successfully!")
    else:
        print("Invalid or expired OTP!")
