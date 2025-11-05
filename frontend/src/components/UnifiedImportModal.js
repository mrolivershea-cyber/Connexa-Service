import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Upload, Activity } from 'lucide-react';
import axios from 'axios';

const UnifiedImportModal = ({ isOpen, onClose, onComplete }) => {
  const { API } = useAuth();

  // Import form state - simplified (no testing options)
  const [importData, setImportData] = useState('');
  const [protocol, setProtocol] = useState('pptp');
  const [previewResult, setPreviewResult] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [isLargeFile, setIsLargeFile] = useState(false);
  const [progress, setProgress] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [isImportActive, setIsImportActive] = useState(false);
  const [regularImportController, setRegularImportController] = useState(null);
  const [regularImportProgress, setRegularImportProgress] = useState(0);
  const [regularImportStats, setRegularImportStats] = useState({ added: 0, skipped: 0, errors: 0 });
  
  // Simulate progress for regular import (non-blocking)
  useEffect(() => {
    if (submitting && !sessionId) {
      let progressValue = 0;
      const interval = setInterval(() => {
        progressValue += Math.random() * 5 + 2;
        if (progressValue >= 90) {
          progressValue = 90;
          clearInterval(interval); // STOP at 90% to allow backend to complete
          return;
        }
        setRegularImportProgress(Math.round(progressValue));
      }, 150);
      
      return () => clearInterval(interval);
    } else {
      // Reset progress when not submitting
      setRegularImportProgress(0);
    }
  }, [submitting, sessionId]);

  useEffect(() => {
    if (isOpen) {
      // Check for active chunked import session
      const activeImport = localStorage.getItem('activeImportSession');
      if (activeImport) {
        try {
          const importData = JSON.parse(activeImport);
          if (importData.sessionId && importData.timestamp > Date.now() - 30 * 60 * 1000) { // 30 minutes
            console.log('Resuming active chunked import session:', importData.sessionId);
            setSessionId(importData.sessionId);
            setIsImportActive(true);
            setSubmitting(false);
            startProgressTracking(importData.sessionId);
            toast.info('📂 Обнаружена активная сессия chunked импорта. Продолжаем...');
            return; // Don't reset states
          } else {
            localStorage.removeItem('activeImportSession');
          }
        } catch (e) {
          localStorage.removeItem('activeImportSession');
        }
      }
      
      // Check for active regular import
      const activeRegular = localStorage.getItem('activeRegularImport');
      if (activeRegular) {
        try {
          const regularData = JSON.parse(activeRegular);
          if (regularData.timestamp > Date.now() - 5 * 60 * 1000) { // 5 minutes
            console.log('Resuming active regular import');
            setSubmitting(true);
            setRegularImportProgress(regularData.progress || 50);
            toast.info('📂 Обнаружен активный импорт. Продолжаем...');
            return; // Don't reset states
          } else {
            localStorage.removeItem('activeRegularImport');
          }
        } catch (e) {
          localStorage.removeItem('activeRegularImport');
        }
      }
      
      // НОВОЕ: Check for last completed import report
      const lastReport = localStorage.getItem('lastImportReport');
      if (lastReport) {
        try {
          const reportData = JSON.parse(lastReport);
          // Show report if it's within 30 minutes
          if (reportData.timestamp > Date.now() - 30 * 60 * 1000) {
            console.log('Restoring last import report');
            setPreviewResult(reportData.report);
            setShowPreview(true);
            toast.info('📊 Показываю результаты последнего импорта');
            return; // Don't reset states
          } else {
            localStorage.removeItem('lastImportReport');
          }
        } catch (e) {
          localStorage.removeItem('lastImportReport');
        }
      }
      
      // Reset form ONLY if no active imports or reports
      setImportData('');
      setProtocol('pptp');
      setPreviewResult(null);
      setShowPreview(false);
      setSubmitting(false);
      setIsLargeFile(false);
      setProgress(null);
      setSessionId(null);
      setIsImportActive(false);
      setRegularImportController(null);
      setRegularImportProgress(0);
      setRegularImportStats({ added: 0, skipped: 0, errors: 0 });
    }
  }, [isOpen]);

  const addSampleText = () => {
    const sampleTexts = {
      pptp: `Format 1 - Key-value pairs:\nIp: 144.229.29.35\nLogin: admin\nPass: admin\nState: California\nCity: Los Angeles\nZip: 90035\n---------------------\nFormat 2 - Single line with spaces (IP Pass Login State):\n76.178.64.46 admin admin CA\n96.234.52.227 admin admin NJ\n---------------------\nFormat 3 - Dash/pipe format:\n68.227.241.4 - admin:admin - Arizona/Phoenix 85001 | 2025-09-03 16:05:25\n96.42.187.97 - 1:1 - Michigan/Lapeer 48446 | 2025-09-03 09:50:22\n---------------------\nFormat 4 - Colon separated:\n70.171.218.52:admin:admin:US:Arizona:85001\n---------------------\nFormat 5 - Multi-line with Location:\nIP: 24.227.222.13\nCredentials: admin:admin\nLocation: Texas (Austin)\nZIP: 78701\n---------------------\nFormat 6 - With PPTP header (first 2 lines ignored):\n> PPTP_SVOIM_VPN:\n🚨 PPTP Connection\nIP: 24.227.222.13\nCredentials: admin:admin\nLocation: Texas (Austin)\nZIP: 78701\n---------------------\nFormat 7 - Simple IP:Login:Pass:\n144.229.29.35:admin:password123\n76.178.64.46:user:pass456\n96.234.52.227:root:secret789`,
      ssh: `192.168.1.100:root:password123:US:New York:10001\n10.0.0.50 secret456 admin CA`,
      socks: `proxy1.example.com:1080:user:pass:US:California:90210\nproxy2.example.com:1080:user2:pass2:GB:London:`,
      server: `server1.example.com admin password US\nserver2.example.com root secret CA`,
      ovpn: `vpn1.example.com:1194:client1:pass123:US:Florida:33101\nvpn2.example.com:443:client2:pass456:GB:London:`
    };
    setImportData(sampleTexts[protocol] || sampleTexts.pptp);
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Check file size
    const fileSizeKB = file.size / 1024;
    const isLarge = fileSizeKB > 500; // 500KB threshold
    
    setIsLargeFile(isLarge);
    
    const reader = new FileReader();
    reader.onload = (e) => {
      setImportData(e.target.result);
      if (isLarge) {
        toast.warning(`📦 Большой файл (${fileSizeKB.toFixed(1)}KB) - будет использована потоковая обработка`);
      } else {
        toast.success('Файл загружен');
      }
    };
    reader.onerror = () => {
      toast.error('Не удалось прочитать файл');
    };
    reader.readAsText(file);
  };

  const handleImport = async () => {
    if (!importData.trim()) {
      toast.error('Пожалуйста, введите или загрузите данные для импорта');
      return;
    }

    const dataSize = new Blob([importData]).size;
    const isLarge = dataSize > 500 * 1024; // 500KB

    console.log(`Import file size: ${(dataSize/1024).toFixed(1)}KB, isLarge: ${isLarge}`);
    setSubmitting(true);
    
    if (isLarge) {
      // Large file - use chunked processing immediately
      try {
        console.log('Using chunked processing for large file');
        toast.info(`📂 Обнаружен большой файл (${(dataSize/1024).toFixed(1)}KB). Используем безопасную обработку по частям...`);
        
        // Use chunked endpoint for large files
        const response = await axios.post(`${API}/nodes/import-chunked`, {
          data: importData,
          protocol,
          testing_mode: 'no_test'
        });

        const { session_id, message } = response.data || {};

        if (session_id) {
          console.log('Chunked processing started, session_id:', session_id);
          setSessionId(session_id);
          setIsImportActive(true);
          
          // Save session to localStorage for recovery
          localStorage.setItem('activeImportSession', JSON.stringify({
            sessionId: session_id,
            timestamp: Date.now()
          }));
          
          toast.success('🚀 Запущена chunked обработка большого файла...');
          startProgressTracking(session_id);
          return;
        } else {
          console.error('No session_id received:', response.data);
          throw new Error(message || 'Не удалось запустить chunked processing');
        }
      } catch (error) {
        console.error('Chunked import error:', error);
        toast.error('❌ Ошибка chunked обработки: ' + (error.response?.data?.message || error.message));
        setSubmitting(false);
        return;
      }
    }

    // Small file - use regular processing
    try {
      const controller = new AbortController();
      setRegularImportController(controller);
      setRegularImportProgress(0);
      
      const response = await axios.post(`${API}/nodes/import`, {
        data: importData,
        protocol,
        testing_mode: 'no_test'
      }, {
        signal: controller.signal
      });

      const { success, report, message } = response.data || {};

      if (!success) {
        toast.error(message || 'Ошибка импорта');
        setSubmitting(false);
        setRegularImportProgress(0);
        return;
      }

      // Complete progress and update stats
      setRegularImportProgress(100);
      setRegularImportStats({
        added: report?.added || 0,
        skipped: report?.skipped_duplicates || 0,
        errors: report?.format_errors || 0
      });

      // Show results
      setPreviewResult(report || null);
      setShowPreview(true);

      // Save report to localStorage for recovery
      if (report) {
        localStorage.setItem('lastImportReport', JSON.stringify({
          report: report,
          timestamp: Date.now()
        }));
      }

      toast.success(`✅ Импорт завершён: ${report?.added || 0} добавлено, ${report?.skipped_duplicates || 0} дубликатов`);
      toast.info('📊 Для тестирования используйте кнопку "Testing" в админ-панели');

      // Вызываем onComplete с задержкой, чтобы дать React время обновить UI
      if (onComplete) {
        try {
          setTimeout(() => {
            onComplete(report);
          }, 100);
        } catch (error) {
          console.error('Error in onComplete callback:', error);
        }
      }
      
    } catch (error) {
      if (error.name === 'AbortError' || error.name === 'CanceledError') {
        toast.info('⏹️ Импорт отменён пользователем');
        setRegularImportProgress(0);
        return;
      }
      
      console.error('Error importing:', error);
      const errorMsg = error.response?.data?.message || 'Не удалось импортировать данные';
      toast.error(errorMsg);
      setRegularImportProgress(0);
    } finally {
      setSubmitting(false);
      setRegularImportController(null);
    }
  };

  const cancelImport = async () => {
    if (!sessionId) return;
    
    try {
      await axios.delete(`${API}/import/cancel/${sessionId}`);
      toast.info('⏹️ Импорт отменён');
      setSubmitting(false);
      setIsImportActive(false);
      setProgress(null);
      setSessionId(null);
      localStorage.removeItem('activeImportSession');
    } catch (error) {
      console.error('Cancel error:', error);
      toast.error('Не удалось отменить импорт');
    }
  };

  const startProgressTracking = (sessionId) => {
    console.log('Starting progress tracking for session:', sessionId);
    let progressInterval;
    
    const trackProgress = async () => {
      try {
        const response = await axios.get(`${API}/import/progress/${sessionId}`);
        const progressData = response.data;
        
        console.log('Progress update:', progressData);
        setProgress(progressData);
        
        if (progressData.status === 'completed' || progressData.status === 'cancelled') {
          if (progressInterval) {
            clearInterval(progressInterval);
          }
          
          setSubmitting(false);
          setIsImportActive(false);
          setSessionId(null);
          localStorage.removeItem('activeImportSession');
          
          if (progressData.status === 'completed') {
            const report = {
              added: progressData.added,
              skipped_duplicates: progressData.skipped,
              replaced_old: progressData.replaced,
              format_errors: progressData.errors
            };
            
            setPreviewResult(report);
            setShowPreview(true);
            
            // Save report to localStorage for recovery
            localStorage.setItem('lastImportReport', JSON.stringify({
              report: report,
              timestamp: Date.now()
            }));
            
            toast.success(`✅ Импорт большого файла завершён: ${progressData.added} добавлено, ${progressData.skipped} дубликатов`);
          toast.info('📊 Для тестирования используйте кнопку "Testing" в админ-панели');
          
          // Вызываем onComplete только после того как UI обновился
          if (onComplete) {
            try {
              // Используем setTimeout чтобы дать React время обновить UI
              setTimeout(() => {
                onComplete({
                  added: progressData.added,
                  skipped_duplicates: progressData.skipped,
                  replaced_old: progressData.replaced
                });
              }, 100);
            } catch (error) {
              console.error('Error in onComplete callback:', error);
            }
          }
          } else if (progressData.status === 'cancelled') {
            toast.info('⏹️ Импорт отменён пользователем');
          }
          return;
        }
        
        if (progressData.status === 'error') {
          if (progressInterval) {
            clearInterval(progressInterval);
          }
          setSubmitting(false);
          setIsImportActive(false);
          setSessionId(null);
          localStorage.removeItem('activeImportSession');
          toast.error('❌ Ошибка импорта: ' + (progressData.message || 'Неизвестная ошибка'));
          return;
        }
      } catch (error) {
        console.error('Progress tracking error:', error);
        if (progressInterval) {
          clearInterval(progressInterval);
        }
        setSubmitting(false);
        setIsImportActive(false);
        setSessionId(null);
        localStorage.removeItem('activeImportSession');
        toast.error('❌ Ошибка отслеживания прогресса');
      }
    };
    
    // Initial call
    trackProgress();
    
    // Set up interval for regular updates
    progressInterval = setInterval(trackProgress, 2000); // Update every 2 seconds
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto" data-testid="unified-import-modal">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center">
              <Activity className="h-5 w-5 mr-2" />
              Импорт узлов
            </DialogTitle>
          </div>
          <DialogDescription>
            Вставьте данные конфигураций. Все новые узлы получат статус "Not Tested". Для тестирования используйте кнопку "Testing".
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 mt-2">
          {/* Compact Progress Bar (для любого импорта) */}
          {submitting && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-3xl font-bold text-blue-600">
                    {sessionId && progress 
                      ? Math.round(((progress?.processed_chunks || 0) / (progress?.total_chunks || 1)) * 100)
                      : regularImportProgress
                    }%
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-700">Прогресс импорта</div>
                    <div className="text-xs text-gray-600">
                      {sessionId 
                        ? `Обработано ${progress?.processed_chunks || 0} из ${progress?.total_chunks || 0} частей`
                        : `Файл: ${(importData.length / 1024).toFixed(1)}KB | Протокол: ${protocol.toUpperCase()}`
                      }
                    </div>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={onClose}
                    className="text-xs"
                  >
                    📋 Свернуть
                  </Button>
                  {sessionId && (
                    <Button 
                      variant="destructive" 
                      size="sm" 
                      onClick={cancelImport}
                      className="text-xs"
                    >
                      ⏹️ Отменить
                    </Button>
                  )}
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="relative w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${Math.max(
                      sessionId && progress 
                        ? ((progress?.processed_chunks || 0) / (progress?.total_chunks || 1)) * 100
                        : regularImportProgress,
                      2
                    )}%` 
                  }}
                />
              </div>
            </div>
          )}
          
          {/* Progress Report для chunked импорта - УДАЛЕНО, заменено компактной версией выше */}
          
          {/* Настройки импорта */}
          {!submitting && (
            <div className="space-y-2">
              <Label htmlFor="import-protocol">Тип протокола</Label>
              <Select value={protocol} onValueChange={setProtocol}>
                <SelectTrigger data-testid="import-protocol-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pptp">PPTP</SelectItem>
                  <SelectItem value="ssh">SSH</SelectItem>
                  <SelectItem value="socks">SOCKS</SelectItem>
                  <SelectItem value="server">SERVER</SelectItem>
                  <SelectItem value="ovpn">OVPN</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="import-data">Данные для импорта</Label>
              <div className="flex space-x-2">
                <Button type="button" variant="outline" size="sm" onClick={addSampleText} data-testid="add-sample-text-btn">
                  Добавить пример
                </Button>
                <Label htmlFor="file-upload" className="cursor-pointer">
                  <Button type="button" variant="outline" size="sm" asChild data-testid="upload-file-btn">
                    <span>
                      <Upload className="h-4 w-4 mr-2" />
                      Загрузить файл
                    </span>
                  </Button>
                </Label>
                <input id="file-upload" type="file" accept=".txt,.csv" onChange={handleFileUpload} className="hidden" />
              </div>
            </div>
            <Textarea
              id="import-data"
              value={importData}
              onChange={(e) => setImportData(e.target.value)}
              placeholder="Вставьте данные узлов здесь или загрузите файл..."
              rows={8}
              className="font-mono text-sm"
              data-testid="import-data-textarea"
            />
          </div>

          {/* Итоговый отчёт импорта */}
          {showPreview && previewResult && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Результаты импорта</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                  <div className="text-center">
                    <div className="text-lg font-bold text-green-600">{previewResult.added || 0}</div>
                    <div className="text-xs text-gray-600">Добавлено</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-yellow-600">{previewResult.skipped_duplicates || 0}</div>
                    <div className="text-xs text-gray-600">Дубликатов</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-blue-600">{previewResult.replaced_old || 0}</div>
                    <div className="text-xs text-gray-600">Заменено</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-purple-600">{previewResult.queued_for_verification || 0}</div>
                    <div className="text-xs text-gray-600">В очереди</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-red-600">{previewResult.format_errors || 0}</div>
                    <div className="text-xs text-gray-600">Ошибок формата</div>
                  </div>
                </div>
                {previewResult.processing_errors > 0 && (
                  <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded">
                    <h4 className="font-medium text-sm text-red-600 mb-1">Ошибок обработки: {previewResult.processing_errors}</h4>
                    <div className="text-xs text-red-600">Проверьте журнал ошибок формата для деталей.</div>
                  </div>
                )}
                {previewResult.smart_summary && (
                  <div className="mt-3 text-sm text-gray-700">{previewResult.smart_summary}</div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        <DialogFooter>
          <div className="flex space-x-2">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => {
                // Clear report from localStorage when manually closing
                localStorage.removeItem('lastImportReport');
                onClose();
              }}
            >
              Закрыть
            </Button>
            {!showPreview ? (
              <Button onClick={handleImport} disabled={submitting || !importData.trim()} data-testid="import-btn">
                {submitting ? (
                  progress ? 
                    `Обработка... (${progress.processed_chunks}/${progress.total_chunks})` : 
                    'Выполняется...'
                ) : 'Импортировать узлы'}
              </Button>
            ) : (
              <Button 
                onClick={() => {
                  // Скрыть результаты и подготовить к новому импорту
                  localStorage.removeItem('lastImportReport');
                  setShowPreview(false);
                  setPreviewResult(null);
                  setImportData('');
                  setProtocol('pptp');
                  toast.success('✅ Готово! Можете начать новый импорт');
                }} 
                variant="default" 
                data-testid="close-after-import-btn"
              >
                Готово
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default UnifiedImportModal;
