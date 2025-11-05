import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { Settings, Lock, Bell } from 'lucide-react';

const OptionsModal = ({ isOpen, onClose }) => {
  const { changePassword, API, token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('password');
  
  // Password change state
  const [passwordForm, setPasswordForm] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [passwordError, setPasswordError] = useState('');
  
  // API Settings state
  const [apiSettings, setApiSettings] = useState({
    geo_service: 'ip-api',
    fraud_service: 'ipqs',
    ipinfo_token: '',
    maxmind_key: '',
    ipqs_api_key: 'uMGBBCbfRXOHbojCTJBloiA6tIIqJcFj',
    scamalytics_key: '',
    abuseipdb_key: ''
  });
  
  // Load settings on open
  React.useEffect(() => {
    if (isOpen && token) {
      fetch(`${API}/settings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(r => r.json())
        .then(data => setApiSettings(data))
        .catch(err => console.error('Failed to load settings:', err));
    }
  }, [isOpen, API, token]);
  
  const saveApiSettings = async () => {
    try {
      const response = await fetch(`${API}/settings`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(apiSettings)
      });
      if (response.ok) {
        toast.success('Настройки сохранены');
      } else {
        toast.error('Ошибка сохранения');
      }
    } catch (error) {
      toast.error('Ошибка: ' + error.message);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setPasswordError('');

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordError('New password and confirmation do not match');
      setLoading(false);
      return;
    }

    if (passwordForm.newPassword.length < 6) {
      setPasswordError('Password must be at least 6 characters long');
      setLoading(false);
      return;
    }

    const result = await changePassword(
      passwordForm.oldPassword, 
      passwordForm.newPassword, 
      passwordForm.confirmPassword
    );
    
    if (result.success) {
      toast.success('Password changed successfully!');
      setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
    } else {
      setPasswordError(result.error);
      toast.error('Password change failed: ' + result.error);
    }
    
    setLoading(false);
  };

  const handlePasswordChange = (field, value) => {
    setPasswordForm(prev => ({ ...prev, [field]: value }));
    setPasswordError('');
  };

  React.useEffect(() => {
    if (isOpen) {
      setPasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
      setPasswordError('');
      setActiveTab('password');
    }
  }, [isOpen]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[85vh]" data-testid="options-modal">
        <DialogHeader className="pb-2">
          <DialogTitle className="text-lg flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </DialogTitle>
          <DialogDescription>
            Manage your admin panel settings and preferences.
          </DialogDescription>
        </DialogHeader>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="password" data-testid="password-tab" className="flex items-center gap-1 text-xs">
              <Lock className="h-3 w-3" />
              Security
            </TabsTrigger>
            <TabsTrigger value="system" data-testid="system-tab" className="flex items-center gap-1 text-xs">
              <Settings className="h-3 w-3" />
              Services
            </TabsTrigger>
            <TabsTrigger value="info" data-testid="info-tab" className="flex items-center gap-1 text-xs">
              Info
            </TabsTrigger>
            <TabsTrigger value="notifications" data-testid="notifications-tab" className="flex items-center gap-1 text-xs">
              <Bell className="h-3 w-3" />
              Alerts
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="password" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Change Password</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePasswordSubmit} className="space-y-4">
                  {passwordError && (
                    <Alert variant="destructive">
                      <AlertDescription>{passwordError}</AlertDescription>
                    </Alert>
                  )}
                  
                  <div className="space-y-2">
                    <Label htmlFor="old-password-modal">Current Password</Label>
                    <Input
                      id="old-password-modal"
                      type="password"
                      value={passwordForm.oldPassword}
                      onChange={(e) => handlePasswordChange('oldPassword', e.target.value)}
                      required
                      disabled={loading}
                      data-testid="old-password-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="new-password-modal">New Password</Label>
                    <Input
                      id="new-password-modal"
                      type="password"
                      value={passwordForm.newPassword}
                      onChange={(e) => handlePasswordChange('newPassword', e.target.value)}
                      required
                      minLength={6}
                      disabled={loading}
                      data-testid="new-password-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirm-password-modal">Confirm New Password</Label>
                    <Input
                      id="confirm-password-modal"
                      type="password"
                      value={passwordForm.confirmPassword}
                      onChange={(e) => handlePasswordChange('confirmPassword', e.target.value)}
                      required
                      minLength={6}
                      disabled={loading}
                      data-testid="confirm-password-input"
                    />
                  </div>
                  
                  <Button 
                    type="submit" 
                    disabled={loading}
                    data-testid="change-password-modal-btn"
                  >
                    {loading ? 'Changing Password...' : 'Change Password'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="system" className="space-y-3">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Геолокация</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <input type="radio" id="geo-ipapi" name="geo_service" checked={apiSettings.geo_service === 'ip-api'} onChange={() => setApiSettings(prev => ({...prev, geo_service: 'ip-api'}))} />
                    <Label htmlFor="geo-ipapi" className="text-sm">ip-api.com (бесплатно)</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input type="radio" id="geo-ipapico" name="geo_service" checked={apiSettings.geo_service === 'ipapi.co'} onChange={() => setApiSettings(prev => ({...prev, geo_service: 'ipapi.co'}))} />
                    <Label htmlFor="geo-ipapico" className="text-sm">ipapi.co (бесплатно)</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input type="radio" id="geo-ipinfo" name="geo_service" checked={apiSettings.geo_service === 'ipinfo'} onChange={() => setApiSettings(prev => ({...prev, geo_service: 'ipinfo'}))} />
                    <Label htmlFor="geo-ipinfo" className="text-sm">ipinfo.io</Label>
                  </div>
                  <Input placeholder="API токен" className="text-xs h-8" value={apiSettings.ipinfo_token} onChange={(e) => setApiSettings(prev => ({...prev, ipinfo_token: e.target.value}))} />
                  
                  <div className="flex items-center space-x-2">
                    <input type="radio" id="geo-maxmind" name="geo_service" checked={apiSettings.geo_service === 'maxmind'} onChange={() => setApiSettings(prev => ({...prev, geo_service: 'maxmind'}))} />
                    <Label htmlFor="geo-maxmind" className="text-sm">MaxMind GeoIP2</Label>
                  </div>
                  <Input placeholder="License Key" className="text-xs h-8" value={apiSettings.maxmind_key} onChange={(e) => setApiSettings(prev => ({...prev, maxmind_key: e.target.value}))} />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Fraud Detection</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <input type="radio" id="fraud-ipqs" name="fraud_service" checked={apiSettings.fraud_service === 'ipqs'} onChange={() => setApiSettings(prev => ({...prev, fraud_service: 'ipqs'}))} />
                    <Label htmlFor="fraud-ipqs" className="text-sm">IPQualityScore</Label>
                  </div>
                  <Input placeholder="API Key" className="text-xs h-8" value={apiSettings.ipqs_api_key} onChange={(e) => setApiSettings(prev => ({...prev, ipqs_api_key: e.target.value}))} />
                  
                  <div className="flex items-center space-x-2">
                    <input type="radio" id="fraud-abuseipdb" name="fraud_service" checked={apiSettings.fraud_service === 'abuseipdb'} onChange={() => setApiSettings(prev => ({...prev, fraud_service: 'abuseipdb'}))} />
                    <Label htmlFor="fraud-abuseipdb" className="text-sm">AbuseIPDB</Label>
                  </div>
                  <Input placeholder="API Key" className="text-xs h-8" value={apiSettings.abuseipdb_key} onChange={(e) => setApiSettings(prev => ({...prev, abuseipdb_key: e.target.value}))} />
                  
                  <div className="flex items-center space-x-2">
                    <input type="radio" id="fraud-scamalytics" name="fraud_service" checked={apiSettings.fraud_service === 'scamalytics'} onChange={() => setApiSettings(prev => ({...prev, fraud_service: 'scamalytics'}))} />
                    <Label htmlFor="fraud-scamalytics" className="text-sm">Scamalytics</Label>
                  </div>
                  <Input placeholder="API Key" className="text-xs h-8" value={apiSettings.scamalytics_key} onChange={(e) => setApiSettings(prev => ({...prev, scamalytics_key: e.target.value}))} />
                </div>
                
                <Button onClick={saveApiSettings} className="w-full mt-2" size="sm">
                  Сохранить
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="info" className="space-y-3">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">System Info</CardTitle>
              </CardHeader>
              <CardContent className="text-sm space-y-2">
                <div><strong>Version:</strong> Connexa v1.7</div>
                <div><strong>Database:</strong> SQLite</div>
                <div><strong>Backend:</strong> FastAPI</div>
                <div><strong>Frontend:</strong> React</div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="notifications" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Notification Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <Alert>
                  <AlertDescription>
                    Notification settings (Telegram integration, email alerts, etc.) 
                    will be available in future versions. Currently, all notifications 
                    are displayed as browser toasts.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button type="button" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default OptionsModal;
