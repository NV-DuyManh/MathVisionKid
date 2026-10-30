// MathVision identity and native assets have one source: app.json.
module.exports = ({ config }) => process.env.MATHVISION_WEB_EXPORT === 'true'
  ? { ...config, experiments: { ...config.experiments, baseUrl: '/study' } }
  : config;
