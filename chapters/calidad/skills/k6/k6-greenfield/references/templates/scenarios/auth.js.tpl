// {{project_name}} — scenarios/auth.js
// Flow reusable de autenticacion. Devuelve { token } o lanza error.
//
// Uso desde otro scenario:
//   import { login } from './auth.js';
//   const { token } = login();
//
// No define options: la carga la determina el workload que lo invoque.

import http from 'k6/http';
import { check, group } from 'k6';
import { config } from '../shared/config.js';

export function login() {
  let token;

  group('auth', () => {
    const res = http.post(
      `${config.authUrl}/login`,
      JSON.stringify({
        username: __ENV.AUTH_USERNAME || '{{auth_username}}',
        password: __ENV.AUTH_PASSWORD || '{{auth_password}}',
      }),
      {
        headers: { 'Content-Type': 'application/json' },
        tags: { endpoint: 'login', step: 'auth' },
      },
    );

    check(res, {
      'auth status 200': (r) => r.status === 200,
      'auth has token': (r) => typeof r.json('token') === 'string',
    }, { endpoint: 'login', step: 'auth' });

    try {
      token = res.json('token');
    } catch (_e) {
      token = undefined;
    }
  });

  if (!token) {
    throw new Error('auth: login no devolvio token. Verificar credenciales / endpoint.');
  }

  return { token };
}

// Default export opcional: permite usar este scenario aislado para validar el endpoint de login.
export default function () {
  login();
}
