const TerserPlugin = require('terser-webpack-plugin');
const WebpackObfuscator = require('webpack-obfuscator');

const isProd = process.env.NODE_ENV === 'production';

module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      if (isProd) {
        // Disable source maps in production
        webpackConfig.devtool = false;

        // Aggressive minification and mangling
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          minimize: true,
          minimizer: [
            new TerserPlugin({
              parallel: true,
              extractComments: false,
              terserOptions: {
                ecma: 2020,
                compress: {
                  drop_console: true,
                  drop_debugger: true,
                  dead_code: true,
                  passes: 3,
                  pure_funcs: [             
                    'console.log',
                    'console.info',
                    'console.debug',
                    'console.warn',
                    'console.error',
                    'console.trace',
                    'console.time',
                    'console.timeEnd'
                  ],
                },
                mangle: {
                  toplevel: true,
                  safari10: false,
                  properties: {
                    regex: /^_/ // mangle private-like properties
                  }
                },
                format: {
                  comments: false,
                },
                keep_fnames: false,
                keep_classnames: false,
              },
            }),
          ],
          splitChunks: {
            chunks: 'all',
            maxAsyncRequests: 25,
            maxInitialRequests: 25,
            minSize: 20000,
          },
          runtimeChunk: 'single',
          removeAvailableModules: true,
          removeEmptyChunks: true,
          usedExports: true,
          sideEffects: true,
        };

        // Add obfuscator late in plugin chain for app chunks only
        webpackConfig.plugins.push(
          new WebpackObfuscator(
            {
              rotateStringArray: true,
              stringArray: true,
              stringArrayThreshold: 0.75,
              stringArrayEncoding: ['base64'],
              stringArrayWrappersCount: 2,
              stringArrayWrappersType: 'function',
              compact: true,
              controlFlowFlattening: true,
              controlFlowFlatteningThreshold: 0.5,
              deadCodeInjection: true,
              deadCodeInjectionThreshold: 0,
              debugProtection: false,
              disableConsoleOutput: true,
              identifierNamesGenerator: 'hexadecimal',
              numbersToExpressions: true,
              simplify: true,
              splitStrings: true,
              splitStringsChunkLength: 10,
              transformObjectKeys: false,
              unicodeEscapeSequence: false,
            },
            [
              // Exclude vendor/runtime chunks to reduce breakage risk
              'runtime~*.js',
              'vendors*.js',
              'static/js/runtime-*.js',
              'static/js/*vendor*.js',
              'node_modules'
            ]
          )
        );
      }

      return webpackConfig;
    },
  },
  babel: {
    // plugins: isProd ? ['transform-remove-console'] : [],
  },
};


