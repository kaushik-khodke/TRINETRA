import cesium from 'vite-plugin-cesium';

/**
 * Creates the browser Vite configuration with Cesium plugin, security headers,
 * and environment variable bindings.
 */
export function createBrowserViteConfig(options = {}) {
  const {
    plugins = [],
    googleApiKey,
    cesiumToken,
    host = 'localhost',
    port = 4173,
  } = options;

  const parsedPort = typeof port === 'string' ? Number.parseInt(port, 10) : (port || 4173);

  const define = {};
  if (googleApiKey !== undefined) {
    define['import.meta.env.GOOGLE_MAPS_API_KEY'] = JSON.stringify(googleApiKey);
  }
  if (cesiumToken !== undefined) {
    define['import.meta.env.CESIUM_ION_TOKEN'] = JSON.stringify(cesiumToken);
  }

  const isAnyHost = host === '0.0.0.0' || host === '::';

  return {
    plugins: [cesium(), ...plugins],
    define,
    server: {
      host,
      port: parsedPort,
      allowedHosts: isAnyHost ? true : ['localhost', '127.0.0.1', '.local'],
      fs: {
        deny: ['**/ENVIRONMENT', '.env.*'],
      },
      headers: {
        'X-Frame-Options': 'DENY',
        'Content-Security-Policy': "frame-ancestors 'none'",
      },
    },
  };
}

export default createBrowserViteConfig;
