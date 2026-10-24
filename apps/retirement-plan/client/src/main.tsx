import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/tokens.css'; // shared design tokens (ACC-APP-IA) — partner rebrand = edit BRAND LAYER only

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);