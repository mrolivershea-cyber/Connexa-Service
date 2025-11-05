import React, { useState, Fragment } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { Card, CardContent } from '../components/ui/card';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../components/ui/dropdown-menu';
import { toast } from 'sonner';
import { 
  MoreHorizontal,
  Eye,
  EyeOff,
  Copy,
  Trash2,
  Edit,
  Check,
  X,
  Activity,
  Play,
  Square,
  Download,
  Zap
} from 'lucide-react';
import axios from 'axios';

const NodesTable = ({ nodes, selectedNodes, onSelectNode, onNodeUpdated, loading }) => {
  const { API } = useAuth();
  const [editingNode, setEditingNode] = useState(null);
  const [editValues, setEditValues] = useState({});
  const [showPasswords, setShowPasswords] = useState({});

  const handleSelectAll = () => {
    if (selectedNodes.length === nodes.length && nodes.length > 0) {
      // Deselect all
      nodes.forEach(node => onSelectNode(node.id));
    } else {
      // Select all that are not already selected
      nodes.forEach(node => {
        if (!selectedNodes.includes(node.id)) {
          onSelectNode(node.id);
        }
      });
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      not_tested: { emoji: '⚫', class: 'bg-gray-100 text-gray-800', label: 'Not Tested' },
      ping_light: { emoji: '🟡', class: 'bg-yellow-100 text-yellow-800', label: 'Ping Test' },
      ping_failed: { emoji: '🔴', class: 'bg-red-100 text-red-800', label: 'PING Failed' },
      ping_ok: { emoji: '🟠', class: 'bg-orange-100 text-orange-800', label: 'PING OK' },
      speed_ok: { emoji: '🔵', class: 'bg-blue-100 text-blue-800', label: 'Speed OK' },
      offline: { emoji: '🔴', class: 'bg-red-100 text-red-800', label: 'Offline' },
      online: { emoji: '🟢', class: 'bg-green-100 text-green-800', label: 'Online' }
    };
    
    const config = statusConfig[status] || statusConfig.not_tested;
    
    return (
      <Badge className={config.class} title={config.label}>
        {config.emoji}
      </Badge>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    
    // Правильно парсим UTC время от API
    const date = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z');
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMins < 1) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else {
      return `${diffDays}d ago`;
    }
  };

  const testNode = async (nodeId, testType = 'ping') => {
    try {
      let endpoint;
      let requestData;
      
      // Используем ТЕ ЖЕ endpoints что и в Testing Modal!
      if (testType === 'ping') {
        endpoint = `${API}/manual/ping-light-test-batch-progress`;
        requestData = { node_ids: [nodeId] };
      } else if (testType === 'speed') {
        endpoint = `${API}/manual/speed-test-batch-progress`;
        requestData = { node_ids: [nodeId] };
      } else if (testType === 'geo') {
        endpoint = `${API}/manual/geo-test-batch`;
        requestData = { node_ids: [nodeId] };
      } else if (testType === 'fraud') {
        endpoint = `${API}/manual/fraud-test-batch`;
        requestData = { node_ids: [nodeId] };
      } else if (testType === 'geo_fraud') {
        endpoint = `${API}/manual/geo-fraud-test-batch`;
        requestData = { node_ids: [nodeId] };
      }
      
      const response = await axios.post(endpoint, requestData);
      
      // Обработка ответов
      if (response.data.results && response.data.results.length > 0) {
        const result = response.data.results[0];
        if (result.success) {
          toast.success(`Тест ${testType} завершен для ${result.ip || nodeId}`);
          onNodeUpdated();
        } else {
          toast.error(`Тест не выполнен: ${result.message || 'Неизвестная ошибка'}`);
        }
      } else if (response.data.session_id) {
        // Для ping/speed с прогрессом
        toast.success(`Тест ${testType} запущен`);
        setTimeout(() => onNodeUpdated(), 3000); // Обновим через 3 сек
      } else {
        toast.success(`Тест ${testType} завершен`);
        onNodeUpdated();
      }
    } catch (error) {
      console.error('Ошибка теста:', error);
      toast.error('Ошибка теста: ' + (error.response?.data?.detail || error.message));
    }
  };

  const startServices = async (nodeId) => {
    try {
      const response = await axios.post(`${API}/nodes/${nodeId}/services/start`);
      if (response.data.success) {
        toast.success(response.data.message);
        onNodeUpdated();
      } else {
        toast.error(`Start failed: ${response.data.message}`);
      }
    } catch (error) {
      console.error('Start services error:', error);
      toast.error('Start failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const stopServices = async (nodeId) => {
    try {
      const response = await axios.post(`${API}/nodes/${nodeId}/services/stop`);
      if (response.data.success) {
        toast.success(response.data.message);
        onNodeUpdated();
      } else {
        toast.error(`Stop failed: ${response.data.message}`);
      }
    } catch (error) {
      console.error('Stop services error:', error);
      toast.error('Stop failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const togglePasswordVisibility = (nodeId) => {
    setShowPasswords(prev => ({
      ...prev,
      [nodeId]: !prev[nodeId]
    }));
  };

  const copyToClipboard=async(t,type="text")=>{try{const el=document.createElement("textarea");el.value=t;document.body.appendChild(el);el.select();document.execCommand("copy");document.body.removeChild(el);toast.success(type+" copied")}catch{toast.error("Copy failed")}};

  const copySocks = (node) => {
    if (!node.socks_ip || !node.socks_port) {
      toast.error("SOCKS данные недоступны");
      return;
    }
    const socksFormat = `${node.socks_ip}:${node.socks_port}:${node.socks_login}:${node.socks_password}`;
    copyToClipboard(socksFormat, "SOCKS config");
  };

  const copyCredentials = (node) => {
    const credentialsFormat = `${node.ip}:${node.login}:${node.password}`;
    copyToClipboard(credentialsFormat, 'Credentials');
  };

  const downloadOvpnConfig = (node) => {
    // Generate OVPN config content
    const ovpnConfig = `client
dev tun
proto udp
remote ${node.ip} 1194
resolv-retry infinite
nobind
persist-key
persist-tun
ca ca.crt
cert client.crt
key client.key
remote-cert-tls server
auth-user-pass
comp-lzo
verb 3
auth-user-pass-stdin
auth ${node.login}
`;
    
    // Create blob and download
    const blob = new Blob([ovpnConfig], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${node.ip}_${node.login}.ovpn`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    toast.success('OVPN config downloaded!');
  };

  const startEdit = (node, field) => {
    setEditingNode(`${node.id}-${field}`);
    setEditValues({
      ...editValues,
      [`${node.id}-${field}`]: node[field] || ''
    });
  };

  const cancelEdit = () => {
    setEditingNode(null);
    setEditValues({});
  };

  const saveEdit = async (node, field) => {
    const newValue = editValues[`${node.id}-${field}`] || '';
    
    try {
      await axios.put(`${API}/nodes/${node.id}`, {
        [field]: newValue
      });
      toast.success(`${field} updated successfully`);
      onNodeUpdated();
      setEditingNode(null);
    } catch (error) {
      console.error('Error updating node:', error);
      toast.error(`Failed to update ${field}`);
    }
  };

  const deleteNode = async (nodeId) => {
    if (!window.confirm('Are you sure you want to delete this node?')) {
      return;
    }

    try {
      await axios.delete(`${API}/nodes/${nodeId}`);
      toast.success('Node deleted successfully');
      onNodeUpdated();
    } catch (error) {
      console.error('Error deleting node:', error);
      toast.error('Failed to delete node');
    }
  };

  const EditableCell = ({ node, field, className = '' }) => {
    const isEditing = editingNode === `${node.id}-${field}`;
    const value = node[field] || '';

    if (isEditing) {
      return (
        <div className={`flex items-center space-x-2 ${className}`}>
          <Input
            value={editValues[`${node.id}-${field}`] || ''}
            onChange={(e) => setEditValues({
              ...editValues,
              [`${node.id}-${field}`]: e.target.value
            })}
            className="text-xs h-8"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                saveEdit(node, field);
              } else if (e.key === 'Escape') {
                cancelEdit();
              }
            }}
          />
          <Button size="sm" variant="ghost" onClick={() => saveEdit(node, field)}>
            <Check className="h-3 w-3" />
          </Button>
          <Button size="sm" variant="ghost" onClick={cancelEdit}>
            <X className="h-3 w-3" />
          </Button>
        </div>
      );
    }

    return (
      <div 
        className={`cursor-pointer hover:bg-gray-100 p-1 rounded ${className}`}
        onClick={() => startEdit(node, field)}
        title={`Click to edit ${field}`}
      >
        {value || <span className="text-gray-400 italic">Empty</span>}
      </div>
    );
  };

  if (loading && nodes.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="text-lg font-medium">Loading nodes...</div>
        </CardContent>
      </Card>
    );
  }

  if (nodes.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="text-lg font-medium mb-2">No nodes found</div>
          <p className="text-gray-600">Add some nodes to get started or adjust your filters.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full" data-testid="nodes-table">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <Checkbox 
                  checked={selectedNodes.length === nodes.length && nodes.length > 0}
                  onCheckedChange={handleSelectAll}
                  data-testid="select-all-nodes-checkbox"
                />
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Speed
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fraud Score
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Risk Level
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                IP
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Protocol
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Login
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Password
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                SOCKS
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                OVPN
              </th>
              <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white">
            {nodes.map((node, index) => (
              <Fragment key={node.id}>
                {/* First Row: Main Information */}
                <tr className={`${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-blue-50 border-b border-gray-100`} data-testid={`node-row-${node.id}`}>
                  <td className="px-2 py-2 whitespace-nowrap" rowSpan={2}>
                    <Checkbox 
                      checked={selectedNodes.includes(node.id)}
                      onCheckedChange={() => onSelectNode(node.id)}
                      data-testid={`node-checkbox-${node.id}`}
                    />
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusBadge(node.status)}
                    </div>
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
                    {node.speed ? `${node.speed} Mbps` : '-'}
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
                    {node.scamalytics_fraud_score !== null && node.scamalytics_fraud_score !== undefined ? node.scamalytics_fraud_score : '-'}
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
                    {node.scamalytics_risk ? (
                      <Badge variant={node.scamalytics_risk === 'low' ? 'success' : node.scamalytics_risk === 'medium' ? 'warning' : 'destructive'}>
                        {node.scamalytics_risk.toUpperCase()}
                      </Badge>
                    ) : '-'}
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                    {node.ip}
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
                    <Badge variant="outline">{node.protocol?.toUpperCase() || 'PPTP'}</Badge>
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
                    {node.login}
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center space-x-1">
                      <span className="text-xs">
                        {showPasswords[node.id] ? node.password : '••••••••'}
                      </span>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        onClick={() => togglePasswordVisibility(node.id)}
                        data-testid={`toggle-password-${node.id}`}
                        className="h-6 w-6 p-0"
                      >
                        {showPasswords[node.id] ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                      </Button>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        onClick={() => copyCredentials(node)}
                        data-testid={`copy-credentials-${node.id}`}
                        className="h-6 w-6 p-0"
                        title="Copy IP:Login:Password"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => copySocks(node)}
                      data-testid={`copy-socks-${node.id}`}
                      className="text-xs px-2 py-1"
                    >
                      <Copy className="h-3 w-3 mr-1" />
                      Copy
                    </Button>
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900">
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => downloadOvpnConfig(node)}
                      data-testid={`download-ovpn-${node.id}`}
                      className="text-xs px-2 py-1"
                    >
                      <Download className="h-3 w-3 mr-1" />
                      Config
                    </Button>
                  </td>
                  <td className="px-2 py-2 whitespace-nowrap text-right text-sm font-medium">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" data-testid={`node-actions-${node.id}`}>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => testNode(node.id, 'ping')}>
                          <Activity className="h-4 w-4 mr-2" />
                          Test Ping
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => testNode(node.id, 'speed')}>
                          <Zap className="h-4 w-4 mr-2" />
                          Speed Test
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => testNode(node.id, 'geo')}>
                          <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          GEO Test
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => testNode(node.id, 'fraud')}>
                          <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          Fraud Test
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => deleteNode(node.id)}
                          className="text-red-600"
                          data-testid={`delete-node-${node.id}`}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </td>
                </tr>

                {/* Second Row: Location and Date Information */}
                <tr className={`${index % 2 === 0 ? 'bg-gray-25' : 'bg-gray-75'} text-xs text-gray-600 border-b-2 border-gray-200`}>
                  <td className="px-2 py-1 text-xs text-gray-500">
                    {formatDate(node.last_update)}
                  </td>
                  <td className="px-2 py-1 text-xs text-gray-700">
                    {node.country || 'Empty'}
                  </td>
                  <td className="px-2 py-1 text-xs text-gray-700">
                    {node.state || 'Empty'}
                  </td>
                  <td className="px-2 py-1 text-xs text-gray-700">
                    {node.city || 'Empty'}
                  </td>
                  <td className="px-2 py-1 text-xs text-gray-700">
                    {node.zipcode || 'Empty'}
                  </td>
                  <td className="px-2 py-1 text-xs text-gray-700">
                    {node.provider || 'Empty'}
                  </td>
                  <td className="px-2 py-1 text-xs text-gray-700">
                    {node.coordinates ? (
                      <div className="flex items-center space-x-1">
                        <span className="font-mono">{node.coordinates}</span>
                        <Button 
                          size="sm" 
                          variant="ghost" 
                          onClick={() => {
                            navigator.clipboard.writeText(node.coordinates);
                            toast.success('Координаты скопированы!');
                          }}
                          className="h-5 w-5 p-0"
                          title="Копировать координаты"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    ) : 'Empty'}
                  </td>
                  <td className="px-2 py-1 text-xs text-gray-900 max-w-xs truncate" colSpan={5}>
                    <EditableCell node={node} field="comment" className="max-w-xs truncate" />
                  </td>
                </tr>
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default NodesTable;
