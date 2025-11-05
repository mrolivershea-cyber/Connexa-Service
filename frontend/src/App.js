import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import LoginPage from './components/LoginPage';
import AdminPanel from './components/AdminPanel';
import ChangePasswordPage from './components/ChangePasswordPage';
import ProtectedRoute from './components/ProtectedRoute';
import AuthProvider from './contexts/AuthContext';
import { TestingProvider } from './contexts/TestingContext';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <TestingProvider>
        <Router>
          <div className="App">
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/change-password" element={
                <ProtectedRoute>
                  <ChangePasswordPage />
                </ProtectedRoute>
              } />
              <Route path="/" element={
                <ProtectedRoute>
                  <AdminPanel />
                </ProtectedRoute>
              } />
            </Routes>
            <Toaster />
          </div>
        </Router>
      </TestingProvider>
    </AuthProvider>
  );
}

export default App;
