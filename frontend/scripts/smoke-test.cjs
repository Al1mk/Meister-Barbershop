#!/usr/bin/env node

/**
 * Smoke test script for Meister Barbershop frontend
 * Validates critical endpoints and media files are accessible
 */

const https = require('https');
const http = require('http');

// Configuration
const BASE_URL = process.env.SMOKE_TEST_URL || 'https://www.meisterbarbershop.de';
const TIMEOUT = 10000; // 10 seconds

// URLs to test
const ENDPOINTS = [
  '/api/barbers/',
  '/media/barbers/ali.jpg',
  '/media/barbers/ehsan.jpg',
  '/media/barbers/iman.jpg',
  '/media/barbers/javad.jpg',
];

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
};

/**
 * Make HTTP(S) GET request
 */
function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;
    const startTime = Date.now();

    const req = protocol.get(url, {
      timeout: TIMEOUT,
      headers: {
        'User-Agent': 'Meister-Barbershop-Smoke-Test/1.0',
      },
    }, (res) => {
      const duration = Date.now() - startTime;

      // Consume response data to free up memory
      res.on('data', () => {});
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          duration,
        });
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error(`Request timeout after ${TIMEOUT}ms`));
    });
  });
}

/**
 * Test a single endpoint
 */
async function testEndpoint(endpoint) {
  const url = `${BASE_URL}${endpoint}`;

  try {
    const result = await fetchUrl(url);
    const success = result.statusCode === 200;

    const status = success
      ? `${colors.green}✓ PASS${colors.reset}`
      : `${colors.red}✗ FAIL${colors.reset}`;

    console.log(`${status} ${endpoint} (${result.statusCode}) [${result.duration}ms]`);

    return {
      endpoint,
      success,
      statusCode: result.statusCode,
      duration: result.duration,
    };
  } catch (error) {
    console.log(`${colors.red}✗ FAIL${colors.reset} ${endpoint} - ${error.message}`);

    return {
      endpoint,
      success: false,
      error: error.message,
    };
  }
}

/**
 * Run all smoke tests
 */
async function runSmokeTests() {
  console.log(`${colors.blue}Running smoke tests against: ${BASE_URL}${colors.reset}\n`);

  const results = [];

  for (const endpoint of ENDPOINTS) {
    const result = await testEndpoint(endpoint);
    results.push(result);
  }

  // Summary
  const passed = results.filter(r => r.success).length;
  const failed = results.length - passed;

  console.log(`\n${'='.repeat(60)}`);
  console.log(`Summary: ${passed} passed, ${failed} failed (${results.length} total)`);
  console.log(`${'='.repeat(60)}\n`);

  if (failed > 0) {
    console.error(`${colors.red}Smoke tests failed!${colors.reset}`);
    process.exit(1);
  } else {
    console.log(`${colors.green}All smoke tests passed!${colors.reset}`);
    process.exit(0);
  }
}

// Run tests
if (require.main === module) {
  runSmokeTests().catch((error) => {
    console.error(`${colors.red}Fatal error:${colors.reset}`, error);
    process.exit(1);
  });
}

module.exports = { runSmokeTests, testEndpoint };
