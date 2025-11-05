import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { 
  Shield, 
  Zap, 
  Database, 
  FileText, 
  Copy, 
  Download,
  Settings2,
  Activity,
  Lock,
  Globe,
  Server
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const SOCKSModal = ({ isOpen, onClose, selectedNodeIds = [], selectAllMode = false, totalCount = 0, activeFilters = {} }) => {
  const { API } = useAuth();
  const [loading, setLoading] = useState(false);
  const [selectedNodesInfo, setSelectedNodesInfo] = useState([]);
  const [socksStats, setSocksStats] = useState({
    active_connections: 0,
    total_tunnels: 0,
    online_socks: 0
  });

  // Настройки маскировки
  const [maskingSettings, setMaskingSettings] = useState({
    obfuscation: true,
    http_imitation: true,
    timing_randomization: true,
    tunnel_encryption: true
  });

  // Настройки производительности
  const [performanceSettings, setPerformanceSettings] = useState({
    tunnel_limit: 100,
    auto_scaling: true,
    cpu_threshold: 80,
    ram_threshold: 80
  });

  // Настройки безопасности
  const [securitySettings, setSecuritySettings] = useState({
    whitelist_enabled: false,
    allowed_ips: []
  });

  const [newAllowedIp, setNewAllowedIp] = useState('');
  const [activeProxies, setActiveProxies] = useState([]);
  const [proxyFileContent, setProxyFileContent] = useState('');
  
  // Состояния для онлайн просмотра
  const [showDatabaseModal, setShowDatabaseModal] = useState(false);
  const [showProxyFileModal, setShowProxyFileModal] = useState(false);
  const [databaseReport, setDatabaseReport] = useState('');

  // Загрузка данных при открытии модала
  useEffect(() => {
    if (isOpen) {
      loadSOCKSData();
      loadSelectedNodesInfo();
    }
  }, [isOpen, selectedNodeIds]);

  const loadSelectedNodesInfo = async () => {
    if (selectedNodeIds.length === 0) {
      setSelectedNodesInfo([]);
      return;
    }

    try {
      const responses = await Promise.all(
        selectedNodeIds.map(id => 
          axios.get(`${API}/nodes/${id}`)
            .then(response => ({ id, data: response.data, error: null }))
            .catch(error => ({ id, data: null, error: error.message }))
        )
      );
      setSelectedNodesInfo(responses);
    } catch (error) {
      console.error('Error loading selected nodes info:', error);
      setSelectedNodesInfo([]);
    }
  };

  const loadSOCKSData = async () => {
    try {
      // Загрузка статистики SOCKS
      const statsResponse = await axios.get(`${API}/socks/stats`);
      setSocksStats(statsResponse.data);

      // Загрузка настроек
      const configResponse = await axios.get(`${API}/socks/config`);
      const config = configResponse.data;
      setMaskingSettings(config.masking || maskingSettings);
      setPerformanceSettings(config.performance || performanceSettings);
      setSecuritySettings(config.security || securitySettings);

      // Загрузка активных прокси
      const proxiesResponse = await axios.get(`${API}/socks/active`);
      setActiveProxies(proxiesResponse.data.proxies || []);

      // Загрузка содержимого файла прокси
      const fileResponse = await axios.get(`${API}/socks/proxy-file`);
      setProxyFileContent(fileResponse.data.content || '');

    } catch (error) {
      console.error('Error loading SOCKS data:', error);
      // Если endpoints не существуют, используем заглушки
      setSocksStats({ active_connections: 0, total_tunnels: 0, online_socks: 0 });
      setActiveProxies([]);
      setProxyFileContent('# SOCKS прокси файл будет создан после запуска сервисов\n');
    }
  };

  const handleStartSocks = async () => {
    if (!selectAllMode && selectedNodeIds.length === 0) {
      toast.error('⚠️ Выберите узлы для запуска SOCKS сервисов', {
        description: 'Сначала закройте это окно, отметьте узлы со статусом "ping_ok" или "speed_ok" в таблице, затем откройте SOCKS снова'
      });
      return;
    }

    setLoading(true);
    try {
      const requestData = {
        masking_settings: maskingSettings,
        performance_settings: performanceSettings,
        security_settings: securitySettings
      };
      
      // Для selectAllMode передаём фильтры вместо node_ids
      if (selectAllMode) {
        requestData.filters = activeFilters;
      } else {
        requestData.node_ids = selectedNodeIds;
      }
      
      const response = await axios.post(`${API}/socks/start`, requestData);

      const results = response.data.results;
      const successCount = results.filter(r => r.success).length;
      const failCount = results.length - successCount;
      
      // Анализируем результаты и показываем детальную информацию
      const failedResults = results.filter(r => !r.success);
      const successfulResults = results.filter(r => r.success);
      
      // Показываем детальную информацию в консоли
      if (failedResults.length > 0) {
        const errorMessages = failedResults.map(r => `Узел ${r.node_id} (${r.ip}): ${r.message}`).join('\n');
        console.log('SOCKS start failures:', errorMessages);
      }
      
      // Анализируем типы ошибок
      const alreadyOnlineErrors = failedResults.filter(r => 
        r.message && r.message.includes('current: online')
      );
      const wrongStatusErrors = failedResults.filter(r => 
        r.message && (
          r.message.includes('ping_ok or speed_ok') || 
          r.message.includes('current: ping_failed') ||
          r.message.includes('current: not_tested')
        )
      );
      const otherErrors = failedResults.filter(r => 
        !alreadyOnlineErrors.includes(r) && !wrongStatusErrors.includes(r)
      );

      // Составляем детальные сообщения
      let detailMessages = [];
      if (alreadyOnlineErrors.length > 0) {
        detailMessages.push(`${alreadyOnlineErrors.length} узлов уже запущены (нужно сначала остановить)`);
      }
      if (wrongStatusErrors.length > 0) {
        detailMessages.push(`${wrongStatusErrors.length} узлов имеют неподходящий статус`);
      }
      if (otherErrors.length > 0) {
        detailMessages.push(`${otherErrors.length} узлов с другими ошибками`);
      }

      if (successCount > 0) {
        toast.success(`✅ SOCKS запущен для ${successCount} из ${results.length} узлов`, {
          description: successCount === results.length ? 
            'Все узлы успешно запущены' : 
            detailMessages.join(', ')
        });
      }
      
      if (failCount > 0 && successCount === 0) {
        toast.error(`❌ Не удалось запустить SOCKS ни для одного узла (${results.length})`, {
          description: detailMessages.join('. ') || 'Проверьте статус узлов в таблице выше'
        });
      } else if (failCount > 0) {
        toast.warning(`⚠️ Частично запущено: ${successCount} успешно, ${failCount} ошибок`, {
          description: detailMessages.join('. ')
        });
      }

      // Обновляем данные
      await Promise.all([loadSOCKSData(), loadSelectedNodesInfo()]);

    } catch (error) {
      console.error('Error starting SOCKS:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Неизвестная ошибка';
      toast.error('❌ Ошибка запуска SOCKS: ' + errorMessage, {
        description: 'Проверьте подключение к серверу и статус узлов'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStopSocks = async () => {
    if (!selectAllMode && selectedNodeIds.length === 0) {
      toast.error('Выберите узлы для остановки SOCKS сервисов');
      return;
    }

    setLoading(true);
    try {
      const requestData = {};
      
      // Для selectAllMode передаём фильтры вместо node_ids
      if (selectAllMode) {
        requestData.filters = activeFilters;
      } else {
        requestData.node_ids = selectedNodeIds;
      }
      
      const response = await axios.post(`${API}/socks/stop`, requestData);

      const results = response.data.results;
      const successCount = results.filter(r => r.success).length;

      if (successCount > 0) {
        toast.success(`🛑 SOCKS остановлен для ${successCount} узлов`);
      }

      await Promise.all([loadSOCKSData(), loadSelectedNodesInfo()]);

    } catch (error) {
      console.error('Error stopping SOCKS:', error);
      toast.error('Ошибка остановки SOCKS: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleRestartSocks = async () => {
    if (selectedNodeIds.length === 0) {
      toast.error('Выберите узлы для перезапуска SOCKS сервисов');
      return;
    }

    setLoading(true);
    try {
      // Сначала останавливаем
      const stopResponse = await axios.post(`${API}/socks/stop`, {
        node_ids: selectedNodeIds
      });

      const stopResults = stopResponse.data.results;
      const stopSuccessCount = stopResults.filter(r => r.success).length;

      if (stopSuccessCount > 0) {
        // Небольшая пауза для корректной остановки
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Затем запускаем снова
        const startResponse = await axios.post(`${API}/socks/start`, {
          node_ids: selectedNodeIds,
          masking_settings: maskingSettings,
          performance_settings: performanceSettings,
          security_settings: securitySettings
        });

        const startResults = startResponse.data.results;
        const startSuccessCount = startResults.filter(r => r.success).length;

        if (startSuccessCount > 0) {
          toast.success(`🔄 SOCKS перезапущен для ${startSuccessCount} узлов`, {
            description: `Остановлено: ${stopSuccessCount}, Запущено: ${startSuccessCount}`
          });
        } else {
          toast.warning(`⚠️ Остановлено ${stopSuccessCount} узлов, но запуск не удался`, {
            description: 'Проверьте статус узлов после остановки'
          });
        }
      } else {
        toast.error('❌ Не удалось остановить ни одного узла для перезапуска');
      }

      await Promise.all([loadSOCKSData(), loadSelectedNodesInfo()]);

    } catch (error) {
      console.error('Error restarting SOCKS:', error);
      toast.error('Ошибка перезапуска SOCKS: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/socks/config`, {
        masking: maskingSettings,
        performance: performanceSettings,
        security: securitySettings
      });
      toast.success('✅ Настройки SOCKS сохранены');
    } catch (error) {
      console.error('Error saving config:', error);
      toast.error('Ошибка сохранения настроек: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleAddAllowedIp = () => {
    if (newAllowedIp.trim()) {
      setSecuritySettings(prev => ({
        ...prev,
        allowed_ips: [...prev.allowed_ips, newAllowedIp.trim()]
      }));
      setNewAllowedIp('');
    }
  };

  const handleRemoveAllowedIp = (index) => {
    setSecuritySettings(prev => ({
      ...prev,
      allowed_ips: prev.allowed_ips.filter((_, i) => i !== index)
    }));
  };

  const handleViewDatabase = async () => {
    try {
      const response = await axios.get(`${API}/socks/database-report`);
      // Показываем отчет в модальном окне вместо скачивания
      const reportText = typeof response.data === 'object' 
        ? JSON.stringify(response.data, null, 2) 
        : response.data;
      setDatabaseReport(reportText);
      setShowDatabaseModal(true);
      toast.success('📊 Отчет БД SOCKS загружен');
    } catch (error) {
      console.error('Error loading database report:', error);
      toast.error('Ошибка загрузки отчета БД: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleOpenProxyFile = () => {
    // Показываем содержимое файла в модальном окне вместо скачивания
    setShowProxyFileModal(true);
    toast.success('📄 Файл прокси открыт для просмотра');
  };

  const handleCopyCredentials = async () => {
    if (activeProxies.length === 0) {
      toast.error('Нет активных SOCKS прокси для копирования');
      return;
    }

    const credentials = activeProxies.map(proxy => 
      `socks5://${proxy.login}:${proxy.password}@${proxy.ip}:${proxy.port}`
    ).join('\n');

    try {
      await navigator.clipboard.writeText(credentials);
      toast.success(`📋 Скопировано ${activeProxies.length} SOCKS credentials`);
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      toast.error('Ошибка копирования в буфер обмена');
    }
  };

  const handleCopyDatabaseReport = async () => {
    try {
      await navigator.clipboard.writeText(databaseReport);
      toast.success('📋 Отчет БД скопирован в буфер обмена');
    } catch (error) {
      console.error('Error copying database report:', error);
      toast.error('Ошибка копирования отчета');
    }
  };

  const handleDownloadDatabaseReport = () => {
    const blob = new Blob([databaseReport], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `socks_database_report_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('📥 Отчет БД скачан');
  };

  const handleCopyProxyFile = async () => {
    try {
      await navigator.clipboard.writeText(proxyFileContent);
      toast.success('📋 Содержимое файла прокси скопировано');
    } catch (error) {
      console.error('Error copying proxy file:', error);
      toast.error('Ошибка копирования файла');
    }
  };

  const handleDownloadProxyFile = () => {
    const blob = new Blob([proxyFileContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'active_proxies.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('📥 Файл прокси скачан');
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-blue-600" />
            SOCKS Управление и Настройки
          </DialogTitle>
          <DialogDescription>
            Управление SOCKS5 сервисами с маскировкой трафика и мониторингом
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Левая колонка: Статистика и управление */}
          <div className="space-y-4">
            {/* Статистика SOCKS */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  SOCKS Статистика
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600">{socksStats.online_socks}</div>
                    <div className="text-sm text-gray-600">Online</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-600">{socksStats.total_tunnels}</div>
                    <div className="text-sm text-gray-600">Туннели</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">{socksStats.active_connections}</div>
                    <div className="text-sm text-gray-600">Соединения</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Информация о выбранных узлах */}
            {selectedNodesInfo.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Server className="h-5 w-5" />
                    Выбранные узлы ({selectedNodesInfo.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {selectedNodesInfo.map(({ id, data, error }) => {
                      if (error || !data) {
                        return (
                          <div key={id} className="flex justify-between items-center p-2 bg-red-50 border border-red-200 rounded">
                            <span className="text-sm text-red-700">Узел {id}</span>
                            <Badge variant="destructive">Ошибка</Badge>
                          </div>
                        );
                      }

                      const canStartSOCKS = ['ping_ok', 'speed_ok'].includes(data.status);
                      const isAlreadyOnline = data.status === 'online';

                      return (
                        <div key={id} className={`flex justify-between items-center p-2 border rounded ${
                          canStartSOCKS ? 'bg-green-50 border-green-200' : 
                          isAlreadyOnline ? 'bg-blue-50 border-blue-200' : 
                          'bg-red-50 border-red-200'
                        }`}>
                          <span className="text-sm font-mono">{data.ip}</span>
                          <div className="flex items-center gap-2">
                            <Badge variant={
                              canStartSOCKS ? 'default' : 
                              isAlreadyOnline ? 'secondary' : 
                              'destructive'
                            }>
                              {data.status}
                            </Badge>
                            {isAlreadyOnline ? (
                              <span className="text-xs text-blue-600">✓ Уже запущен</span>
                            ) : canStartSOCKS ? (
                              <span className="text-xs text-green-600">✓ Готов</span>
                            ) : (
                              <span className="text-xs text-red-600">✗ Неподходящий</span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* Сводная информация */}
                  <div className="mt-3 pt-3 border-t">
                    {(() => {
                      const validNodes = selectedNodesInfo.filter(({ data }) => 
                        data && ['ping_ok', 'speed_ok'].includes(data.status)
                      );
                      const onlineNodes = selectedNodesInfo.filter(({ data }) => 
                        data && data.status === 'online'
                      );
                      const invalidNodes = selectedNodesInfo.filter(({ data, error }) => 
                        error || !data || !['ping_ok', 'speed_ok', 'online'].includes(data?.status)
                      );

                      return (
                        <div className="text-xs space-y-1">
                          {validNodes.length > 0 && (
                            <div className="text-green-600">✓ {validNodes.length} узлов готовы для запуска SOCKS</div>
                          )}
                          {onlineNodes.length > 0 && (
                            <div className="text-blue-600">ℹ {onlineNodes.length} узлов уже запущены (нужно сначала остановить)</div>
                          )}
                          {invalidNodes.length > 0 && (
                            <div className="text-red-600">✗ {invalidNodes.length} узлов не подходят для SOCKS</div>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Управление SOCKS */}
            <Card>
              <CardHeader>
                <CardTitle>Управление Сервисами</CardTitle>
                <CardDescription>
                  {selectedNodeIds.length === 0 ? (
                    <div className="mt-2 text-xs text-amber-600">
                      ⚠️ Выберите узлы в таблице перед запуском SOCKS
                    </div>
                  ) : (
                    <div className="mt-2 text-xs text-blue-600">
                      💡 Только узлы со статусом "ping_ok" или "speed_ok" могут запустить SOCKS
                    </div>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {(() => {
                  // Анализируем статусы выбранных узлов
                  const validNodes = selectedNodesInfo.filter(({ data }) => 
                    data && ['ping_ok', 'speed_ok'].includes(data.status)
                  );
                  const onlineNodes = selectedNodesInfo.filter(({ data }) => 
                    data && data.status === 'online'
                  );
                  
                  return (
                    <div className="space-y-2">
                      {/* Основные кнопки */}
                      <div className="flex gap-2">
                        <Button 
                          onClick={handleStartSocks}
                          disabled={loading || selectedNodeIds.length === 0 || validNodes.length === 0}
                          className="bg-green-600 hover:bg-green-700 flex-1"
                        >
                          <Zap className="h-4 w-4 mr-2" />
                          Старт SOCKS ({validNodes.length})
                        </Button>
                        <Button 
                          onClick={handleStopSocks}
                          disabled={loading || selectedNodeIds.length === 0}
                          variant="destructive"
                          className="flex-1"
                        >
                          <Server className="h-4 w-4 mr-2" />
                          Стоп SOCKS
                        </Button>
                      </div>
                      
                      {/* Кнопка перезапуска для онлайн узлов */}
                      {onlineNodes.length > 0 && (
                        <Button 
                          onClick={handleRestartSocks}
                          disabled={loading || selectedNodeIds.length === 0}
                          variant="outline"
                          className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
                        >
                          <Activity className="h-4 w-4 mr-2" />
                          Перезапуск SOCKS ({onlineNodes.length} узлов)
                        </Button>
                      )}
                    </div>
                  );
                })()}
              </CardContent>
            </Card>

            {/* Действия с файлами и БД */}
            <Card>
              <CardHeader>
                <CardTitle>Управление Данными</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Button onClick={handleViewDatabase} variant="outline" className="w-full">
                    <Database className="h-4 w-4 mr-2" />
                    Смотреть базу отчет
                  </Button>
                  <Button onClick={handleOpenProxyFile} variant="outline" className="w-full">
                    <FileText className="h-4 w-4 mr-2" />
                    Открыть текстовый файл
                  </Button>
                  <Button onClick={handleCopyCredentials} variant="outline" className="w-full">
                    <Copy className="h-4 w-4 mr-2" />
                    Копировать credentials
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Правая колонка: Настройки */}
          <div className="space-y-4">
            {/* Настройки маскировки */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lock className="h-5 w-5" />
                  Настройки Маскировки
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="obfuscation">Обфускация протокола</Label>
                  <Switch 
                    id="obfuscation"
                    checked={maskingSettings.obfuscation}
                    onCheckedChange={(checked) => 
                      setMaskingSettings(prev => ({ ...prev, obfuscation: checked }))
                    }
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="http_imitation">Имитация HTTP/HTTPS</Label>
                  <Switch 
                    id="http_imitation"
                    checked={maskingSettings.http_imitation}
                    onCheckedChange={(checked) => 
                      setMaskingSettings(prev => ({ ...prev, http_imitation: checked }))
                    }
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="timing_randomization">Рандомизация timing</Label>
                  <Switch 
                    id="timing_randomization"
                    checked={maskingSettings.timing_randomization}
                    onCheckedChange={(checked) => 
                      setMaskingSettings(prev => ({ ...prev, timing_randomization: checked }))
                    }
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="tunnel_encryption">Шифрование туннеля</Label>
                  <Switch 
                    id="tunnel_encryption"
                    checked={maskingSettings.tunnel_encryption}
                    onCheckedChange={(checked) => 
                      setMaskingSettings(prev => ({ ...prev, tunnel_encryption: checked }))
                    }
                  />
                </div>
              </CardContent>
            </Card>

            {/* Настройки производительности */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings2 className="h-5 w-5" />
                  Настройки Производительности
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="tunnel_limit">Лимит туннелей</Label>
                  <Input
                    id="tunnel_limit"
                    type="number"
                    value={performanceSettings.tunnel_limit}
                    onChange={(e) => 
                      setPerformanceSettings(prev => ({ 
                        ...prev, 
                        tunnel_limit: parseInt(e.target.value) || 100 
                      }))
                    }
                    placeholder="100"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="auto_scaling">Автоматическое увеличение</Label>
                  <Switch 
                    id="auto_scaling"
                    checked={performanceSettings.auto_scaling}
                    onCheckedChange={(checked) => 
                      setPerformanceSettings(prev => ({ ...prev, auto_scaling: checked }))
                    }
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="cpu_threshold">CPU порог (%)</Label>
                    <Input
                      id="cpu_threshold"
                      type="number"
                      value={performanceSettings.cpu_threshold}
                      onChange={(e) => 
                        setPerformanceSettings(prev => ({ 
                          ...prev, 
                          cpu_threshold: parseInt(e.target.value) || 80 
                        }))
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor="ram_threshold">RAM порог (%)</Label>
                    <Input
                      id="ram_threshold"
                      type="number"
                      value={performanceSettings.ram_threshold}
                      onChange={(e) => 
                        setPerformanceSettings(prev => ({ 
                          ...prev, 
                          ram_threshold: parseInt(e.target.value) || 80 
                        }))
                      }
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Настройки безопасности */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  Настройки Безопасности
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="whitelist_enabled">Whitelist IP адресов</Label>
                  <Switch 
                    id="whitelist_enabled"
                    checked={securitySettings.whitelist_enabled}
                    onCheckedChange={(checked) => 
                      setSecuritySettings(prev => ({ ...prev, whitelist_enabled: checked }))
                    }
                  />
                </div>
                
                {securitySettings.whitelist_enabled && (
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <Input
                        placeholder="192.168.1.1"
                        value={newAllowedIp}
                        onChange={(e) => setNewAllowedIp(e.target.value)}
                      />
                      <Button onClick={handleAddAllowedIp} size="sm">
                        Добавить
                      </Button>
                    </div>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {securitySettings.allowed_ips.map((ip, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                          <span className="text-sm">{ip}</span>
                          <Button 
                            size="sm" 
                            variant="ghost" 
                            onClick={() => handleRemoveAllowedIp(index)}
                          >
                            ✕
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        <Separator />

        <div className="flex justify-between">
          <Button variant="outline" onClick={onClose}>
            Закрыть
          </Button>
          <Button onClick={handleSaveConfig} disabled={loading}>
            <Settings2 className="h-4 w-4 mr-2" />
            Сохранить Настройки
          </Button>
        </div>
      </DialogContent>
      
      {/* Модальное окно для просмотра отчета БД */}
      <Dialog open={showDatabaseModal} onOpenChange={setShowDatabaseModal}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-600" />
              Отчет База Данных SOCKS
            </DialogTitle>
            <DialogDescription>
              Просмотр отчета базы данных SOCKS в режиме онлайн
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="flex gap-2 mb-4">
              <Button variant="outline" size="sm" onClick={handleCopyDatabaseReport}>
                <Copy className="h-4 w-4 mr-2" />
                Копировать
              </Button>
              <Button variant="outline" size="sm" onClick={handleDownloadDatabaseReport}>
                <Download className="h-4 w-4 mr-2" />
                Скачать
              </Button>
            </div>
            
            <div className="flex-1 border rounded-lg bg-gray-50 overflow-auto">
              <pre className="p-4 text-sm font-mono whitespace-pre-wrap">
                {databaseReport || 'Загрузка отчета...'}
              </pre>
            </div>
          </div>
          
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => setShowDatabaseModal(false)}>
              Закрыть
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Модальное окно для просмотра файла прокси */}
      <Dialog open={showProxyFileModal} onOpenChange={setShowProxyFileModal}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-green-600" />
              Текстовый Файл Прокси
            </DialogTitle>
            <DialogDescription>
              Просмотр активных SOCKS прокси в режиме онлайн
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="flex gap-2 mb-4">
              <Button variant="outline" size="sm" onClick={handleCopyProxyFile}>
                <Copy className="h-4 w-4 mr-2" />
                Копировать
              </Button>
              <Button variant="outline" size="sm" onClick={handleDownloadProxyFile}>
                <Download className="h-4 w-4 mr-2" />
                Скачать
              </Button>
            </div>
            
            <div className="flex-1 border rounded-lg bg-gray-50 overflow-auto">
              <pre className="p-4 text-sm font-mono whitespace-pre-wrap">
                {proxyFileContent || '# Файл прокси пуст\n# Запустите SOCKS сервисы для появления активных прокси'}
              </pre>
            </div>
          </div>
          
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => setShowProxyFileModal(false)}>
              Закрыть
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Dialog>
  );
};

export default SOCKSModal;