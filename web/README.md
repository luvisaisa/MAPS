# RA-D-PS Web Interface

Modern React-based web interface for the Radiology XML Data Processing System.

## Technology Stack

- React 18+ with TypeScript
- Vite - Build tool and dev server
- Tailwind CSS - Utility-first CSS framework
- React Router - Client-side routing
- TanStack Query (React Query) - Server state management
- Axios - HTTP client
- Zustand - Lightweight state management
- Recharts - Data visualization
- React Dropzone - File upload with drag-and-drop
- Vitest - Testing framework

## Getting Started

### Installation

```bash
npm install
npm run dev
```

Application will be available at http://localhost:5173

### Environment Variables

The `.env` file contains:
```
VITE_API_URL=http://localhost:8000
VITE_ENV=development
```

## Features

### Implemented (Phase 1 Complete)
- Project setup with Vite + React + TypeScript
- Tailwind CSS configuration
- API client with TypeScript types
- Basic layout (Header, Sidebar)
- React Router configuration
- React Query setup
- Dashboard page skeleton

### Next Implementation Phases
- Phase 2: File Upload & Processing
- Phase 3: Profile Management
- Phase 4: History & Results
- Phase 5: Dashboard & Analytics
- Phase 6: Testing & Optimization

## API Integration

Connects to FastAPI backend on port 8000.
See http://localhost:8000/docs for API documentation.

## Development

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run test         # Run tests
```

## Documentation

See main project CLAUDE.md for development guidelines.
