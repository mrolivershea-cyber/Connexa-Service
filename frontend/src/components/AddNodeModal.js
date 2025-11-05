import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import axios from 'axios';

const AddNodeModal = ({ isOpen, onClose, onNodeAdded }) => {
  const { API } = useAuth();
  const [loading, setLoading] = useState(false);
  const [autoTest, setAutoTest] = useState(true);
  const [testType, setTestType] = useState('ping');
  const [formData, setFormData] = useState({
    protocol: 'pptp', // Protocol selection first
    ip: '',
    port: '',
    login: '',
    password: '',
    provider: '',
    country: '',
    state: '',
    city: '',
    zipcode: '',
    comment: ''
  });

  React.useEffect(() => {
    if (isOpen) {
      setFormData({
        protocol: 'pptp',
        ip: '',
        port: '',
        login: '',
        password: '',
        provider: '',
        country: '',
        state: '',
        city: '',
        zipcode: '',
        comment: ''
      });
      setAutoTest(true);
      setTestType('ping');
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (autoTest) {
        // Use auto-test endpoint
        const response = await axios.post(`${API}/nodes/auto-test?test_type=${testType}`, formData);
        
        const node = response.data.node;
        const testResult = response.data.test_result;
        
        toast.success(`${formData.protocol?.toUpperCase() || 'PPTP'} узел добавлен и протестирован!`);
        
        // Show test results
        if (testResult.ping) {
          const ping = testResult.ping;
          if (ping.reachable) {
            toast.success(`✅ Ping: ${ping.avg_latency}ms, потери: ${ping.packet_loss}%`);
          } else {
            toast.warning('⚠️ Узел недоступен по ping');
          }
        }
        
        if (testResult.speed && testResult.speed.success) {
          const speed = testResult.speed;
          toast.info(`🌐 Скорость: ⬇️${speed.download} Mbps ⬆️${speed.upload} Mbps`);
        }
        
      } else {
        // Standard creation without test
        await axios.post(`${API}/nodes`, formData);
        toast.success(`${formData.protocol?.toUpperCase() || 'PPTP'} узел добавлен успешно!`);
      }
      
      onNodeAdded();
    } catch (error) {
      console.error('Error adding node:', error);
      const errorMsg = error.response?.data?.detail || 'Ошибка добавления узла';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto" data-testid="add-server-modal">
        <DialogHeader>
          <DialogTitle>Добавить {formData.protocol?.toUpperCase() || 'PPTP'} Сервер</DialogTitle>
          <DialogDescription>
            Добавить новый {formData.protocol} сервер в список подключений.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Protocol Selection - First */}
          <div className="space-y-2">
            <Label htmlFor="protocol">Протокол Сервера *</Label>
            <Select value={formData.protocol} onValueChange={(value) => handleChange('protocol', value)}>
              <SelectTrigger data-testid="server-protocol-select">
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
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="ip">IP Адрес *</Label>
              <Input
                id="ip"
                value={formData.ip}
                onChange={(e) => handleChange('ip', e.target.value)}
                placeholder="192.168.1.1"
                required
                data-testid="node-ip-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="port">Порт {formData.protocol === 'socks' ? 'SOCKS' : formData.protocol?.toUpperCase()}</Label>
              <Input
                id="port"
                type="number"
                value={formData.port || ''}
                onChange={(e) => handleChange('port', e.target.value)}
                placeholder={
                  formData.protocol === 'pptp' ? '1723' :
                  formData.protocol === 'ssh' ? '22' :
                  formData.protocol === 'socks' ? '1080' :
                  formData.protocol === 'ovpn' ? '1194' :
                  '8080'
                }
                data-testid="server-port-input"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="login">Логин</Label>
              <Input
                id="login"
                value={formData.login}
                onChange={(e) => handleChange('login', e.target.value)}
                placeholder="username"
                data-testid="node-login-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Пароль</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => handleChange('password', e.target.value)}
                placeholder="password"
                data-testid="node-password-input"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="provider">Провайдер</Label>
            <Input
              id="provider"
              value={formData.provider}
              onChange={(e) => handleChange('provider', e.target.value)}
              placeholder="например, DigitalOcean, AWS, и т.д."
              data-testid="node-provider-input"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="country">Страна</Label>
              <Input
                id="country"
                value={formData.country}
                onChange={(e) => handleChange('country', e.target.value)}
                placeholder="United States"
                data-testid="node-country-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="state">Штат/Регион</Label>
              <Input
                id="state"
                value={formData.state}
                onChange={(e) => handleChange('state', e.target.value)}
                placeholder="California"
                data-testid="node-state-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="city">Город</Label>
              <Input
                id="city"
                value={formData.city}
                onChange={(e) => handleChange('city', e.target.value)}
                placeholder="Los Angeles"
                data-testid="node-city-input"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="zipcode">ZIP Код</Label>
              <Input
                id="zipcode"
                value={formData.zipcode}
                onChange={(e) => handleChange('zipcode', e.target.value)}
                placeholder="90210"
                data-testid="node-zip-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="comment">Комментарий</Label>
              <Input
                id="comment"
                value={formData.comment}
                onChange={(e) => handleChange('comment', e.target.value)}
                placeholder="Опциональный комментарий"
                data-testid="node-comment-input"
              />
            </div>
          </div>

          {/* Auto-test options */}
          <div className="space-y-3 p-3 border rounded">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="auto-test"
                checked={autoTest}
                onCheckedChange={setAutoTest}
                data-testid="auto-test-checkbox"
              />
              <Label htmlFor="auto-test" className="text-sm font-medium">
                Автоматическое тестирование после добавления
              </Label>
            </div>
            
            {autoTest && (
              <div className="ml-6 space-y-2">
                <Label htmlFor="test-type">Тип тестирования:</Label>
                <Select value={testType} onValueChange={setTestType}>
                  <SelectTrigger data-testid="auto-test-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ping">Только Ping (быстро)</SelectItem>
                    <SelectItem value="speed">Только Скорость</SelectItem>
                    <SelectItem value="both">Ping + Скорость (полный)</SelectItem>
                  </SelectContent>
                </Select>
                <div className="text-xs text-gray-600">
                  {testType === 'ping' && 'Проверка доступности узла (ICMP ping)'}
                  {testType === 'speed' && 'Тестирование скорости интернет соединения'}
                  {testType === 'both' && 'Комбинированная проверка доступности и скорости'}
                </div>
              </div>
            )}
          </div>
        </form>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Отмена
          </Button>
          <Button 
            type="submit" 
            onClick={handleSubmit}
            disabled={loading || !formData.ip}
            data-testid="add-node-submit-btn"
          >
            {loading ? (
              autoTest ? 'Добавление и тестирование...' : 'Добавление...'
            ) : (
              `Добавить ${formData.protocol?.toUpperCase() || 'Сервер'}`
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AddNodeModal;
