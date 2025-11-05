import React, { createContext, useContext, useState, useEffect } from 'react';

const TestingContext = createContext();

export const TestingProvider = ({ children }) => {
  const [activeSessions, setActiveSessions] = useState(new Map());

  // Add a new testing session (from import or manual testing)
  const addSession = (sessionId, source = 'manual', nodeIds = [], testType = 'ping') => {
    const session = {
      sessionId,
      source, // 'import' or 'manual'
      nodeIds,
      testType,
      status: 'running',
      startTime: Date.now()
    };
    
    setActiveSessions(prev => {
      const newMap = new Map(prev);
      newMap.set(sessionId, session);
      return newMap;
    });
    
    // Auto-cleanup after 30 minutes
    setTimeout(() => {
      removeSession(sessionId);
    }, 30 * 60 * 1000);
    
    return session;
  };

  // Update session status
  const updateSession = (sessionId, updates) => {
    setActiveSessions(prev => {
      const newMap = new Map(prev);
      if (newMap.has(sessionId)) {
        newMap.set(sessionId, { ...newMap.get(sessionId), ...updates });
      }
      return newMap;
    });
  };

  // Remove completed/cancelled session
  const removeSession = (sessionId) => {
    setActiveSessions(prev => {
      const newMap = new Map(prev);
      newMap.delete(sessionId);
      return newMap;
    });
  };

  // Get active session from import
  const getActiveImportSession = () => {
    for (const [sessionId, session] of activeSessions) {
      if (session.source === 'import' && session.status === 'running') {
        return session;
      }
    }
    return null;
  };

  // Check if there are any active sessions
  const hasActiveSessions = () => {
    return Array.from(activeSessions.values()).some(session => session.status === 'running');
  };

  // Get active sessions count
  const getActiveSessionsCount = () => {
    return Array.from(activeSessions.values()).filter(session => session.status === 'running').length;
  };

  const value = {
    activeSessions,
    addSession,
    updateSession,
    removeSession,
    getActiveImportSession,
    hasActiveSessions,
    getActiveSessionsCount
  };

  return (
    <TestingContext.Provider value={value}>
      {children}
    </TestingContext.Provider>
  );
};

export const useTesting = () => {
  const context = useContext(TestingContext);
  if (!context) {
    throw new Error('useTesting must be used within a TestingProvider');
  }
  return context;
};