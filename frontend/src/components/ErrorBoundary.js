import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console
    console.error('🚨 React Error Boundary caught an error:', error, errorInfo);
    
    // Store error details
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
    
    // Prevent page reload by catching the error
    // You could also send this to an error reporting service
  }

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return (
        <div style={{ padding: '20px', backgroundColor: '#fee', border: '2px solid red', margin: '20px' }}>
          <h2>⚠️ Что-то пошло не так</h2>
          <p>Приложение обнаружило ошибку. Страница НЕ будет перезагружена.</p>
          <details style={{ whiteSpace: 'pre-wrap', marginTop: '10px' }}>
            <summary>Подробности ошибки (для разработчика)</summary>
            <p><strong>Error:</strong> {this.state.error && this.state.error.toString()}</p>
            <p><strong>Stack:</strong></p>
            <pre>{this.state.errorInfo && this.state.errorInfo.componentStack}</pre>
          </details>
          <button 
            onClick={() => {
              this.setState({ hasError: false, error: null, errorInfo: null });
              window.location.href = '/';
            }}
            style={{ marginTop: '20px', padding: '10px 20px', cursor: 'pointer' }}
          >
            Перезагрузить приложение
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
