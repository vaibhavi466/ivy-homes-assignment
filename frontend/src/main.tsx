import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './aesthetic-base.css'
import './aesthetic-auth.css'
import './aesthetic-cards.css'
import './aesthetic-detail.css'
import './aesthetic-analytics.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
