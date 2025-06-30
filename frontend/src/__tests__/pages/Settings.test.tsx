import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import Settings from '../../pages/Settings';
import * as api from '../../services/api';
import { ScheduleType, TaskType } from '../../types/schedule';

jest.mock('../../services/api');

const mockConfig = {
  scraping_enabled: true,
  max_concurrent_jobs: 5,
  default_max_pages: 10,
  rate_limit_delay: 5,
  current_environment: 'development',
  environments: ['development', 'staging', 'production'],
};

const mockSchedules = [
  {
    id: '1',
    task_name: 'category_monitor_all',
    task_type: TaskType.CATEGORY_MONITOR,
    description: 'Monitor all retailer categories',
    schedule_type: ScheduleType.INTERVAL,
    schedule_value: { hours: 6 },
    task_params: {},
    enabled: true,
    last_run: '2023-12-01T10:00:00Z',
    next_run: '2023-12-01T16:00:00Z',
    last_status: 'success',
    is_overdue: false,
    run_count: 10,
    success_rate: 90,
  },
  {
    id: '2',
    task_name: 'daily_price_update',
    task_type: TaskType.PRICE_UPDATE,
    description: 'Update product prices daily',
    schedule_type: ScheduleType.CRON,
    schedule_value: { minute: '0', hour: '2' },
    task_params: {},
    enabled: false,
    last_run: null,
    next_run: null,
    last_status: null,
    is_overdue: false,
    run_count: 0,
    success_rate: 0,
  },
];

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return {
    user: userEvent.setup(),
    ...render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          {component}
        </BrowserRouter>
      </QueryClientProvider>
    ),
  };
};

describe('Settings Page', () => {
  beforeEach(() => {
    (api.configApi.get as jest.Mock).mockResolvedValue({
      data: mockConfig,
    });
    (api.configApi.update as jest.Mock).mockResolvedValue({});
    (api.configApi.reset as jest.Mock).mockResolvedValue({});
    (api.scheduleApi.getAll as jest.Mock).mockResolvedValue({
      data: mockSchedules,
    });
    (api.scheduleApi.create as jest.Mock).mockResolvedValue({});
    (api.scheduleApi.update as jest.Mock).mockResolvedValue({});
    (api.scheduleApi.toggle as jest.Mock).mockResolvedValue({});
    (api.scheduleApi.delete as jest.Mock).mockResolvedValue({});
    (api.scheduleApi.runNow as jest.Mock).mockResolvedValue({});
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('General Settings Tab', () => {
    it('should render settings page with title', () => {
      renderWithProviders(<Settings />);
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('should display current configuration values', async () => {
      renderWithProviders(<Settings />);

      await waitFor(() => {
        expect(screen.getByDisplayValue('5')).toBeInTheDocument();
        expect(screen.getByDisplayValue('10')).toBeInTheDocument();
      });
    });

    it('should update configuration values', async () => {
      const { user } = renderWithProviders(<Settings />);

      await waitFor(() => {
        expect(screen.getByLabelText('Max Concurrent Jobs')).toBeInTheDocument();
      });

      const maxJobsInput = screen.getByLabelText('Max Concurrent Jobs');
      await user.clear(maxJobsInput);
      await user.type(maxJobsInput, '8');

      const saveButton = screen.getByText('Save Settings');
      await user.click(saveButton);

      expect(api.configApi.update).toHaveBeenCalledWith({
        scraping_enabled: true,
        max_concurrent_jobs: 8,
        default_max_pages: 10,
        rate_limit_delay: 5,
      });
    });

    it('should toggle scraping enabled', async () => {
      const { user } = renderWithProviders(<Settings />);

      await waitFor(() => {
        expect(screen.getByLabelText('Enable Scraping')).toBeInTheDocument();
      });

      const enableSwitch = screen.getByLabelText('Enable Scraping');
      await user.click(enableSwitch);

      const saveButton = screen.getByText('Save Settings');
      await user.click(saveButton);

      expect(api.configApi.update).toHaveBeenCalledWith(
        expect.objectContaining({
          scraping_enabled: false,
        })
      );
    });

    it('should show success message after saving', async () => {
      const { user } = renderWithProviders(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Save Settings')).toBeInTheDocument();
      });

      const saveButton = screen.getByText('Save Settings');
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText('Settings saved successfully!')).toBeInTheDocument();
      });
    });

    it('should reset to defaults when reset button clicked', async () => {
      const { user } = renderWithProviders(<Settings />);
      
      // Mock window.location.reload
      delete (window as any).location;
      window.location = { reload: jest.fn() } as any;

      await waitFor(() => {
        expect(screen.getByText('Reset to Defaults')).toBeInTheDocument();
      });

      const resetButton = screen.getByText('Reset to Defaults');
      await user.click(resetButton);

      expect(api.configApi.reset).toHaveBeenCalled();
    });
  });

  describe('Schedules Tab', () => {
    it('should switch to schedules tab', async () => {
      const { user } = renderWithProviders(<Settings />);

      const schedulesTab = screen.getByText('Schedules');
      await user.click(schedulesTab);

      await waitFor(() => {
        expect(screen.getByText('Monitoring Schedules')).toBeInTheDocument();
      });
    });

    it('should display schedule list', async () => {
      const { user } = renderWithProviders(<Settings />);

      const schedulesTab = screen.getByText('Schedules');
      await user.click(schedulesTab);

      await waitFor(() => {
        expect(screen.getByText('category_monitor_all')).toBeInTheDocument();
        expect(screen.getByText('daily_price_update')).toBeInTheDocument();
      });
    });

    it('should toggle schedule enabled status', async () => {
      const { user } = renderWithProviders(<Settings />);

      const schedulesTab = screen.getByText('Schedules');
      await user.click(schedulesTab);

      await waitFor(() => {
        expect(screen.getByText('category_monitor_all')).toBeInTheDocument();
      });

      const switches = screen.getAllByRole('checkbox');
      const firstScheduleSwitch = switches[0];
      await user.click(firstScheduleSwitch);

      expect(api.scheduleApi.toggle).toHaveBeenCalledWith('1', false);
    });

    it('should open add schedule dialog', async () => {
      const { user } = renderWithProviders(<Settings />);

      const schedulesTab = screen.getByText('Schedules');
      await user.click(schedulesTab);

      await waitFor(() => {
        expect(screen.getByText('Add Schedule')).toBeInTheDocument();
      });

      const addButton = screen.getByText('Add Schedule');
      await user.click(addButton);

      expect(screen.getByText('Create Schedule')).toBeInTheDocument();
    });

    it('should create new schedule', async () => {
      const { user } = renderWithProviders(<Settings />);

      const schedulesTab = screen.getByText('Schedules');
      await user.click(schedulesTab);

      const addButton = screen.getByText('Add Schedule');
      await user.click(addButton);

      const taskNameInput = screen.getByLabelText('Task Name');
      await user.type(taskNameInput, 'test_schedule');

      const descriptionInput = screen.getByLabelText('Description');
      await user.type(descriptionInput, 'Test schedule description');

      const createButton = screen.getByText('Create');
      await user.click(createButton);

      expect(api.scheduleApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          task_name: 'test_schedule',
          description: 'Test schedule description',
        })
      );
    });

    it('should run schedule immediately', async () => {
      const { user } = renderWithProviders(<Settings />);

      const schedulesTab = screen.getByText('Schedules');
      await user.click(schedulesTab);

      await waitFor(() => {
        expect(screen.getByText('category_monitor_all')).toBeInTheDocument();
      });

      const runButtons = screen.getAllByLabelText('Run Now');
      await user.click(runButtons[0]);

      expect(api.scheduleApi.runNow).toHaveBeenCalledWith('1');
    });

    it('should delete schedule with confirmation', async () => {
      const { user } = renderWithProviders(<Settings />);
      window.confirm = jest.fn().mockReturnValue(true);

      const schedulesTab = screen.getByText('Schedules');
      await user.click(schedulesTab);

      await waitFor(() => {
        expect(screen.getByText('category_monitor_all')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByLabelText('Delete');
      await user.click(deleteButtons[0]);

      expect(window.confirm).toHaveBeenCalledWith(
        'Are you sure you want to delete this schedule?'
      );
      expect(api.scheduleApi.delete).toHaveBeenCalledWith('1');
    });

    it('should edit existing schedule', async () => {
      const { user } = renderWithProviders(<Settings />);

      const schedulesTab = screen.getByText('Schedules');
      await user.click(schedulesTab);

      await waitFor(() => {
        expect(screen.getByText('category_monitor_all')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByLabelText('Edit');
      await user.click(editButtons[0]);

      expect(screen.getByText('Update Schedule')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Monitor all retailer categories')).toBeInTheDocument();
    });
  });
});