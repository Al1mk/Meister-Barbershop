/**
 * Sentry Error Tracking Integration
 *
 * Only initializes if VITE_SENTRY_DSN is set in environment variables.
 * No PII (Personally Identifiable Information) is collected.
 */

import * as Sentry from '@sentry/react';

/**
 * Initialize Sentry error tracking
 *
 * @returns {boolean} Whether Sentry was initialized
 */
export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN;

  // Skip initialization if no DSN is provided
  if (!dsn) {
    console.log('Sentry: Skipping initialization (no VITE_SENTRY_DSN set)');
    return false;
  }

  try {
    Sentry.init({
      dsn,

      // Environment and release tracking
      environment: import.meta.env.MODE || 'production',
      release: import.meta.env.VITE_RELEASE || 'unknown',

      // Integrations
      integrations: [
        // Browser tracing for performance monitoring
        new Sentry.BrowserTracing({
          // Set sample rate for performance monitoring
          tracePropagationTargets: [
            'localhost',
            /^https:\/\/www\.meisterbarbershop\.de/,
          ],
        }),
        // Replay integration for session replay (optional)
        new Sentry.Replay({
          maskAllText: true,
          blockAllMedia: true,
        }),
      ],

      // Performance monitoring sample rate (10%)
      tracesSampleRate: 0.1,

      // Session replay sample rate
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,

      // Privacy: Do not send any PII
      beforeSend(event) {
        // Strip potential PII from error messages
        if (event.request) {
          delete event.request.cookies;
          delete event.request.headers;
        }

        // Remove user IP
        if (event.user) {
          delete event.user.ip_address;
        }

        return event;
      },

      // Filter out known non-critical errors
      ignoreErrors: [
        // Browser extensions
        'top.GLOBALS',
        'chrome-extension://',
        'moz-extension://',
        // Network errors (handled by app)
        'Network request failed',
        'NetworkError',
        'Failed to fetch',
        // ResizeObserver (non-critical)
        'ResizeObserver loop limit exceeded',
      ],

      // Deny URLs (don't report errors from these scripts)
      denyUrls: [
        /extensions\//i,
        /^chrome:\/\//i,
        /^moz-extension:\/\//i,
      ],
    });

    console.log('Sentry: Initialized successfully');
    return true;
  } catch (error) {
    console.error('Sentry: Initialization failed', error);
    return false;
  }
}

/**
 * Capture a custom error or message
 *
 * @param {Error|string} error - Error object or message
 * @param {object} context - Additional context
 */
export function captureError(error, context = {}) {
  if (!import.meta.env.VITE_SENTRY_DSN) {
    console.error('Error:', error, context);
    return;
  }

  Sentry.captureException(error, {
    extra: context,
  });
}

/**
 * Set user context (use carefully to avoid PII)
 *
 * @param {object} user - User context (no PII!)
 */
export function setUserContext(user) {
  if (!import.meta.env.VITE_SENTRY_DSN) {
    return;
  }

  // Only set anonymous identifiers, no PII
  Sentry.setUser({
    id: user.id || 'anonymous',
  });
}

/**
 * Add breadcrumb for debugging
 *
 * @param {string} message - Breadcrumb message
 * @param {object} data - Additional data
 */
export function addBreadcrumb(message, data = {}) {
  if (!import.meta.env.VITE_SENTRY_DSN) {
    return;
  }

  Sentry.addBreadcrumb({
    message,
    data,
    level: 'info',
  });
}
