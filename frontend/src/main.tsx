import React from 'react'
import ReactDOM from 'react-dom/client'
import { AppRouter } from './app/Router'
import './styles/globals.css'
import { instalarDetectorSesionVencida } from './shared/lib/sesionVencida'

instalarDetectorSesionVencida()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>,
)
