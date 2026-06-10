function fn() {
  var env = karate.env || '{{env}}';
  karate.log('karate.env =', env);

  var config = {
    baseUrl: '{{baseUrl}}',
    ssl: true,
    connectTimeout: 5000,
    readTimeout: 5000
  };

  if (env === 'dev') {
    config.baseUrl = '{{baseUrl}}';
  }
  if (env === 'qa') {
    config.baseUrl = '{{baseUrl}}';
  }
  if (env === 'staging') {
    config.baseUrl = '{{baseUrl}}';
  }
  if (env === 'prod') {
    config.baseUrl = '{{baseUrl}}';
  }

  return config;
}
