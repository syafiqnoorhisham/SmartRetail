"""
Quick test script to verify SendGrid email configuration
Run this to test if SendGrid is working properly
"""

import os
from dotenv import load_dotenv
from django.core.mail import send_mail
from django.conf import settings

# Load environment variables
load_dotenv()

# Configure Django settings if not already configured
if not settings.configured:
    settings.configure(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        EMAIL_HOST=os.getenv('EMAIL_HOST', 'smtp.sendgrid.net'),
        EMAIL_PORT=int(os.getenv('EMAIL_PORT', 587)),
        EMAIL_USE_TLS=os.getenv('EMAIL_USE_TLS', 'True') == 'True',
        EMAIL_HOST_USER=os.getenv('EMAIL_HOST_USER', 'apikey'),
        EMAIL_HOST_PASSWORD=os.getenv('EMAIL_HOST_PASSWORD', ''),
        DEFAULT_FROM_EMAIL=os.getenv('DEFAULT_FROM_EMAIL', 'noreply@smartretail.com'),
    )

def test_sendgrid():
    """Test SendGrid email sending"""
    
    print("=" * 60)
    print("🧪 SendGrid Configuration Test")
    print("=" * 60)
    
    # Show configuration (hide password)
    print(f"\n📧 Email Configuration:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   Host: {settings.EMAIL_HOST}")
    print(f"   Port: {settings.EMAIL_PORT}")
    print(f"   TLS: {settings.EMAIL_USE_TLS}")
    print(f"   User: {settings.EMAIL_HOST_USER}")
    print(f"   Password: {'*' * 20} (hidden)")
    print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
    
    # Get test email
    test_email = input("\n📬 Enter your test email address: ").strip()
    
    if not test_email:
        print("❌ No email provided. Exiting.")
        return
    
    print(f"\n📤 Sending test email to: {test_email}")
    print("⏳ Please wait...")
    
    try:
        # Send test email
        send_mail(
            subject='🎉 SendGrid Test - SmartRetail',
            message='This is a test email from SmartRetail to verify SendGrid configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        print("\n✅ SUCCESS! Email sent successfully!")
        print(f"📬 Check your inbox at: {test_email}")
        print("\n💡 If you don't see it:")
        print("   1. Check your spam/junk folder")
        print("   2. Wait a few minutes (SendGrid can take 1-2 minutes)")
        print("   3. Verify sender authentication in SendGrid dashboard")
        
    except Exception as e:
        print(f"\n❌ FAILED! Error sending email:")
        print(f"   {type(e).__name__}: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify your SendGrid API key is correct")
        print("   2. Check if sender email is verified in SendGrid")
        print("   3. Ensure EMAIL_HOST_USER='apikey' (literally 'apikey')")
        print("   4. Check SendGrid dashboard for error logs")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_sendgrid()
