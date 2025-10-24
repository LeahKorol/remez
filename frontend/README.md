# REMEZ Frontend

### Project Overview
REMEZ Frontend is a modern React application that provides a user-friendly interface for managing queries, performing statistical analysis, and integrating Google OAuth authentication for secure login and registration. This project emphasizes responsive UI, modular components, and clear error handling.

#

### Features
* User authentication with email/password and Google OAuth
* Email verification and password reset flows
* Dynamic query management with live status updates
* CSV and chart export of query results
* Responsive and intuitive UI with clear error messages
* Detailed statistical analysis visualization

#

### Tech Stack
* Frontend Framework: React 18+
* Routing: React Router DOM
* State Management: React Context & Hooks
* HTTP Client: Axios
* Notifications: react-toastify and ToastNotification component
* Charts: Chart.js (via RorChart component)
* Icons: react-icons (FaTimes, FaFileCsv, FaFileImage, FaArrowDown, etc.)

#

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/LeahKorol/remez.git
   cd frontend
   ```
2. Install dependencies:
   ```
   npm install
   ```
   or
   ```
   yarn install
   ```
#

### Environment Variables
Create a .env file in the root directory with the following variables:
```
# Auth cookies setting
JWT_AUTH_COOKIE=jwt-access
JWT_AUTH_REFRESH_COOKIE=jwt-refresh
JWT_AUTH_SECURE=False
JWT_AUTH_HTTPONLY=True
ACCESS_TOKEN_LIFETIME_HOURS=4
REFRESH_TOKEN_LIFETIME_DAYS=7 

# CORS origins
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
# http://localhost:5173,http://127.0.0.1:5173

# Google OAuth Settings 
REACT_APP_GOOGLE_CLIENT_ID=<YOUR_ID>
REACT_APP_GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback,http://127.0.0.1:3000/auth/google/callback

# Frontend URLs
# <EMAIL_CONFIRM_REDIRECT_BASE_URL>/<key>
EMAIL_CONFIRM_REDIRECT_BASE_URL=http://localhost:3000/email/confirm/
# <PASSWORD_RESET_CONFIRM_REDIRECT_BASE_URL>/<uidb64>/<token>/
PASSWORD_RESET_CONFIRM_REDIRECT_BASE_URL=http://localhost:3000/password-reset/confirm/
```

#

### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create an OAuth 2.0 Client ID for a Web Application
3. Set authorized JavaScript origins (e.g., http://localhost:3000)
4. Add REACT_APP_GOOGLE_CLIENT_ID to your .env file

#

### Folder Structure
```
frontend/
│
├─ node-modules/
├─ public/               # Static assets
|  └─ images/ 
├─ src/
│  ├─ components/        # Reusable components (GoogleAuth, Charts, Modals)
│  ├─ pages/             # Page components (Home, Login, Registration, UserProfile, etc.)
│  |  ├─ App.js          # Root App component
│  ├─ utils/             # Helper functions, API services, token refresh
│  ├─ axiosConfig.js     # Axios instance configuration
│  └─ index.js           #  App entry point
├─ .env                  # Environment variables
├─ package.json
└─ README.md
```

#

### Running the Application
1. Start the development server:
   ```
   npm start
   ```
   or
   ```
   yarn start
   ```
2. The app will run on http://localhost:3000 by default.

#

### Components Overview

#### Authentication
- **GoogleAuthService**: Handles Google OAuth popup login, user profile fetching, and backend authentication.
- **useGoogleAuth**: React hook wrapping GoogleAuthService with loading and error states.
- **GoogleAuthButton**: Button component for login/registration with Google.

#### UI Components
- **QueryDetailsView**: Displays detailed query info, chart (RorChart), drugs, reactions, CSV/PNG export, and dynamic status refresh.  
  **Props**: `query`, `handleNewQuery`, `refreshQuery`.
- **QueryForm**: Handles creation/editing of queries with dynamic drug/reaction lists, input validation, and submission.  
  **Props**: `onSubmit`, `onCancel`, `showToastMessage`, `isEditing`, `isSubmitting`, `resetTrigger`, initial field values.
- **RorChart**: Line chart of ROR values with log₁₀ transformation, confidence intervals, zoom/pan, and responsive layout.  
  **Props**: `query`, `year_start`, `quarter_start`.
- **SavedQueriesList**: Lists saved queries with view, edit, and delete actions. Locks actions for processing queries.  
  **Props**: `savedQueries`, `onViewQuery`, `onEditQuery`, `onDeleteQuery`, `editingQueryId`, `isEditing`, `editingQueryLoading`.
- **Sidebar**: User sidebar with avatar, saved queries, search, navigation, and logout popup.  
  **Props**: `user`, `savedQueries`, callbacks for actions, and logout.
- **ToastNotification**: Temporary on-screen messages for errors, warnings, info; auto-dismisses and stacks smoothly.  
  **Props**: `id`, `message`, `type`, `duration`, `onClose`, `index`.
- **TutorialCarousel**: Step-by-step tutorial overlay guiding users through REMEZ workflow (15 slides).  
  **Props**: `open`, `onClose`.  
  **Features**: Keyboard navigation, skip/got-it buttons, responsive modal, accessible, reusable from "?" icon.

### Pages Overview

- **Home**: Landing page of the application with general introduction and navigation.  
- **Login**: Handles user login, error messages, forgot password, and authentication flows.  
- **PasswordReset**: Page for requesting password reset email.  
- **PasswordResetConfirm**: Page for setting a new password via a reset token.  
- **Register**: User registration form.  
- **EmailVerify**: Handles email verification via a key in the URL.  
- **EmailVerificationSent**: Informs the user that a verification email has been sent.  
- **UserProfile**: Main user dashboard, displaying saved queries, query details, ROR charts, CSV/PNG exports, and dynamic status refresh.  
- **QueryResultPage**: Displays the detailed results of a specific query.  
- **AnalysisEmailNotification**: Informs the user that an analysis is ready and sent by email, and provides a quick link to view results.  
- **PrivacyPolicy**: Static page with the website's privacy policy.  
- **AboutResearch**: Static page describing the REMEZ research methodology, including a link to Dr. Boris Gorelik's main research.  
- **LoadingPage**: Shows a loading spinner while waiting for async operations.  
- **NotFoundPage (404)**: Displays 404 error for unknown routes.  
- **ServerErrorPage (500)**: Displays server error message.  
- **MaintenancePage**: Informs users of system maintenance.  
- **SessionExpiredPage**: Informs users when the session has expired and redirects to login.  

### Utilities Overview
- **validateQueryForm(formData)**  
  Validates query form fields and returns an array of error messages.  
  *Checks*: at least one valid drug & reaction, proper time range (≥2 periods, ≤10 years), meaningful query name (≥3 chars).
- **showToastMessage(message, type = "success")**  
  Shows a toast notification (`"success" | "error" | "info"`).
- **TokenService / fetchWithRefresh**  
  Manages JWT tokens and authenticated fetch requests with automatic refresh on 401.  
  *Usage*: `fetchWithRefresh(url, options)`.
- **UserContext / UserProvider / useUser**  
  React context for user session: provides `userId`, `login(id)`, and `logout()`.  
  *Hook*: `useUser()` for accessing context anywhere.

#

### Error Handling
* Backend errors are parsed and displayed via toast notifications and inline messages.
* Login, registration, and password reset flows handle 401, 404, 409, 500, and validation errors gracefully.
* Network errors are caught and reported to the user.
