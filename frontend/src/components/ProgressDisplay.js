import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity } from 'lucide-react';

/**
 * Унифицированный компонент отображения прогресса импорта
 * Поддерживает как chunked импорт с session_id, так и обычный импорт с прогресс-баром
 */
const ProgressDisplay = ({ 
  type = 'chunked', // 'chunked' или 'regular'
  progress = null, // Данные прогресса для chunked импорта
  regularProgress = 0, // Процент для обычного импорта (0-100)
  regularStats = { added: 0, skipped: 0, errors: 0 }, // Статистика для обычного импорта
  fileInfo = null, // Информация о файле { size, protocol }
  onMinimize = null, // Callback для сворачивания
  onCancel = null // Callback для отмены
}) => {
  // Вычисляем процент прогресса
  const percentComplete = type === 'chunked'
    ? Math.round(((progress?.processed_chunks || 0) / (progress?.total_chunks || 1)) * 100)
    : regularProgress;

  // Вычисляем статистику
  const stats = type === 'chunked'
    ? {
        added: progress?.added || 0,
        skipped: progress?.skipped || 0,
        errors: progress?.errors || 0,
        total: (progress?.added || 0) + (progress?.skipped || 0) + (progress?.errors || 0)
      }
    : {
        added: regularStats.added || 0,
        skipped: regularStats.skipped || 0,
        errors: regularStats.errors || 0,
        total: (regularStats.added || 0) + (regularStats.skipped || 0) + (regularStats.errors || 0)
      };

  // Вычисляем скорость обработки (узлов в секунду)
  const processingSpeed = type === 'chunked' && progress?.processed_chunks > 0
    ? Math.max(1, Math.round((stats.added + stats.skipped) / Math.max(1, progress.processed_chunks) * 10))
    : 0;

  // Текст текущей операции
  const currentOperation = type === 'chunked'
    ? (progress?.current_operation || 'Инициализация chunked обработки...')
    : 'Обработка и сохранение узлов в базу данных...';

  // Детали прогресса
  const progressDetails = type === 'chunked'
    ? `Обработано ${progress?.processed_chunks || 0} из ${progress?.total_chunks || 0} частей`
    : fileInfo
      ? `Файл: ${fileInfo.size || 'размер неизвестен'} | Протокол: ${fileInfo.protocol || 'pptp'}`
      : 'Файл обрабатывается напрямую';

  return (
    <Card className="border-blue-400 bg-blue-50 shadow-lg">
      <CardHeader className="pb-2 bg-blue-100 border-b border-blue-300">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold flex items-center text-blue-800">
            <Activity className="h-5 w-5 mr-2 text-blue-600" />
            {type === 'chunked' ? '📂 Chunked Import - Большой файл' : '📂 Прямая обработка файла'}
          </CardTitle>
          <div className="flex space-x-2">
            {onMinimize && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={onMinimize}
                className="bg-white hover:bg-gray-100"
              >
                📋 Свернуть в фон
              </Button>
            )}
            {onCancel && (
              <Button 
                variant="destructive" 
                size="sm" 
                onClick={onCancel}
              >
                ⏹️ Отменить
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3 pt-4">
        {/* ЦЕНТРАЛЬНЫЙ ПРОЦЕНТ */}
        <div className="text-center bg-white p-4 rounded-lg border-2 border-blue-300">
          <div className="text-5xl font-extrabold text-blue-600 mb-2">
            {percentComplete}%
          </div>
          <div className="text-lg font-semibold text-gray-700 mb-1">
            Прогресс импорта
          </div>
          <div className="text-sm text-gray-600">
            {progressDetails}
          </div>
        </div>
        
        {/* ПРОГРЕСС-БАР */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-gray-600">
            <span>
              {type === 'chunked' 
                ? `Прогресс: ${progress?.processed_chunks || 0} из ${progress?.total_chunks || 0} частей`
                : 'Прогресс обработки'
              }
            </span>
            <span>{percentComplete}%</span>
          </div>
          <div className="relative w-full bg-blue-200 rounded-full h-4 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full transition-all duration-500 ease-out flex items-center justify-end pr-2"
              style={{ 
                width: `${Math.max(percentComplete, 5)}%` 
              }}
            >
              <span className="text-xs text-white font-semibold">
                {percentComplete > 10 ? `${percentComplete}%` : ''}
              </span>
            </div>
          </div>
          
          {/* Скорость обработки */}
          {type === 'chunked' && processingSpeed > 0 && (
            <div className="text-xs text-center text-gray-500">
              🚀 Скорость: ~{processingSpeed} узлов/сек
            </div>
          )}
        </div>
        
        {/* ДЕТАЛЬНАЯ СТАТИСТИКА */}
        <div className="grid grid-cols-4 gap-2 text-sm">
          <div className="text-center p-3 bg-green-100 rounded-lg border border-green-200">
            <div className="text-xl font-bold text-green-800">
              {stats.added}
            </div>
            <div className="text-xs text-green-600">✅ Добавлено</div>
          </div>
          <div className="text-center p-3 bg-yellow-100 rounded-lg border border-yellow-200">
            <div className="text-xl font-bold text-yellow-800">
              {stats.skipped}
            </div>
            <div className="text-xs text-yellow-600">⚠️ Пропущено</div>
          </div>
          <div className="text-center p-3 bg-red-100 rounded-lg border border-red-200">
            <div className="text-xl font-bold text-red-800">
              {stats.errors}
            </div>
            <div className="text-xs text-red-600">❌ Ошибок</div>
          </div>
          <div className="text-center p-3 bg-blue-100 rounded-lg border border-blue-200">
            <div className="text-xl font-bold text-blue-800">
              {stats.total || '?'}
            </div>
            <div className="text-xs text-blue-600">📊 Всего</div>
          </div>
        </div>
        
        {/* ТЕКУЩАЯ ОПЕРАЦИЯ */}
        <div className="bg-gray-50 border border-gray-200 p-3 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">💼 Текущая операция</span>
            <span className="text-xs text-gray-500">
              {new Date().toLocaleTimeString()}
            </span>
          </div>
          <div className="text-sm text-gray-800 bg-white p-2 rounded border">
            {currentOperation}
          </div>
          
          <div className="flex items-center mt-2 space-x-2">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
            </div>
            <span className="text-xs text-blue-600 font-medium">Активная обработка</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ProgressDisplay;
