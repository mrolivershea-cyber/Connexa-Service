import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTesting } from '../contexts/TestingContext';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Activity, Zap, Wifi, Timer, Minus, X } from 'lucide-react';
import axios from 'axios';

const TestingModal = ({ isOpen, onClose, selectedNodeIds = [], selectAllMode = false, totalCount = 0, activeFilters = {}, onTestComplete }) => {
  const { API } = useAuth();
  const { getActiveImportSession, updateSession, removeSession, addSession } = useTesting();
  const [loading, setLoading] = useState(false);
  const [testType, setTestType] = useState('ping_light');
  const [results, setResults] = useState(null);
  const [progress, setProgress] = useState(0);
  const [isMinimized, setIsMinimized] = useState(false);
  const [processedNodes, setProcessedNodes] = useState(0);
  const [totalNodes, setTotalNodes] = useState(0);
  
  // Progress State for new system
  const [progressData, setProgressData] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [useNewSystem, setUseNewSystem] = useState(false);
  const [error, setError] = useState(null);

  React.useEffect(() => {
    if (isOpen) {
      // First, check for active import session with delay to ensure provider is ready
      setTimeout(() => {
        const activeImportSession = getActiveImportSession();
        
        if (activeImportSession) {
          console.log('Found active import session:', activeImportSession);
          // Connect to active import testing session
          setSessionId(activeImportSession.sessionId);
          setLoading(true);
          setProgressData(null);
          setResults(null);
          setTestType(activeImportSession.testType);
          setProcessedNodes(0);
          setTotalNodes(activeImportSession.nodeIds.length);
          setUseNewSystem(true);
          setIsMinimized(false);
          
          toast.success(`Подключено к активному тестированию из импорта (${activeImportSession.nodeIds.length} узлов)`);
          return;
        }
        
        // Check for saved progress state from manual testing
        const savedState = localStorage.getItem('testingProgress');
        
        if (savedState) {
          try {
            const state = JSON.parse(savedState);
            const isRecent = (Date.now() - state.timestamp) < 300000; // 5 minutes
            
            if (isRecent && state.sessionId) {
              console.log('Restoring saved testing session:', state.sessionId, 'loading:', state.loading, 'completed:', state.completed);
              // Restore saved state
              setSessionId(state.sessionId);
              setLoading(state.loading || false);
              setProgressData(state.progressData || null);
              setResults(state.results || null);
              setTestType(state.testType || 'ping');
              setProcessedNodes(state.processedNodes || 0);
              setTotalNodes(state.totalNodes || selectedNodeIds.length);
              setUseNewSystem(true);
              setIsMinimized(false);
              
              if (state.completed) {
                toast.info('Показаны результаты завершенного тестирования');
              } else if (state.loading) {
                toast.info('Восстановлено активное тестирование');
              } else {
                toast.info('Восстановлена сессия тестирования');
              }
              return;
            } else {
              // Clear old saved state only if it's really old
              console.log('Clearing old testing state');
              localStorage.removeItem('testingProgress');
            }
          } catch (error) {
            console.error('Error parsing saved testing state:', error);
            localStorage.removeItem('testingProgress');
          }
        }
        
        // Reset for new testing only if no active sessions found
        console.log('No active sessions found, resetting to default state');
        setTestType('ping_light');
        setResults(null);
        setProgress(0);
        setIsMinimized(false);
        setProcessedNodes(0);
        const calculatedTotal = selectAllMode ? totalCount : selectedNodeIds.length;
        console.log('📊 Setting totalNodes:', {
          selectAllMode,
          totalCount,
          selectedNodeIdsLength: selectedNodeIds.length,
          calculatedTotal
        });
        setTotalNodes(calculatedTotal);
        setProgressData(null);
        setSessionId(null);
        setUseNewSystem(false);
      }, 100);
    }
  }, [isOpen, selectedNodeIds.length, selectAllMode, totalCount, getActiveImportSession]);

  // Auto-persist testing session to survive page refreshes
  React.useEffect(() => {
    if (!sessionId || !loading) return;
    const persist = () => {
      const savedState = {
        sessionId,
        loading,
        progressData: {
          // Only save essential progress data
          processed: progressData?.processed_items || 0,
          total: progressData?.total_items || 0,
          currentOperation: progressData?.current_task || ''
        },
        testType,
        totalNodes,
        timestamp: Date.now()
        // REMOVED: selectedNodeIds, results, processedNodes - too large for localStorage
      };
      
      try {
        // Check localStorage size before saving
        const stateString = JSON.stringify(savedState);
        if (stateString.length > 100000) { // 100KB limit
          console.warn('Testing state too large for localStorage, saving minimal data');
          const minimalState = {
            sessionId,
            loading,
            totalNodes,
            timestamp: Date.now()
          };
          localStorage.setItem('testingProgress', JSON.stringify(minimalState));
        } else {
          localStorage.setItem('testingProgress', stateString);
        }
      } catch (e) {
        console.warn('Failed to save testing progress to localStorage:', e.message);
        // Continue without localStorage
      }
    };

    // Persist immediately and on interval
    persist();
    const iv = setInterval(persist, 1500);

    // Persist on page unload
    const handleBeforeUnload = () => persist();
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      clearInterval(iv);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [sessionId, loading, progressData, results, testType, processedNodes, totalNodes, selectedNodeIds]);

  // Progress tracking effect (same as ImportModal)
  React.useEffect(() => {
    let eventSource = null;
    
    if (sessionId && loading) {
      // Обеспечиваем мгновенную видимость процесса до прихода первого SSE
      setProgressData(prev => prev || { status: 'running', processed_items: 0, total_items: totalNodes || selectedNodeIds.length, current_task: `Запущено тестирование ${selectedNodeIds.length} узлов...`, results: [] });
      eventSource = new EventSource(`${API}/progress/${sessionId}`);
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setProgressData(data);
          setProcessedNodes(data.processed_items || 0);
          setTotalNodes(data.total_items || selectedNodeIds.length);
          setProgress(data.progress_percent || 0);
          
          if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
            eventSource.close();
            setLoading(false);
            
            if (data.status === 'completed') {
              // Update session status in global state
              updateSession(sessionId, { status: 'completed' });
              
              // Convert progress results to expected format
              const testResults = data.results?.map(result => ({
                node_id: result.node_id,
                ip: result.ip,
                success: result.success,
                status: result.status,
                ping_result: result.success ? {
                  success: true,
                  avg_time: '< 100ms',
                  packet_loss: '0%'
                } : {
                  success: false,
                  message: 'Connection failed'
                }
              })) || [];
              
              setResults(testResults);
              toast.success(`Тестирование завершено: ${testResults.filter(r => r.success).length} успешно`);
              
              // Keep completed results visible for longer before cleanup
              const completedState = {
                sessionId: null,
                testRunning: false,
                testType,
                totalNodes,
                timestamp: Date.now(),
                completed: true
                // REMOVED large objects to prevent localStorage overflow
              };
              try {
                localStorage.setItem('testingProgress', JSON.stringify(completedState));
              } catch (e) {
                console.warn('Failed to save completed state to localStorage:', e.message);
              }
              
              // Remove session after longer delay to show completion
              setTimeout(() => {
                removeSession(sessionId);
                // Clean up after session removal, not immediately
                setTimeout(() => {
                  localStorage.removeItem('testingProgress');
                }, 30000); // Keep for 30 seconds after session removal
              }, 10000);
              
              if (onTestComplete) {
                onTestComplete();
              }
              
              // Проверить наличие failed узлов для retry
              if (testType === 'ping_light') {
                axios.get(`${API}/stats`, {
                  headers: { Authorization: `Bearer ${token}` }
                }).then(statsResponse => {
                  const failedCount = statsResponse.data.ping_failed || 0;
                  if (failedCount > 0) {
                    setFailedNodeCount(failedCount);
                    setShowRetryPrompt(true);
                  }
                }).catch(err => {
                  console.error('Failed to get stats for retry:', err);
                });
              }
            } else if (data.status === 'failed') {
              updateSession(sessionId, { status: 'failed' });
              setTimeout(() => {
                removeSession(sessionId);
                localStorage.removeItem('testingProgress');
              }, 5000);
              toast.error('Ошибка при тестировании');
            }
          }
        } catch (error) {
          console.error('Error parsing progress data:', error);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
        setLoading(false);
      };
    }
    
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [sessionId, loading, API, selectedNodeIds.length, onTestComplete, totalNodes]);

  const [pingConcurrency, setPingConcurrency] = useState(15);   // АГРЕССИВНО увеличено для скорости
  const [speedConcurrency, setSpeedConcurrency] = useState(8);  // АГРЕССИВНО увеличено для скорости
  const [pingTimeouts, setPingTimeouts] = useState('0.5');     // СВЕРХ-БЫСТРЫЙ единственный таймаут
  const [speedSampleKB, setSpeedSampleKB] = useState(16); // Оптимизировано: 16KB быстрее чем 32KB      // МИНИМИЗИРОВАНО для максимальной скорости
  const [speedTimeout, setSpeedTimeout] = useState(2);         // ЭКСТРЕМАЛЬНО быстро
  
  // Retry Failed state
  const [showRetryPrompt, setShowRetryPrompt] = useState(false);
  const [failedNodeCount, setFailedNodeCount] = useState(0);

  // Автоматическое изменение параметров при выборе типа теста
  React.useEffect(() => {
    if (testType === 'ping_light') {
      // PING LIGHT оптимальные параметры
      setPingConcurrency(100);      // Увеличенный параллелизм для быстрой проверки портов
      setSpeedConcurrency(0);       // Не используется в PING LIGHT
      setPingTimeouts('2');         // 2s timeout (Fast preset) - ~76% success rate
      setSpeedSampleKB(0);          // Не используется при проверке порта
      setSpeedTimeout(0);           // Не используется при проверке порта
      console.log('🚀 PING LIGHT режим: параметры оптимизированы для быстрой проверки портов');
    } else if (testType === 'ping') {
      // PING OK оптимальные параметры
      setPingConcurrency(15);       // Средний параллелизм для PPTP авторизации
      setSpeedConcurrency(0);       // Не используется в PING OK
      setPingTimeouts('8');         // 8s timeout для PPTP handshake
      setSpeedSampleKB(0);          // Не используется
      setSpeedTimeout(0);           // Не используется
      console.log('🔄 PING OK режим: параметры установлены для PPTP авторизации');
    } else if (testType === 'speed') {
      // SPEED OK оптимальные параметры
      setPingConcurrency(15);       // Для автоматического PING OK (если нужно)
      setSpeedConcurrency(8);       // Параллелизм для speed тестов
      setPingTimeouts('8');         // Для автоматического PING OK
      setSpeedSampleKB(128);        // Реальный размер пробы (соответствует backend)
      setSpeedTimeout(60);          // Реальный timeout (соответствует backend)
      console.log('🔄 SPEED OK режим: параметры установлены для тестов скорости');
    }
  }, [testType]);

  // Retry Failed функция
  const retryFailed = async () => {
    setShowRetryPrompt(false);
    
    try {
      const token = localStorage.getItem('token');
      
      // Получить все failed узлы
      const failedResponse = await axios.get(`${API}/nodes?status=ping_failed&limit=1000`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const failedIds = failedResponse.data.nodes.map(n => n.id);
      
      if (failedIds.length === 0) {
        alert('Нет failed узлов для retry');
        return;
      }
      
      // Установить увеличенный timeout (5s)
      setPingTimeouts('5');
      
      // Запустить тест с failed узлами
      console.log(`🔄 Retry ${failedIds.length} failed nodes with 5s timeout`);
      
      const requestData = {
        node_ids: failedIds,
        ping_concurrency: 100,
        ping_timeouts: [5.0]
      };
      
      const response = await axios.post(`${API}/manual/ping-light-test-batch-progress`, requestData, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 180000
      });
      
      setSessionId(response.data.session_id);
      setLoading(true);
      setError(null);
      
    } catch (err) {
      console.error('Retry failed:', err);
      setError(err.response?.data?.detail || err.message || 'Retry failed');
    }
  };

  const handleTest = async () => {
    // DEBUG: проверяем что приходит
    console.log('🔍 handleTest called');
    console.log('selectedNodeIds:', selectedNodeIds);
    console.log('selectedNodeIds.length:', selectedNodeIds.length);
    console.log('selectAllMode:', selectAllMode);
    console.log('totalCount (prop):', totalCount);
    console.log('totalNodes (state):', totalNodes);
    console.log('testType:', testType);
    
    if (!selectAllMode && selectedNodeIds.length === 0) {
      console.log('❌ Stopping: no nodes selected');
      toast.error('Выберите узлы для тестирования');
      return;
    }
    
    if (selectAllMode) {
      toast.info('🚀 Запуск тестирования всех узлов в базе...');
    }
    
    console.log('✅ Validation passed, starting test...');

    setLoading(true);
    setProgress(0);
    setProcessedNodes(0);
    setTotalNodes(selectAllMode ? totalCount : selectedNodeIds.length);
    setResults(null);
    setProgressData(null);
    setSessionId(null);
    
    // ALWAYS use progress-enabled endpoints for ANY batch size
    setUseNewSystem(true);
    
    try {
      let endpoint;
      
      // Use appropriate endpoints for each test type
      if (testType === 'ping_light') {
        endpoint = 'manual/ping-light-test-batch-progress';  // Fast TCP check without auth with progress
      } else if (testType === 'ping') {
        endpoint = 'manual/ping-test-batch-progress';  // Full ping with auth
      } else if (testType === 'speed') {
        endpoint = 'manual/speed-test-batch-progress';
      } else if (testType === 'geo') {
        endpoint = 'manual/geo-test-batch';  // GEO check
      } else if (testType === 'fraud') {
        endpoint = 'manual/fraud-test-batch';  // Fraud check
      } else if (testType === 'geo_fraud') {
        endpoint = 'manual/geo-fraud-test-batch';  // Combined GEO + Fraud
      }
      
      // No more progress simulation - SSE will provide real progress
      
      const nodeCount = selectAllMode ? totalCount : selectedNodeIds.length;
      console.log(`Starting ${testType} test for ${nodeCount} nodes using ${endpoint}`);
      
      // Для selectAllMode НЕ передаём node_ids - backend сам получит узлы по фильтрам
      const requestData = {
        test_type: testType,
        ping_concurrency: pingConcurrency,
        speed_concurrency: speedConcurrency,
        ping_timeouts: pingTimeouts.split(',').map(v => parseFloat(v.trim())).filter(v => !isNaN(v)),
        speed_sample_kb: Number(speedSampleKB) || 512,
        speed_timeout: Number(speedTimeout) || 15
      };
      
      // Только для режима выбора отдельных узлов передаём node_ids
      if (!selectAllMode) {
        requestData.node_ids = selectedNodeIds;
      } else {
        // Передаём фильтры для Select All режима
        requestData.filters = activeFilters;
      }
      
      const response = await axios.post(`${API}/${endpoint}`, requestData, {
        timeout: 180000 // 3 minutes for single tests
      });
      
      if (response.data.session_id) {
        // Track progress via SSE
        setSessionId(response.data.session_id);
        
        // Register session in global state
        addSession(response.data.session_id, 'manual', selectedNodeIds, testType);
        
        // Persist initial state to survive refreshes
        const savedState = {
          sessionId: response.data.session_id,
          loading: true,
          testType,
          totalNodes: selectedNodeIds.length,
          timestamp: Date.now()
          // REMOVED large arrays to prevent localStorage overflow
        };
        try {
          localStorage.setItem('testingProgress', JSON.stringify(savedState));
        } catch (e) {
          console.warn('Failed to save test start state to localStorage:', e.message);
        }
        toast.info(response.data.message || 'Тестирование начато');
        // Don't set loading to false yet, SSE will handle completion
      } else {
        // Fallback: direct response (shouldn't happen with progress endpoints)
        setProgress(100);
        localStorage.removeItem('testingProgress');
        setResults(response.data.results);
        setProcessedNodes(response.data.results?.length || 0);
        
        const successCount = response.data.results?.filter(r => r.success).length || 0;
        const failCount = (response.data.results?.length || 0) - successCount;
        
        if (successCount > 0) {
          toast.success(`Протестировано ${successCount} узлов`);
        }
        if (failCount > 0) {
          toast.warning(`Ошибки с ${failCount} узлами`);
        }

        if (onTestComplete) {
          onTestComplete();
        }
        
        setLoading(false);
      }
      
    } catch (error) {
      console.error('Testing error:', error);
      toast.error('Ошибка тестирования: ' + (error.response?.data?.detail || error.message));
    } finally {
      // Note: SSE handles completion, no need to set loading=false here
    }
  };

  const handleMinimize = () => {
    // Save current state to localStorage for restoration
    if (sessionId || loading) {
      const savedState = {
        sessionId,
        testRunning: true,
        testType,
        totalNodes,
        timestamp: Date.now()
        // REMOVED large objects to prevent localStorage overflow
      };
      try {
        localStorage.setItem('testingProgress', JSON.stringify(savedState));
        toast.info('Тестирование свернуто. Откройте Testing для просмотра прогресса.');
      } catch (e) {
        console.warn('Failed to save minimized state to localStorage:', e.message);
        toast.info('Тестирование продолжается в фоне.');
      }
    }
    
    // Close the modal but keep the process running
    onClose();
  };

  const getTestTypeDescription = () => {
    switch (testType) {
      case 'ping':
        return 'Проверка доступности узлов (ICMP ping)';
      case 'speed':
        return 'Тестирование скорости интернет соединения';
      default:
        return '';
    }
  };

  const renderTestResult = (result) => {
    if (!result.success) {
      return (
        <div className="p-3 bg-red-100 text-red-800 rounded">
          <div className="font-medium">Node {result.node_id} - {result.ip || 'N/A'}</div>
          <div className="text-sm">{result.message}</div>
        </div>
      );
    }

    // Handle manual ping test results (new format)
    if (result.ping_result) {
      const pingResult = result.ping_result;
      const isSuccess = pingResult.success;
      
      return (
        <div className={`p-3 rounded ${
          isSuccess ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          <div className="flex justify-between items-start">
            <div>
              <div className="font-medium">Node {result.node_id} - {result.ip}</div>
              <div className="text-sm">
                {isSuccess ? (
                  <span>✅ PPTP Порт Доступен • {pingResult.avg_time}ms • Потери: {pingResult.packet_loss}%</span>
                ) : (
                  <span>❌ PPTP Недоступен • {pingResult.message}</span>
                )}
              </div>
              <div className="text-xs text-gray-600">
                Статус: {result.original_status} → {result.status}
              </div>
            </div>
            <Badge variant={isSuccess ? 'default' : 'destructive'}>
              {result.status}
            </Badge>
          </div>
        </div>
      );
    }

    // Handle legacy ping test results (old format)
    if (result.ping) {
      const ping = result.ping;
      return (
        <div className={`p-3 rounded ${
          ping.reachable ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          <div className="flex justify-between items-start">
            <div>
              <div className="font-medium">Node {result.node_id} - {result.ip}</div>
              <div className="text-sm">
                {ping.reachable ? (
                  <span>✅ Доступен • Ping: {ping.avg_latency}ms • Потери: {ping.packet_loss}%</span>
                ) : (
                  <span>❌ Недоступен</span>
                )}
              </div>
            </div>
            <Badge variant={ping.reachable ? 'default' : 'destructive'}>
              {ping.reachable ? 'Online' : 'Offline'}
            </Badge>
          </div>
        </div>
      );
    }

    // Handle manual speed test results (new format)
    if (result.speed_result) {
      const speedResult = result.speed_result;
      const isSuccess = speedResult.success;
      
      return (
        <div className={`p-3 rounded ${
          isSuccess ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
        }`}>
          <div className="flex justify-between items-start">
            <div>
              <div className="font-medium">Node {result.node_id} - {result.ip}</div>
              {isSuccess ? (
                <div className="text-sm">
                  ⬇️ {speedResult.download} Mbps • ⬆️ {speedResult.upload} Mbps • Ping: {speedResult.ping}ms
                </div>
              ) : (
                <div className="text-sm">❌ Ошибка: {speedResult.message}</div>
              )}
              <div className="text-xs text-gray-600">
                Статус: {result.status} • Скорость: {result.speed || 'N/A'}
              </div>
            </div>
            <Badge variant={isSuccess ? 'default' : 'secondary'}>
              {result.status}
            </Badge>
          </div>
        </div>
      );
    }

    // Handle legacy speed test results (old format)
    if (result.speed) {
      const speed = result.speed;
      return (
        <div className={`p-3 rounded ${
          speed.success ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
        }`}>
          <div className="flex justify-between items-start">
            <div>
              <div className="font-medium">Node {result.node_id} - {result.ip}</div>
              {speed.success ? (
                <div className="text-sm">
                  ⬇️ {speed.download} Mbps • ⬆️ {speed.upload} Mbps • Ping: {speed.ping}ms
                  <br />
                  <span className="text-xs">Сервер: {speed.server}</span>
                </div>
              ) : (
                <div className="text-sm">❌ Ошибка: {speed.error}</div>
              )}
            </div>
          </div>
        </div>
      );
    }

    if (result.test) {
      const test = result.test;
      return (
        <div className={`p-3 rounded ${
          test.overall === 'online' ? 'bg-green-100 text-green-800' :
          test.overall === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          <div className="flex justify-between items-start">
            <div>
              <div className="font-medium">Node {result.node_id} - {result.ip}</div>
              <div className="text-sm space-y-1">
                {test.ping && (
                  <div>
                    Ping: {test.ping.reachable ? `${test.ping.avg_latency}ms` : 'Недоступен'}
                  </div>
                )}
                {test.speed && (
                  <div>
                    {test.speed.success ? (
                      `Скорость: ⬇️${test.speed.download} Mbps ⬆️${test.speed.upload} Mbps`
                    ) : (
                      'Скорость: Ошибка'
                    )}
                  </div>
                )}
              </div>
            </div>
            <Badge variant={test.overall === 'online' ? 'default' : 
                           test.overall === 'degraded' ? 'secondary' : 'destructive'}>
              {test.overall}
            </Badge>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[800px] max-h-[80vh] overflow-y-auto" data-testid="testing-modal">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center">
              <Activity className="h-5 w-5 mr-2" />
              Тестирование Узлов
              {sessionId && progressData && (
                <Badge variant="secondary" className="ml-2">
                  {getActiveImportSession()?.sessionId === sessionId ? 'Из импорта' : 'Ручное'}
                </Badge>
              )}
            </DialogTitle>
            {(loading || progressData) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMinimize}
                className="h-8 w-8 p-0"
                title="Свернуть"
              >
                <Minus className="h-4 w-4" />
              </Button>
            )}
          </div>
          <DialogDescription>
            Проверка доступности и скорости соединения для выбранных узлов.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-2">
          {/* Компактный объединенный блок настроек */}
          <div className="border rounded-lg p-2.5 space-y-2">
            {/* Test Type Selection */}
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Тип Тестирования</label>
              <Select value={testType} onValueChange={setTestType}>
                <SelectTrigger data-testid="test-type-select" className="h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ping_light">
                    <div className="flex items-center">
                      <Zap className="h-4 w-4 mr-2 text-yellow-500" />
                      Ping Test
                    </div>
                  </SelectItem>
                  <SelectItem value="ping">
                    <div className="flex items-center">
                      <Wifi className="h-4 w-4 mr-2" />
                      PING OK (с авторизацией)
                    </div>
                  </SelectItem>
                  <SelectItem value="speed">
                    <div className="flex items-center">
                      <Zap className="h-4 w-4 mr-2" />
                      Speed Test
                    </div>
                  </SelectItem>
                  <SelectItem value="geo">
                    <div className="flex items-center">
                      <svg className="h-4 w-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      GEO Test (Country, State, City, Provider)
                    </div>
                  </SelectItem>
                  <SelectItem value="fraud">
                    <div className="flex items-center">
                      <svg className="h-4 w-4 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      Fraud Test (Fraud Score, Risk Level)
                    </div>
                  </SelectItem>
                  <SelectItem value="geo_fraud">
                    <div className="flex items-center">
                      <svg className="h-4 w-4 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      GEO + Fraud (полная проверка)
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <hr className="border-gray-200" />

            {/* Параметры (компактно) */}
              
              <div className="space-y-3">
                {/* Параллелизм Ping - для всех типов */}
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Параллелизм {testType === 'ping_light' ? '(TCP)' : testType === 'ping' ? '(PPTP)' : '(авто)'}
                  </label>
                  {/* Адаптивные пресеты в зависимости от типа теста */}
                  <div className="flex gap-1 mb-1">
                    {testType === 'ping_light' && (
                      <>
                        <button onClick={() => setPingConcurrency(50)} className={`px-2 py-0.5 text-xs rounded ${pingConcurrency === 50 ? 'bg-green-500 text-white' : 'bg-gray-100'}`}>
                          50
                        </button>
                        <button onClick={() => setPingConcurrency(100)} className={`px-2 py-0.5 text-xs rounded ${pingConcurrency === 100 ? 'bg-green-500 text-white' : 'bg-gray-100'}`}>
                          ⚖️100
                        </button>
                        <button onClick={() => setPingConcurrency(150)} className={`px-2 py-0.5 text-xs rounded ${pingConcurrency === 150 ? 'bg-green-500 text-white' : 'bg-gray-100'}`}>
                          🚀150
                        </button>
                      </>
                    )}
                    {testType === 'ping' && (
                      <>
                        <button onClick={() => setPingConcurrency(10)} className={`px-2 py-0.5 text-xs rounded ${pingConcurrency === 10 ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}>
                          10
                        </button>
                        <button onClick={() => setPingConcurrency(15)} className={`px-2 py-0.5 text-xs rounded ${pingConcurrency === 15 ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}>
                          ⚖️15
                        </button>
                        <button onClick={() => setPingConcurrency(25)} className={`px-2 py-0.5 text-xs rounded ${pingConcurrency === 25 ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}>
                          🚀25
                        </button>
                      </>
                    )}
                    {testType === 'speed' && (
                      <>
                        <button onClick={() => setPingConcurrency(15)} className={`px-2 py-0.5 text-xs rounded ${pingConcurrency === 15 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                          ⚖️15
                        </button>
                        <button onClick={() => setPingConcurrency(25)} className={`px-2 py-0.5 text-xs rounded ${pingConcurrency === 25 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                          🚀25
                        </button>
                      </>
                    )}
                  </div>
                  <input type="number" min={1} max={150} value={pingConcurrency} onChange={e => setPingConcurrency(parseInt(e.target.value) || 15)} className="w-full border rounded px-2 py-1 text-xs h-7" />
                </div>

                {/* Таймауты Ping - только для PING типов */}
                {(testType === 'ping_light' || testType === 'ping') && (
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Timeout
                    </label>
                    {testType === 'ping_light' && (
                      <div className="flex gap-1 mb-1">
                        <button onClick={() => setPingTimeouts('2')} className={`px-2 py-0.5 text-xs rounded ${pingTimeouts === '2' ? 'bg-green-500 text-white' : 'bg-gray-100'}`}>
                          ⚡2s
                        </button>
                        <button onClick={() => setPingTimeouts('3')} className={`px-2 py-0.5 text-xs rounded ${pingTimeouts === '3' ? 'bg-green-500 text-white' : 'bg-gray-100'}`}>
                          ⚖️3s
                        </button>
                        <button onClick={() => setPingTimeouts('5')} className={`px-2 py-0.5 text-xs rounded ${pingTimeouts === '5' ? 'bg-green-500 text-white' : 'bg-gray-100'}`}>
                          🎯5s
                        </button>
                      </div>
                    )}
                    {testType === 'ping' && (
                      <div className="flex gap-1 mb-1">
                        <button onClick={() => setPingTimeouts('5')} className={`px-2 py-0.5 text-xs rounded ${pingTimeouts === '5' ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}>
                          ⚡5s
                        </button>
                        <button onClick={() => setPingTimeouts('8')} className={`px-2 py-0.5 text-xs rounded ${pingTimeouts === '8' ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}>
                          ⚖️8s
                        </button>
                        <button onClick={() => setPingTimeouts('12')} className={`px-2 py-0.5 text-xs rounded ${pingTimeouts === '12' ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}>
                          🎯12s
                        </button>
                      </div>
                    )}
                    <input type="text" value={pingTimeouts} onChange={e => setPingTimeouts(e.target.value)} className="w-full border rounded px-2 py-1 text-xs h-7" />
                  </div>
                )}

                {/* Speed Concurrency - только для SPEED */}
                {testType === 'speed' && (
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Параллелизм Speed</label>
                    <div className="flex gap-1 mb-1">
                      <button onClick={() => setSpeedConcurrency(5)} className={`px-2 py-0.5 text-xs rounded ${speedConcurrency === 5 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                        5
                      </button>
                      <button onClick={() => setSpeedConcurrency(8)} className={`px-2 py-0.5 text-xs rounded ${speedConcurrency === 8 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                        ⚖️8
                      </button>
                      <button onClick={() => setSpeedConcurrency(10)} className={`px-2 py-0.5 text-xs rounded ${speedConcurrency === 10 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                        🚀10
                      </button>
                    </div>
                    <input type="number" min={1} max={20} value={speedConcurrency} onChange={e => setSpeedConcurrency(parseInt(e.target.value) || 8)} className="w-full border rounded px-2 py-1 text-xs h-7" />
                  </div>
                )}

                {/* Расширенные настройки Speed - только для SPEED */}
                {testType === 'speed' && (
                  <details className="mt-1">
                    <summary className="cursor-pointer text-xs text-blue-600 hover:text-blue-800 select-none py-1">
                      ▶ Расширенные
                    </summary>
                    <div className="mt-2 space-y-2 pl-2 border-l border-blue-200">
                      {/* Speed Sample Size */}
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Объём пробы (KB)</label>
                        <div className="flex gap-1 mb-1">
                          <button onClick={() => setSpeedSampleKB(64)} className={`px-2 py-0.5 text-xs rounded ${speedSampleKB === 64 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                            ⚡64
                          </button>
                          <button onClick={() => setSpeedSampleKB(128)} className={`px-2 py-0.5 text-xs rounded ${speedSampleKB === 128 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                            ⚖️128
                          </button>
                          <button onClick={() => setSpeedSampleKB(256)} className={`px-2 py-0.5 text-xs rounded ${speedSampleKB === 256 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                            🎯256
                          </button>
                        </div>
                        <input type="number" min={8} max={512} value={speedSampleKB} onChange={e => setSpeedSampleKB(parseInt(e.target.value) || 128)} className="w-full border rounded px-2 py-1 text-xs h-7" />
                      </div>

                      {/* Speed Timeout */}
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Timeout (сек)</label>
                        <div className="flex gap-1 mb-1">
                          <button onClick={() => setSpeedTimeout(30)} className={`px-2 py-0.5 text-xs rounded ${speedTimeout === 30 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                            ⚡30s
                          </button>
                          <button onClick={() => setSpeedTimeout(60)} className={`px-2 py-0.5 text-xs rounded ${speedTimeout === 60 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                            ⚖️60s
                          </button>
                          <button onClick={() => setSpeedTimeout(90)} className={`px-2 py-0.5 text-xs rounded ${speedTimeout === 90 ? 'bg-purple-500 text-white' : 'bg-gray-100'}`}>
                            🎯90s
                          </button>
                        </div>
                        <input type="number" min={10} max={120} value={speedTimeout} onChange={e => setSpeedTimeout(parseInt(e.target.value) || 60)} className="w-full border rounded px-2 py-1 text-xs h-7" />
                      </div>
                    </div>
                  </details>
                )}
              </div>
              
              {/* Компактная подсказка */}
              <div className="text-xs text-gray-500 mt-2 p-2 bg-blue-50 rounded">
                💡 <strong>Совет:</strong> Используйте ⚖️ Balanced для оптимального баланса
              </div>
            </div>

          {/* Node Selection - компактная строка вместо Card */}
          <div className="text-sm px-3 py-2 bg-gray-50 rounded border border-gray-200">
            {(selectAllMode || selectedNodeIds.length > 0) ? (
              <span className="text-gray-700">
                📊 Выбрано: <strong>{selectAllMode ? `ВСЕ (${totalCount})` : selectedNodeIds.length}</strong> узлов
              </span>
            ) : (
              <span className="text-gray-500">Выберите узлы в таблице или используйте Select All</span>
            )}
            {!selectAllMode && (!selectedNodeIds || selectedNodeIds.length === 0) && (
              <span className="text-red-600 ml-2">⚠️ Нет выбранных узлов</span>
            )}
          </div>

          {/* Progress */}
          {loading && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center justify-between">
                  <span>Прогресс тестирования</span>
                  <span className="text-sm font-normal">
                    {processedNodes}/{totalNodes}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>
                      {progressData?.current_task || `Выполняется ${
                        testType === 'ping_light' ? 'PING LIGHT (быстрая проверка TCP порта)' :
                        testType === 'ping' ? 'PING OK (с авторизацией)' : 
                        testType === 'speed' ? 'тест скорости' : 
                        'комбинированное'
                      } тестирование...`}
                    </span>
                    <span>{Math.round((processedNodes / totalNodes) * 100) || progress}%</span>
                  </div>
                  <Progress value={processedNodes > 0 ? (processedNodes / totalNodes) * 100 : progress} className="w-full" />
                  <div className="text-xs text-gray-600">
                    Тестируется {selectedNodeIds.length} узлов
                    {useNewSystem && ' (батч-система)'}
                  </div>
                  
                  {/* Show recent results for new system */}
                  {progressData?.results && progressData.results.length > 0 && (
                    <div className="mt-2 max-h-20 overflow-y-auto space-y-1">
                      {progressData.results.slice(-3).map((result, index) => (
                        <div key={index} className="text-xs text-gray-600 flex items-center">
                          <span className={`mr-2 ${result.success ? 'text-green-600' : 'text-red-600'}`}>
                            {result.success ? '✅' : '❌'}
                          </span>
                          {result.ip} - {result.status}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Results */}
          {results && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center">
                  <Timer className="h-4 w-4 mr-2" />
                  Результаты Тестирования
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {results.map((result, index) => (
                    <div key={index}>
                      {renderTestResult(result)}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Retry Failed Prompt */}
        {showRetryPrompt && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 text-yellow-600">
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-yellow-800 mb-1">
                  Обнаружено {failedNodeCount} неудачных узлов
                </h3>
                <p className="text-sm text-yellow-700 mb-3">
                  Повторить тест с увеличенным timeout (5s) для восстановления медленных узлов?
                  Ожидается восстановление ~4-10% узлов.
                </p>
                <div className="flex gap-2">
                  <Button size="sm" onClick={retryFailed} className="bg-yellow-600 hover:bg-yellow-700">
                    🔄 Retry Failed (5s timeout)
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => setShowRetryPrompt(false)}>
                    Пропустить
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Закрыть
          </Button>
          <Button 
            onClick={handleTest}
            disabled={loading || (!selectAllMode && selectedNodeIds.length === 0)}
            data-testid="start-testing-btn"
          >
            <Activity className="h-4 w-4 mr-2" />
            {loading ? 'Тестирование...' : 'Начать Тест'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default TestingModal;
