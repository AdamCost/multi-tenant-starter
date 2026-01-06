# Multi-Tenant Starter

A production-ready SaaS boilerplate with multi-tenant architecture, authentication, and team management.

## Features

- **Authentication**: JWT-based auth with password reset and SSO-ready structure
- **Multi-Tenant Organizations**: Built-in organization/team management with role-based access control
- **Team Management**: Invite team members, manage roles (admin/editor/viewer)
- **API Key Management**: Generate API keys with scopes, rate limiting, and usage tracking
- **Settings Pages**: Pre-built profile and organization settings

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Database
- **Alembic** - Database migrations
- **JWT** - Authentication tokens

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **Axios** - HTTP client

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your database credentials and secrets

# Run database migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload --port 8001
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

Visit http://localhost:5173 to see the app.

## Project Structure

```
multi-tenant-starter/
├── backend/
│   ├── auth/              # Authentication & authorization
│   ├── models/            # SQLAlchemy models
│   ├── routes/            # API endpoints
│   ├── services/          # Business logic
│   ├── alembic/           # Database migrations
│   ├── main.py            # FastAPI app entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── context/       # React context (auth)
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   └── App.jsx        # Main app component
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password

### Organizations
- `GET /organizations` - List user's organizations
- `POST /organizations` - Create organization
- `GET /organizations/{id}` - Get organization details
- `PATCH /organizations/{id}` - Update organization

### Team Management
- `GET /organizations/{id}/members` - List team members
- `POST /organizations/{id}/invites` - Invite team member
- `DELETE /organizations/{id}/members/{user_id}` - Remove member

### API Keys
- `GET /api-keys` - List API keys
- `POST /api-keys` - Create API key
- `DELETE /api-keys/{id}` - Revoke API key

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:pass@localhost:5432/starter_db
SECRET_KEY=your-secret-key
SENDGRID_API_KEY=your-sendgrid-key
FROM_EMAIL=noreply@yourdomain.com
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8001
```

## Role-Based Access Control

| Role | View | Edit | Manage Team |
|------|------|------|-------------|
| Admin | Yes | Yes | Yes |
| Editor | Yes | Yes | No |
| Viewer | Yes | No | No |

## Customization

### Adding New Features
1. Create models in `backend/models/`
2. Add routes in `backend/routes/`
3. Create migrations with `alembic revision --autogenerate -m "description"`
4. Add frontend pages in `frontend/src/pages/`

### Branding
- Update logo in `frontend/src/components/Layout.jsx`
- Modify colors in `frontend/tailwind.config.js`
- Update app name in `backend/main.py`

## License

MIT
