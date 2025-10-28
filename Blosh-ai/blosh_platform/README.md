# Blosh Platform

A clean and simple React platform with Python Flask backend, styled in the Blosh aesthetic.

## Features

- 🔐 Simple password authentication (no signup required)
- 🎨 Clean white background with black text (Blosh style)
- 📱 Fully responsive design
- 🔔 Toast notifications for success/error messages
- 🔄 Session persistence (stays logged in on refresh)
- 📊 Sidebar navigation for future tools

## Prerequisites

- Python 3.7 or higher
- Node.js 14 or higher
- npm or yarn

## Quick Start

### Option 1: Using the start script (Recommended)

```bash
cd blosh_platform
chmod +x start.sh
./start.sh
```

This will automatically:
- Install all dependencies
- Start the backend server on port 5000
- Start the frontend server on port 3000
- Open the application in your browser

### Option 2: Manual start

#### Backend

```bash
cd blosh_platform/backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

#### Frontend

```bash
cd blosh_platform/frontend
npm install
npm start
```

## Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Password**: `Bloshai12!`

## Project Structure

```
blosh_platform/
├── backend/
│   ├── app.py              # Flask application with authentication
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.js         # Login page
│   │   │   ├── Dashboard.js     # Main dashboard
│   │   │   ├── Sidebar.js       # Navigation sidebar
│   │   │   └── Home.js          # Home page
│   │   ├── services/
│   │   │   └── api.js           # API service layer
│   │   ├── App.js               # Main app component
│   │   └── index.js             # Entry point
│   └── package.json
├── start.sh                # Startup script
└── README.md
```

## Features Implemented

### Authentication
- Hardcoded password authentication
- Session-based login (persists on refresh)
- Secure logout functionality

### UI/UX
- Clean, minimal design matching Blosh branding
- Responsive sidebar navigation
- Mobile-friendly hamburger menu
- Toast notifications for user feedback

### Technical
- React Router for navigation
- Axios for API calls
- Flask-CORS for cross-origin requests
- Session management with Flask sessions

## Adding New Tools

To add new tools to the sidebar:

1. Create a new component in `frontend/src/components/`
2. Add the route in `Dashboard.js`
3. Add the menu item in `Sidebar.js`

Example:

```javascript
// In Sidebar.js
const menuItems = [
  { name: 'Home', path: '/', icon: '🏠' },
  { name: 'New Tool', path: '/new-tool', icon: '🔧' }
];

// In Dashboard.js
<Routes>
  <Route path="/" element={<Home />} />
  <Route path="/new-tool" element={<NewTool />} />
</Routes>
```

## Security Note

⚠️ This is a development setup with a hardcoded password. For production use:
- Use environment variables for sensitive data
- Implement proper user authentication
- Enable HTTPS
- Use secure session configuration
- Add rate limiting

## License

Proprietary - Blosh Fashion Company

