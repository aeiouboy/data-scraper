# Price Tracking Dashboard

## Overview

The Price Tracking Dashboard is a comprehensive React component integrated into the Price Comparisons page that provides real-time insights into cross-retailer product matching and price tracking.

## Features

### 1. **Match Overview Tab**
- **Confidence Distribution**: Visual breakdown of match confidence levels (High/Medium/Low)
- **Manual Review Stats**: Track accuracy of matching algorithm through user confirmations
- **Real-time Analytics**: View total products matched, average price variance, and retailer coverage

### 2. **Price Trends Tab**
- **Historical Price Visualization**: Area charts showing price trends for matched products
- **Savings Opportunities Chart**: Visual representation of top savings opportunities
- **Cross-retailer Price Comparison**: Track price changes across different retailers

### 3. **Savings Opportunities Tab**
- **Top Savings Cards**: Detailed cards showing products with highest savings potential
- **Price Variance Indicators**: Color-coded variance percentages
- **Best Retailer Identification**: Instantly see which retailer offers the best price

### 4. **Manual Review Tab**
- **Product Match Verification**: Review and confirm/reject suggested matches
- **Confidence Score Display**: See detailed matching metrics
- **Learning System**: Help improve the algorithm by providing feedback

## Key Components

### Action Buttons
1. **Process New Products**: Queue unmatched products for automatic matching
2. **Test Product Match**: Test the matching algorithm with sample products
3. **Refresh Analytics**: Update dashboard with latest data

### Test Match Dialog
- Enter two product names (Thai or English)
- Optional brand information
- Real-time matching results with detailed breakdown
- Shows normalized text for debugging

### Match Review Dialog
- Review suggested matches for selected products
- One-click confirm or reject matches
- Detailed match metrics (name similarity, brand match, SKU match, spec match)

## Technical Implementation

### API Integration
```typescript
// New matching APIs added to services/api.ts
export const matchingApi = {
  testMatch: (data) => api.post('/matching/test-match', data),
  processNewProducts: (params) => api.post('/matching/process-new-products', null, { params }),
  getMatchSuggestions: (productId, minConfidence) => api.get(`/matching/match-suggestions/${productId}`),
  confirmMatch: (data) => api.post('/matching/confirm-match', data),
  getAnalytics: () => api.get('/matching/analytics'),
};
```

### Component Structure
- Built with Material-UI components
- Uses React Query for data fetching and caching
- Recharts for data visualization
- TypeScript for type safety

## Usage

1. **Enable Multi-Retailer Mode**: The dashboard requires data from multiple retailers
2. **Process Products**: Click "Process New Products" to start matching
3. **Review Matches**: Use the Manual Review tab to verify matches
4. **Monitor Performance**: Track matching accuracy and savings opportunities

## Metrics Displayed

- **Total Products Matched**: Count of successfully matched products across retailers
- **Average Price Variance**: Percentage difference in prices for same products
- **Match Accuracy**: Percentage of correct matches based on manual reviews
- **Retailers Covered**: Number of retailers in the matching system

## Color Coding

- 🟢 **Green**: High confidence matches (90%+), best prices
- 🟡 **Yellow**: Medium confidence matches (70-90%), moderate savings
- 🔴 **Red**: Low confidence matches (<70%), high price variance

## Next Steps

1. **Historical Data**: Implement price history tracking over time
2. **Alerts**: Set up notifications for significant price drops
3. **Export**: Add functionality to export savings reports
4. **Bulk Actions**: Enable bulk confirmation of matches
5. **Advanced Filters**: Add more filtering options for savings opportunities