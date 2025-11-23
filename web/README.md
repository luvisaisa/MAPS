# RA-D-PS Web Interface

modern react-based web interface for the radiology annotation data processing system (ra-d-ps).

## overview

this web interface provides a user-friendly frontend for uploading, processing, and managing radiology xml data. it connects to the fastapi backend and offers functionality equivalent to the tkinter gui with enhanced usability and modern design.

## features

- **file upload & processing**: drag-and-drop xml file upload with batch processing
- **profile management**: create, edit, and manage parsing profiles
- **processing history**: view and filter processing jobs with real-time status
- **export options**: download results in excel, json, or csv formats
- **dashboard analytics**: view processing statistics and trends
- **responsive design**: works on desktop, tablet, and mobile devices

## technology stack

- react 19 with typescript
- vite - build tool and dev server
- tailwind css 3 - utility-first css framework
- react router - client-side routing
- tanstack query (react query) - server state management
- axios - http client
- zustand - lightweight state management
- recharts - data visualization
- react dropzone - file upload with drag-and-drop
- vitest - testing framework

## getting started

### installation

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
