/**
 * Schedule types for monitoring automation
 */

export enum ScheduleType {
  INTERVAL = 'interval',
  CRON = 'cron'
}

export enum TaskType {
  CATEGORY_MONITOR = 'category_monitor',
  PRODUCT_SCRAPE = 'product_scrape',
  PRICE_UPDATE = 'price_update',
  INVENTORY_CHECK = 'inventory_check'
}

export enum ScheduleStatus {
  SUCCESS = 'success',
  FAILURE = 'failure',
  RUNNING = 'running'
}

export interface IntervalSchedule {
  days?: number;
  hours?: number;
  minutes?: number;
  seconds?: number;
}

export interface CronSchedule {
  minute: string;
  hour: string;
  day_of_week: string;
  day_of_month: string;
  month_of_year: string;
}

export interface MonitoringSchedule {
  id?: string;
  task_name: string;
  task_type: TaskType;
  description?: string;
  schedule_type: ScheduleType;
  schedule_value: IntervalSchedule | CronSchedule | Record<string, any>;
  task_params: Record<string, any>;
  enabled: boolean;
  last_run?: string;
  next_run?: string;
  last_status?: ScheduleStatus;
  last_error?: string;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
}

export interface ScheduleResponse extends MonitoringSchedule {
  is_overdue: boolean;
  run_count: number;
  success_rate: number;
}

export interface ScheduleHistory {
  id: string;
  schedule_id: string;
  started_at: string;
  completed_at?: string;
  status: ScheduleStatus;
  result?: Record<string, any>;
  error_message?: string;
  duration_seconds?: number;
  items_processed?: number;
  items_failed?: number;
  created_at: string;
}

export interface ScheduleCreate {
  task_name: string;
  task_type: TaskType;
  description?: string;
  schedule_type: ScheduleType;
  schedule_value: IntervalSchedule | CronSchedule | Record<string, any>;
  task_params?: Record<string, any>;
  enabled?: boolean;
}

export interface ScheduleUpdate {
  description?: string;
  schedule_type?: ScheduleType;
  schedule_value?: IntervalSchedule | CronSchedule | Record<string, any>;
  task_params?: Record<string, any>;
  enabled?: boolean;
}

export interface ScheduleStats {
  total_schedules: number;
  enabled_schedules: number;
  disabled_schedules: number;
  schedules_by_type: Record<TaskType, number>;
  recent_runs: {
    total: number;
    successful: number;
    failed: number;
    running: number;
  };
  average_duration_seconds: number;
  next_scheduled_runs: Array<{
    task_name: string;
    task_type: TaskType;
    next_run: string;
  }>;
}

// Helper functions
export const getTaskTypeLabel = (taskType: TaskType): string => {
  switch (taskType) {
    case TaskType.CATEGORY_MONITOR:
      return 'Category Monitoring';
    case TaskType.PRODUCT_SCRAPE:
      return 'Product Scraping';
    case TaskType.PRICE_UPDATE:
      return 'Price Update';
    case TaskType.INVENTORY_CHECK:
      return 'Inventory Check';
    default:
      return taskType;
  }
};

export const getScheduleTypeLabel = (scheduleType: ScheduleType): string => {
  switch (scheduleType) {
    case ScheduleType.INTERVAL:
      return 'Interval';
    case ScheduleType.CRON:
      return 'Cron Expression';
    default:
      return scheduleType;
  }
};

export const formatInterval = (interval: IntervalSchedule): string => {
  const parts = [];
  if (interval.days) parts.push(`${interval.days} day${interval.days > 1 ? 's' : ''}`);
  if (interval.hours) parts.push(`${interval.hours} hour${interval.hours > 1 ? 's' : ''}`);
  if (interval.minutes) parts.push(`${interval.minutes} minute${interval.minutes > 1 ? 's' : ''}`);
  if (interval.seconds) parts.push(`${interval.seconds} second${interval.seconds > 1 ? 's' : ''}`);
  return parts.join(', ') || 'No interval';
};

export const formatCron = (cron: CronSchedule): string => {
  return `${cron.minute} ${cron.hour} ${cron.day_of_month} ${cron.month_of_year} ${cron.day_of_week}`;
};

export const getStatusColor = (status: ScheduleStatus): 'success' | 'error' | 'warning' | 'info' => {
  switch (status) {
    case ScheduleStatus.SUCCESS:
      return 'success';
    case ScheduleStatus.FAILURE:
      return 'error';
    case ScheduleStatus.RUNNING:
      return 'info';
    default:
      return 'warning';
  }
};