import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Chip,
} from '@mui/material';
import FilterableRetailerSelector from './FilterableRetailerSelector';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Inventory as InventoryIcon,
  CloudDownload as ScrapingIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  CompareArrows as CompareIcon,
  Monitor as MonitorIcon,
  TrendingUp as TrendingUpIcon,
  Store as StoreIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';

const drawerWidth = 240;

interface LayoutProps {
  children: React.ReactNode;
}

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Products', icon: <InventoryIcon />, path: '/products' },
  { text: 'Price Comparisons', icon: <CompareIcon />, path: '/price-comparisons' },
  { text: 'Scraping', icon: <ScrapingIcon />, path: '/scraping' },
  { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
  { text: 'Monitoring', icon: <MonitorIcon />, path: '/monitoring' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <div>
      <Toolbar sx={{ 
        background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
        color: 'white',
        flexDirection: 'column',
        alignItems: 'center',
        py: 1.5,
        minHeight: '80px !important'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <Avatar sx={{ 
            bgcolor: 'white', 
            color: '#1976d2',
            width: 28,
            height: 28,
            fontSize: '0.9rem'
          }}>
            <TrendingUpIcon sx={{ fontSize: '1.1rem' }} />
          </Avatar>
          <Typography variant="subtitle1" component="div" sx={{ 
            fontWeight: 700,
            fontSize: '1rem',
            textAlign: 'center',
            lineHeight: 1.2
          }}>
            TWD Price
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Typography variant="subtitle2" sx={{ 
            fontWeight: 600,
            fontSize: '0.85rem'
          }}>
            Intelligence
          </Typography>
          <Chip 
            label="Hub" 
            size="small" 
            sx={{ 
              bgcolor: 'rgba(255, 255, 255, 0.25)', 
              color: 'white',
              fontWeight: 600,
              fontSize: '0.7rem',
              height: '20px'
            }} 
          />
        </Box>
      </Toolbar>
      <Divider />
      
      {/* Retailer Selector in Sidebar */}
      <Box sx={{ p: 2 }}>
        <FilterableRetailerSelector fullWidth />
      </Box>
      <Divider />
      
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          background: 'linear-gradient(90deg, #1976d2 0%, #1565c0 50%, #0d47a1 100%)',
          boxShadow: '0 4px 20px rgba(25, 118, 210, 0.3)',
        }}
      >
        <Toolbar sx={{ minHeight: '64px !important' }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AssessmentIcon sx={{ fontSize: 28, color: '#42a5f5' }} />
              <Typography variant="h6" noWrap component="div" sx={{ 
                fontWeight: 600,
                background: 'linear-gradient(45deg, #ffffff 30%, #e3f2fd 90%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                {menuItems.find(item => item.path === location.pathname)?.text || 'TWD Price Intelligence Hub'}
              </Typography>
            </Box>
            
            <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip 
                icon={<StoreIcon sx={{ color: 'white !important' }} />}
                label="Live Data" 
                size="small" 
                sx={{ 
                  bgcolor: 'rgba(76, 175, 80, 0.8)',
                  color: 'white',
                  fontWeight: 500,
                  '& .MuiChip-icon': {
                    color: 'white'
                  }
                }} 
              />
              <Chip 
                label="Pro" 
                size="small" 
                sx={{ 
                  bgcolor: 'rgba(255, 193, 7, 0.9)',
                  color: '#1565c0',
                  fontWeight: 600
                }} 
              />
            </Box>
          </Box>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
        }}
      >
        {children}
      </Box>
    </Box>
  );
}