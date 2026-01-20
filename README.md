# rtls-stream-visualizer
Real Time Location System Stream Visualizer

# Архитектура приложения
## Описание компонентов
**stream_generator** -- CLI утилита, которая по заданным параметрам (IP, Port, скорость отправки сообщений, JSONL path) будет отправлять UDP датаграммы, состоящие из отдельных JSON, полученных из JSONL файла

**stream_handler** -- модуль приема и обработки UDP потока, который:
- Принимает UDP-пакеты
- Парсит и преобразовывает пакеты в нормализованные события
- Производит валидацию координат, корректности timestamp
- Обрабатывает дубликаты и out-of-order сообщения
- Маршрутизирует события в модуль визуализации
- Логгирует события, ошибки

**vizualizator_2d** -- модуль визуализации 2-х мерной сцены, который будет отображать все полученные события в соответствии с их timestamp, предоставляя возможность останавливать / возобновлять / ускорять воспроизведение

### Observability
**OpenTelemetry** -- инструментирование приложения для сбора трейсов и метрик со всех компонентов

**Prometheus** -- хранение и агрегация метрик (количество обработанных пакетов, ошибки валидации, latency и т.д.)

**Grafana** -- визуализация метрик и трейсов, дашборды для мониторинга состояния системы

## Схема взаимодействия
```mermaid
sequenceDiagram
  participant sg as StreamGenerator
  participant sh as StreamHandler
  participant v2d as Vizualizator2D
  participant otel as OpenTelemetry Collector
  participant prom as Prometheus
  participant graf as Grafana

  Note over sg: Чтение JSONL файла
  
  loop Для каждой JSON записи
    sg->>sh: UDP датаграмма (JSON)
    sg-->>otel: Trace span (отправка)
    
    activate sh
    sh-->>otel: Trace span (обработка)
    sh->>sh: Парсинг JSON
    
    alt Валидация успешна
      sh->>sh: Нормализация события
      sh->>sh: Проверка дубликатов/порядка
      sh->>v2d: Нормализованное событие
      activate v2d
      v2d-->>otel: Trace span (визуализация)
      v2d->>v2d: Отображение на 2D сцене
      deactivate v2d
    else Ошибка валидации
      sh->>sh: Логгирование ошибки
      sh-->>otel: Error span
    end
    deactivate sh
  end

  Note over v2d: Управление воспроизведением<br/>(пауза/возобновление/ускорение)

  Note over otel,graf: Сбор и экспорт телеметрии
  
  otel->>prom: Метрики (OTLP/Prometheus)
  otel->>graf: Трейсы (Tempo/Jaeger)
  
  loop Периодически
    prom->>graf: Scrape метрик
  end
  
  Note over graf: Дашборды и алерты
```
