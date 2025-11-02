# Meister Barbershop - Frontend

Modern React frontend for Meister Barbershop booking system.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **i18next** - Internationalization (German/English)
- **Sentry** - Error tracking (optional)

## Getting Started

### Prerequisites

- Node.js 20.x or later
- npm 10.x or later

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.sample .env

# Start development server
npm run dev
```

The app will be available at http://localhost:5173

## Available Scripts

### Development

```bash
# Start dev server with hot reload
npm run dev

# Preview production build locally
npm run preview
```

### Build

```bash
# Build for production
npm run build

# Output will be in ./dist directory
```

### Quality Checks

```bash
# Run ESLint
npm run lint

# Auto-fix linting issues
npm run lint:fix

# Run smoke tests (requires production URL)
npm run smoke

# Run smoke tests against custom URL
SMOKE_TEST_URL=https://staging.example.com npm run smoke
```

## Environment Variables

Create a `.env` file based on `.env.sample`:

### Required

- `VITE_API_BASE` - API base URL (default: `/api`)

### Optional

- `VITE_SENTRY_DSN` - Sentry DSN for error tracking (leave empty to disable)
- `VITE_RELEASE` - Release version for Sentry (automatically set in CI)

### Example `.env` file

```env
VITE_API_BASE=/api

# Uncomment to enable Sentry
# VITE_SENTRY_DSN=https://your-dsn@sentry.io/your-project-id
```

## Code Quality

### Linting

ESLint is configured with React best practices:

```bash
# Check for linting errors
npm run lint

# Auto-fix issues
npm run lint:fix
```

### Pre-commit Hooks

Husky and lint-staged automatically run `eslint --fix` on staged files before each commit.

### CI/CD

GitHub Actions runs the following checks on each push/PR:
1. ESLint (fails on errors)
2. Build (must succeed)
3. Smoke tests (checks critical endpoints)

## Sentry Error Tracking

Sentry integration is **optional** and only activates when `VITE_SENTRY_DSN` is set.

### Setup

1. Create a Sentry project at https://sentry.io
2. Copy your DSN
3. Add to `.env`:
   ```
   VITE_SENTRY_DSN=https://your-key@sentry.io/your-project-id
   ```

### Features

- **Error tracking** - Automatic capture of unhandled errors
- **Performance monitoring** - 10% sample rate for API calls
- **Privacy-first** - No PII collected, IPs stripped
- **Smart filtering** - Ignores browser extensions and non-critical errors

### Testing Sentry

```javascript
// Trigger a test error (dev console)
throw new Error('Sentry test error');
```

## Smoke Tests

Smoke tests validate critical production endpoints:

```bash
# Test production
npm run smoke

# Test custom URL
SMOKE_TEST_URL=https://staging.example.com npm run smoke
```

### Tested Endpoints

- `/api/barbers/` - Barber list API
- `/media/barbers/ali.jpg` - Barber photos
- `/media/barbers/ehsan.jpg`
- `/media/barbers/iman.jpg`
- `/media/barbers/javad.jpg`

## Image Optimization

### WebP Support

The frontend automatically serves WebP images when available, with fallback to JPEG:

```jsx
<picture>
  <source type="image/webp" srcset="/media/barbers/ali.webp" />
  <img src="/media/barbers/ali.jpg" loading="lazy" decoding="async" alt="Ali" />
</picture>
```

### Best Practices

- Images use `loading="lazy"` for performance
- `decoding="async"` prevents blocking the main thread
- WebP reduces file size by ~30% with same quality

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   │   ├── BarberCard.jsx
│   │   └── ...
│   ├── pages/          # Page components (routes)
│   ├── hooks/          # Custom React hooks
│   ├── lib/            # Utilities
│   │   ├── api.js      # API client
│   │   └── sentry.js   # Sentry integration
│   ├── i18n/           # Translations (de, en)
│   ├── data/           # Static data
│   ├── styles.css      # Global styles
│   ├── App.jsx         # Root component
│   └── main.jsx        # Entry point
├── scripts/
│   └── smoke-test.js   # Smoke test runner
├── public/             # Static assets
├── .eslintrc.cjs       # ESLint config
├── vite.config.js      # Vite config
└── package.json        # Dependencies & scripts
```

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use a different port
npm run dev -- --port 3000
```

### Build Fails

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
```

### Linting Errors

```bash
# Auto-fix most issues
npm run lint:fix

# Check what can't be auto-fixed
npm run lint
```

## Contributing

1. Create a feature branch
2. Make changes
3. Run `npm run lint:fix`
4. Commit (pre-commit hooks will run automatically)
5. Push and create a PR (CI will run quality checks)

## License

Proprietary - Meister Barbershop
