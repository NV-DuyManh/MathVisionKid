// MathVision identity and native assets have one source: app.json.
module.exports = ({ config }) => process.env.MATHVISION_WEB_EXPORT === 'true'
  ? { ...config, experiments: { ...config.experiments, baseUrl: '/study' },
      web: process.env.MATHVISION_WEB_PREVIEW === 'true' ? { ...config.web, output: 'single' } : config.web }
  : config;
