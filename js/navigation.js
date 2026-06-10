// js/navigation.js
import { login } from './auth.js';

const form = document.getElementById('loginForm');
const msg  = document.getElementById('loginMessage');

form.addEventListener('submit', async e => {
  e.preventDefault();
  msg.textContent = '⏳ Autenticando...';
  try {
    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const payload  = await login(email, password);
    const role     = payload.role; // ajusta si tu claim se llama diferente
    // Redirige a la página en roles/{role}.html
    window.location.href = `roles/${role}.html`;
  } catch (err) {
    msg.textContent = '❌ ' + err.message;
  }
});

