# MAPS Web Interface

modern react-based web interface for the medical imaging processing suite (maps).

## overview

this web interface provides a user-friendly frontend for uploading, processing, and managing medical imaging xml data. it connects to the fastapi backend and offers functionality equivalent to the tkinter gui with enhanced usability and modern design.

## features

### core functionality
- **file upload & processing**: drag-and-drop xml/json file upload with batch processing
- **profile management**: create, edit, and manage parsing profiles for different data formats
- **processing history**: view and filter processing jobs with pagination
- **export options**: download results in excel, json, csv, or sqlite formats
- **dashboard analytics**: view processing statistics, trends, and insights

### real-time features
- **live progress tracking**: websocket and sse support for real-time job updates
- **supabase realtime**: automatic ui updates when database changes occur
- **job notifications**: instant feedback on processing status

### advanced features
- **keyword extraction**: automated medical terminology extraction and normalization
- **keyword search**: semantic search across extracted keywords with filtering
- **3d visualization**: interactive nodule visualization from lidc/idri data
- **pylidc integration**: seamless integration with pylidc library for lung ct analysis
- **analytics dashboard**: parse case distribution, inter-rater reliability, data completeness
- **advanced search**: full-text search with filters across all processed documents

### design
- **responsive design**: works on desktop, tablet, and mobile devices
- **modern ui**: built with tailwind css for clean, professional interface
- **accessibility**: wcag 2.1 compliant components

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
