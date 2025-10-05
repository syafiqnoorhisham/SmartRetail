# SmartRetail - Django + Supabase Application

A modern Django application with Supabase backend for authentication and data management.

## 🚀 Features

- ✅ Django frontend application
- ✅ Supabase backend integration
- ✅ User authentication (Login/Logout)
- ✅ Beautiful modern UI design
- ✅ Responsive design for mobile and desktop
- ✅ Session management
- ✅ Flash messages for user feedback

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Supabase account and project

## 🛠️ Installation

### 1. Clone or Navigate to the Project

```bash
cd /Users/syafiqnoorhisham/Desktop/src/smartretail
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit the `.env` file and add your Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Django Secret Key
SECRET_KEY=your-secret-key-here-change-in-production

# Debug Mode
DEBUG=True

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 6. Setup Supabase

1. Go to [https://supabase.com](https://supabase.com)
2. Create a new project or use existing one
3. Enable Email authentication:
   - Go to Authentication > Providers
   - Enable Email provider
4. Copy your project URL and anon key:
   - Go to Settings > API
   - Copy `Project URL` and `anon/public key`
5. Create a test user:
   - Go to Authentication > Users
   - Click "Add user" > "Create new user"
   - Enter email and password

### 7. Run Database Migrations

```bash
python manage.py migrate
```

### 8. Create Superuser (Optional - for Django Admin)

```bash
python manage.py createsuperuser
```

### 9. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 10. Run Development Server

```bash
python manage.py runserver
```

The application will be available at: **http://127.0.0.1:8000/**

## 📁 Project Structure

```
smartretail/
├── smartretail/              # Project configuration
│   ├── __init__.py
│   ├── settings.py           # Django settings
│   ├── urls.py               # Main URL configuration
│   ├── wsgi.py               # WSGI configuration
│   └── asgi.py               # ASGI configuration
├── core/                     # Main application
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py              # View functions
│   ├── urls.py               # App URL configuration
│   ├── supabase_client.py    # Supabase client setup
│   ├── models.py             # Django models (minimal)
│   ├── admin.py
│   └── tests.py
├── templates/                # HTML templates
│   ├── base.html             # Base template
│   ├── login.html            # Login page
│   └── dashboard.html        # Dashboard page
├── static/                   # Static files
│   └── css/
│       └── style.css         # Main stylesheet
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables example
├── .gitignore               # Git ignore file
└── README.md                 # This file
```

## 🔐 Authentication Flow

1. User visits login page
2. Enters email and password
3. Django sends credentials to Supabase
4. Supabase validates and returns session token
5. Django stores session information
6. User is redirected to dashboard
7. Session is maintained until logout

## 🎨 Features Implemented

### Login Page
- Email and password fields
- Form validation
- "Forgot password" link (placeholder)
- "Sign up" link (placeholder)
- Modern gradient design matching the provided image
- Responsive layout

### Dashboard
- Simple success message
- User email display
- Logout functionality
- Clean, minimal design

### Session Management
- Secure session storage
- Auto-redirect if already logged in
- Protected dashboard route
- Proper logout handling

## 🔧 Configuration

### Supabase Settings

The application uses Supabase for:
- User authentication (sign in/sign up)
- Session management
- User data storage (future expansion)

### Django Settings

Key configurations in `settings.py`:
- Session timeout: 24 hours
- Static files served via WhiteNoise
- SQLite for Django admin (sessions, etc.)
- Supabase for user authentication

## 🚦 Usage

### Login
1. Navigate to `http://127.0.0.1:8000/`
2. Enter your Supabase user credentials
3. Click "Log in"
4. You'll be redirected to the dashboard on success

### Logout
1. Click the "Logout" button in the dashboard
2. You'll be redirected back to the login page

## 🐛 Troubleshooting

### Common Issues

**Issue:** `ValueError: Supabase URL and Key must be set`
**Solution:** Make sure your `.env` file exists and contains valid Supabase credentials.

**Issue:** Login fails with "Invalid credentials"
**Solution:** 
- Check if the user exists in Supabase Authentication
- Verify the email and password are correct
- Make sure Email authentication is enabled in Supabase

**Issue:** Static files not loading
**Solution:** Run `python manage.py collectstatic --noinput`

**Issue:** ImportError for supabase
**Solution:** Make sure you've installed all dependencies: `pip install -r requirements.txt`

## 📝 Development Notes

### Adding New Features

1. **Database tables:** Create them in Supabase dashboard
2. **Views:** Add to `core/views.py`
3. **URLs:** Register in `core/urls.py`
4. **Templates:** Create in `templates/` directory
5. **Static files:** Add to `static/` directory

### Best Practices

- Keep sensitive data in `.env` file
- Never commit `.env` to version control
- Use Supabase Row Level Security (RLS) for data protection
- Test authentication flows thoroughly
- Keep Django and dependencies updated

## 🔄 Future Enhancements

- [ ] Sign up functionality
- [ ] Password reset flow
- [ ] User profile page
- [ ] Dashboard with real data
- [ ] Role-based access control
- [ ] API endpoints for mobile/SPA
- [ ] Email verification
- [ ] Two-factor authentication

## 📚 Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)

## 🤝 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review Supabase logs in the dashboard
3. Check Django logs in the console
4. Review the Supabase Python client documentation

## 📄 License

This project is for educational and development purposes.

---

**Built with Django 5.0.1 and Supabase** 🚀
