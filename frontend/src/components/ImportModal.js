import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Upload } from 'lucide-react';
import axios from 'axios';

const ImportModal = ({ isOpen, onClose, onImportComplete }) => {
  const { API } = useAuth();
  const [loading, setLoading] = useState(false);
  const [importData, setImportData] = useState('');
  const [protocol, setProtocol] = useState('pptp');
  const [previewResult, setPreviewResult] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  React.useEffect(() => {
    if (isOpen) {
      setImportData('');
      setProtocol('pptp');
      setPreviewResult(null);
      setShowPreview(false);
    }
  }, [isOpen]);

  const addSampleText = () => {
    const sampleTexts = {
      pptp: `Format 1 - Key-value pairs:
Ip: 144.229.29.35
Login: admin
Pass: admin
State: California
City: Los Angeles
Zip: 90035
---------------------
Format 2 - Single line with spaces (IP Pass Login State):
76.178.64.46 admin admin CA
96.234.52.227 admin admin NJ
---------------------
Format 3 - Dash/pipe format:
68.227.241.4 - admin:admin - Arizona/Phoenix 85001 | 2025-09-03 16:05:25
96.42.187.97 - 1:1 - Michigan/Lapeer 48446 | 2025-09-03 09:50:22
---------------------
Format 4 - Colon separated:
70.171.218.52:admin:admin:US:Arizona:85001
---------------------
Format 5 - Multi-line with Location:
IP: 24.227.222.13
Credentials: admin:admin
Location: Texas (Austin)
ZIP: 78701
---------------------
Format 6 - With PPTP header (first 2 lines ignored):
> PPTP_SVOIM_VPN:
🚨 PPTP Connection
IP: 24.227.222.13
Credentials: admin:admin
Location: Texas (Austin)
ZIP: 78701`,
      ssh: `192.168.1.100:root:password123:US:New York:10001
10.0.0.50 secret456 admin CA`,
      socks: `proxy1.example.com:1080:user:pass:US:California:90210
proxy2.example.com:1080:user2:pass2:GB:London:`,
      server: `server1.example.com admin password US
server2.example.com root secret CA`,
      ovpn: `vpn1.example.com:1194:client1:pass123:US:Florida:33101
vpn2.example.com:443:client2:pass456:GB:London:`
    };
    setImportData(sampleTexts[protocol] || sampleTexts.pptp);
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      setImportData(e.target.result);
      toast.success('File loaded successfully');
    };
    reader.onerror = () => {
      toast.error('Failed to read file');
    };
    reader.readAsText(file);
  };

  const handleImport = async () => {
    if (!importData.trim()) {
      toast.error('Please enter or upload data to import');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/nodes/import`, {
        data: importData,
        protocol
      });
      
      if (response.data.success) {
        const report = response.data.report;
        setPreviewResult(report);
        setShowPreview(true);
        
        // Show detailed toast notification
        let message = `Import complete: ${report.added} added`;
        if (report.skipped_duplicates > 0) message += `, ${report.skipped_duplicates} duplicates`;
        if (report.replaced_old > 0) message += `, ${report.replaced_old} replaced`;
        if (report.queued_for_verification > 0) message += `, ${report.queued_for_verification} queued`;
        if (report.format_errors > 0) message += `, ${report.format_errors} format errors`;
        
        toast.success(message);
        onImportComplete(report);
      } else {
        toast.error(response.data.message || 'Import failed');
      }
    } catch (error) {
      console.error('Error importing:', error);
      const errorMsg = error.response?.data?.message || 'Failed to import data';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto" data-testid="import-modal">
        <DialogHeader>
          <DialogTitle>Import Nodes</DialogTitle>
          <DialogDescription>
            Import nodes from text data. Supports multiple formats (A-G) as per TZ requirements.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Protocol Selection */}
          <div className="space-y-2">
            <Label htmlFor="import-protocol">Protocol Type</Label>
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

          {/* Import Data */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="import-data">Import Data</Label>
              <div className="flex space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addSampleText}
                  data-testid="add-sample-text-btn"
                >
                  Add Sample Text
                </Button>
                <Label htmlFor="file-upload" className="cursor-pointer">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    asChild
                    data-testid="upload-file-btn"
                  >
                    <span>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload File
                    </span>
                  </Button>
                </Label>
                <input
                  id="file-upload"
                  type="file"
                  accept=".txt,.csv"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>
            </div>
            <Textarea
              id="import-data"
              value={importData}
              onChange={(e) => setImportData(e.target.value)}
              placeholder="Paste your node data here or upload a file..."
              rows={12}
              className="font-mono text-sm"
              data-testid="import-data-textarea"
            />
          </div>

          {/* Supported Formats Help */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Supported Import Formats</CardTitle>
            </CardHeader>
            <CardContent className="text-xs space-y-2">
              <div><strong>Format A:</strong> Key-value pairs (Ip: xxx, Login: xxx, Pass: xxx)</div>
              <div><strong>Format B:</strong> Space separated (IP login pass state_code)</div>
              <div><strong>Format C:</strong> Dash/pipe format (IP - login:pass - State/City ZIP | date)</div>
              <div><strong>Format D:</strong> Colon separated (IP:login:pass:country:state:zip)</div>
              <div><strong>Format E/F:</strong> Multi-line with Location: State (City)</div>
              <div><strong>Format G:</strong> Minimal (IP login pass)</div>
            </CardContent>
          </Card>

          {/* Preview Results */}
          {showPreview && previewResult && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Import Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-xl font-bold text-green-600">{previewResult.added || 0}</div>
                    <div className="text-xs text-gray-600">Added</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-yellow-600">{previewResult.skipped_duplicates || 0}</div>
                    <div className="text-xs text-gray-600">Duplicates</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-blue-600">{previewResult.replaced_old || 0}</div>
                    <div className="text-xs text-gray-600">Replaced</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-purple-600">{previewResult.queued_for_verification || 0}</div>
                    <div className="text-xs text-gray-600">Queued</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-red-600">{previewResult.format_errors || 0}</div>
                    <div className="text-xs text-gray-600">Format Errors</div>
                  </div>
                </div>
                
                {previewResult.processing_errors > 0 && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
                    <h4 className="font-medium text-red-600 mb-2">Processing Errors: {previewResult.processing_errors}</h4>
                    <div className="text-xs text-red-600">
                      Check the Format Error log for details.
                    </div>
                  </div>
                )}
                
                <div className="mt-4 text-xs text-gray-600">
                  <strong>Summary:</strong> Processed {previewResult.total_processed} blocks, successfully parsed {previewResult.successfully_parsed}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            onClick={handleImport}
            disabled={loading || !importData.trim()}
            data-testid="import-btn"
          >
            {loading ? 'Importing...' : 'Import Nodes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ImportModal;
