import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Download } from 'lucide-react';
import axios from 'axios';

const ExportModal = ({ isOpen, onClose, selectedNodeIds }) => {
  const { API } = useAuth();
  const [loading, setLoading] = useState(false);
  const [exportFormat, setExportFormat] = useState('txt');
  const [exportFields, setExportFields] = useState({
    ip: true,
    login: true,
    password: true,
    protocol: true,
    provider: true,
    country: true,
    state: true,
    city: true,
    zipcode: true,
    comment: true
  });

  const handleFieldToggle = (field) => {
    setExportFields(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const selectAllFields = () => {
    const allSelected = Object.values(exportFields).every(Boolean);
    const newState = !allSelected;
    
    setExportFields({
      ip: newState,
      login: newState,
      password: newState,
      protocol: newState,
      provider: newState,
      country: newState,
      state: newState,
      city: newState,
      zipcode: newState,
      comment: newState
    });
  };

  const handleExport = async () => {
    if (!selectedNodeIds.length) {
      toast.error('No nodes selected for export');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/export`, {
        node_ids: selectedNodeIds,
        format: exportFormat
      });

      const { data, filename } = response.data;
      
      // Create and download file
      const blob = new Blob([data], { 
        type: exportFormat === 'csv' ? 'text/csv' : 'text/plain' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast.success(`Exported ${selectedNodeIds.length} nodes successfully!`);
      onClose();
    } catch (error) {
      console.error('Error exporting nodes:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to export nodes';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const getPreviewFormat = () => {
    switch (exportFormat) {
      case 'csv':
        return 'IP,Login,Password,Protocol,Provider,Country,State,City,ZIP,Comment';
      case 'socks':
        return 'IP:1080:Login:Password';
      default:
        return 'IP Login Password Country';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]" data-testid="export-modal">
        <DialogHeader>
          <DialogTitle>Export Selected Nodes</DialogTitle>
          <DialogDescription>
            Export {selectedNodeIds.length} selected nodes in your preferred format.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Export Format */}
          <div className="space-y-2">
            <Label htmlFor="export-format">Export Format</Label>
            <Select value={exportFormat} onValueChange={setExportFormat}>
              <SelectTrigger data-testid="export-format-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="txt">TXT (Space separated)</SelectItem>
                <SelectItem value="csv">CSV (Comma separated)</SelectItem>
                <SelectItem value="socks">SOCKS (ip:port:login:pass)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Format Preview */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Format Preview</CardTitle>
            </CardHeader>
            <CardContent>
              <code className="text-xs bg-gray-100 p-2 rounded block">
                {getPreviewFormat()}
              </code>
            </CardContent>
          </Card>

          {/* Field Selection (only for TXT and CSV) */}
          {exportFormat !== 'socks' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center justify-between">
                  Fields to Export
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={selectAllFields}
                    data-testid="select-all-fields-btn"
                  >
                    {Object.values(exportFields).every(Boolean) ? 'Deselect All' : 'Select All'}
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(exportFields).map(([field, checked]) => (
                    <div key={field} className="flex items-center space-x-2">
                      <Checkbox
                        id={`field-${field}`}
                        checked={checked}
                        onCheckedChange={() => handleFieldToggle(field)}
                        data-testid={`export-field-${field}`}
                      />
                      <Label htmlFor={`field-${field}`} className="text-sm capitalize">
                        {field === 'zipcode' ? 'ZIP Code' : field}
                      </Label>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Export Summary */}
          <div className="text-sm text-gray-600">
            Ready to export <strong>{selectedNodeIds.length}</strong> nodes in <strong>{exportFormat.toUpperCase()}</strong> format.
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            onClick={handleExport}
            disabled={loading || selectedNodeIds.length === 0}
            data-testid="export-download-btn"
          >
            <Download className="h-4 w-4 mr-2" />
            {loading ? 'Exporting...' : 'Download Export'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ExportModal;
