module.exports = ({ config }) => {
  const iosClientId = process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID?.trim();
  const iosClientMatch = iosClientId?.match(/^(.+)\.apps\.googleusercontent\.com$/);

  if (iosClientId && !iosClientMatch) {
    throw new Error('EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID is not a valid Google OAuth client ID.');
  }

  const googlePlugin = iosClientMatch
    ? [[
        '@react-native-google-signin/google-signin',
        { iosUrlScheme: `com.googleusercontent.apps.${iosClientMatch[1]}` },
      ]]
    : [];

  return {
    ...config,
    experiments: process.env.MATHVISION_WEB_EXPORT === 'true'
      ? { ...config.experiments, baseUrl: '/study' }
      : config.experiments,
    plugins: [...(config.plugins ?? []), ...googlePlugin],
  };
};
