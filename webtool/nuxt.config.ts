// https://nuxt.com/docs/api/configuration/nuxt-config
const TESTSUITE_API_BASE =
  process.env.TESTSUITE_API_BASE || 'http://localhost:8000/api'
const PROXY_API_BASE =
  process.env.PROXY_API_BASE || 'http://localhost:8080/api'

export default defineNuxtConfig({
  app: {
    head: {
      title: 'DSM TestSuite',
      meta: [
        { name: 'description', content: 'TestSuite to challenge your P2P Network' }
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
      ]
    }
  },
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@pinia/nuxt'
  ],

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    public: {
      // Dev only: `nuxt dev` can't proxy websocket upgrades, so the browser connects to the backend directly.
      // In production (empty) the socket goes through the gateway on the page's own origin.
      testsuiteWsPort: process.env.TESTSUITE_WS_PORT ?? (process.env.NODE_ENV === 'production' ? '' : '8000'),
      proxyWsPort: process.env.PROXY_WS_PORT ?? (process.env.NODE_ENV === 'production' ? '' : '8080'),
    }
  },

  routeRules: {
    '/': { prerender: true }
  },

  compatibilityDate: '2026-06-30',

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  },
  devServer: {
    host: '0.0.0.0',
    port: 3000,
  },
  vite: {
    build: {
      // Kiosk hosts run Windows Server 2012, whose ceiling is Firefox ESR 115
      // (still patched) and Chrome/Edge 109 (frozen since Jan 2023) - matches
      // ../trainlist-frontend's .browserslistrc.
      target: ['chrome109', 'firefox115', 'edge109', 'safari16'],
    },
    server: {
      proxy: {
        '/testsuite': {
          target: TESTSUITE_API_BASE,
          changeOrigin: true,
          secure: false,
          rewrite: (p) => p.replace(/^\/testsuite/, ''),
        },
        '/proxy': {
          target: PROXY_API_BASE,
          changeOrigin: true,
          secure: false,
          rewrite: (p) => p.replace(/^\/proxy/, ''),
        }
      },
    },
    optimizeDeps: {
      include: [
        'mapbox-gl', // CJS
        'threebox-plugin/main.js', // CJS
        'zod',
      ],
    },
  },
})
