import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { getAllAnalyses, getSettings } from '../../services/api';
import './TrendsView.css';

function TrendsView() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBrand, setSelectedBrand] = useState('');
  const [compareTo, setCompareTo] = useState('GROUP_AVERAGE');
  const [selectedMetric, setSelectedMetric] = useState('omzet_index');
  const [availableBrands, setAvailableBrands] = useState([]);
  const [trendData, setTrendData] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (analyses.length > 0 && selectedBrand) {
      calculateTrends();
    }
  }, [analyses, selectedBrand, compareTo, selectedMetric]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [analysesData, settingsData] = await Promise.all([
        getAllAnalyses(),
        getSettings()
      ]);
      
      // Sort by year and week number (ascending for time series)
      const sorted = analysesData.sort((a, b) => {
        const yearA = parseInt(a.year);
        const yearB = parseInt(b.year);
        if (yearA !== yearB) return yearA - yearB;
        return parseInt(a.week_number) - parseInt(b.week_number);
      });
      setAnalyses(sorted);
      
      // Extract available brands
      const brandsSet = new Set();
      sorted.forEach(analysis => {
        if (analysis.brands_data) {
          Object.keys(analysis.brands_data).forEach(brand => {
            brandsSet.add(brand);
          });
        }
      });
      const brandsList = Array.from(brandsSet).sort();
      setAvailableBrands(brandsList);
      
      // Set defaults from settings
      const defaultBrand = settingsData?.brand_analyzer?.default_trend_brand || brandsList[0] || '';
      const defaultComp = settingsData?.brand_analyzer?.default_comparison || 'GROUP_AVERAGE';
      setSelectedBrand(defaultBrand);
      setCompareTo(defaultComp);
      
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const parseValue = (value) => {
    if (!value) return 0;
    // Remove % signs and convert to float
    const cleanValue = String(value).replace('%', '').replace('€', '').trim();
    return parseFloat(cleanValue) || 0;
  };

  const calculateTrends = () => {
    const primaryData = [];
    const comparisonData = [];
    
    analyses.forEach(analysis => {
      // Include year in label for clarity
      const weekLabel = `W${analysis.week_number}'${String(analysis.year).slice(-2)}`;
      
      // Primary brand data
      const brandData = analysis.brands_data?.[selectedBrand] || {};
      primaryData.push({
        week: weekLabel,
        weekNum: parseInt(analysis.week_number),
        year: parseInt(analysis.year),
        value: parseValue(brandData[selectedMetric]),
        label: selectedBrand
      });
      
      // Comparison data
      if (compareTo === 'GROUP_AVERAGE') {
        const groupData = analysis.group_average || {};
        comparisonData.push({
          week: weekLabel,
          weekNum: parseInt(analysis.week_number),
          year: parseInt(analysis.year),
          value: parseValue(groupData[selectedMetric]),
          label: 'Group Average'
        });
      } else {
        const compBrandData = analysis.brands_data?.[compareTo] || {};
        comparisonData.push({
          week: weekLabel,
          weekNum: parseInt(analysis.week_number),
          year: parseInt(analysis.year),
          value: parseValue(compBrandData[selectedMetric]),
          label: compareTo
        });
      }
    });
    
    setTrendData({ primary: primaryData, comparison: comparisonData });
  };

  const getMetricLabel = (metric) => {
    const labels = {
      'omzet_index': 'Omzet Index',
      'dvk': 'Doorverkoop %',
      'rent': 'Rentabiliteit',
      'marge': 'Marge %',
      'os': 'OS (Voorraadrotatie)'
    };
    return labels[metric] || metric;
  };

  const getMetricUnit = (metric) => {
    const units = {
      'omzet_index': '',
      'dvk': '%',
      'rent': '€',
      'marge': '%',
      'os': ''
    };
    return units[metric] || '';
  };

  const calculateStats = (data) => {
    if (!data || data.length === 0) return null;
    
    const values = data.map(d => d.value);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const latest = values[values.length - 1];
    const previous = values.length > 1 ? values[values.length - 2] : latest;
    const change = latest - previous;
    const changePercent = previous !== 0 ? ((change / previous) * 100) : 0;
    
    return { avg, min, max, latest, change, changePercent };
  };

  const renderChart = () => {
    if (!trendData.primary || trendData.primary.length === 0) {
      return <div className="no-data">No data available for selected filters</div>;
    }

    const primaryStats = calculateStats(trendData.primary);
    const comparisonStats = calculateStats(trendData.comparison);
    
    // Calculate chart bounds
    const allValues = [
      ...trendData.primary.map(d => d.value),
      ...trendData.comparison.map(d => d.value)
    ];
    const maxValue = Math.max(...allValues);
    const minValue = Math.min(...allValues);
    const range = maxValue - minValue || 1;
    const chartHeight = 300;
    const padding = 40;

    return (
      <div className="chart-container">
        <div className="chart-stats-row">
          <div className="stats-group">
            <h4 className="stats-group-title">{selectedBrand}</h4>
            <div className="chart-stats">
              <div className="stat-card">
                <div className="stat-label">Latest</div>
                <div className="stat-value">
                  {primaryStats.latest.toFixed(2)}{getMetricUnit(selectedMetric)}
                </div>
                <div className={`stat-change ${primaryStats.change >= 0 ? 'positive' : 'negative'}`}>
                  {primaryStats.change >= 0 ? '↑' : '↓'} {Math.abs(primaryStats.changePercent).toFixed(1)}%
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Average</div>
                <div className="stat-value">
                  {primaryStats.avg.toFixed(2)}{getMetricUnit(selectedMetric)}
                </div>
              </div>
            </div>
          </div>

          <div className="stats-group">
            <h4 className="stats-group-title">{compareTo === 'GROUP_AVERAGE' ? 'Group Average' : compareTo}</h4>
            <div className="chart-stats">
              <div className="stat-card">
                <div className="stat-label">Latest</div>
                <div className="stat-value">
                  {comparisonStats.latest.toFixed(2)}{getMetricUnit(selectedMetric)}
                </div>
                <div className={`stat-change ${comparisonStats.change >= 0 ? 'positive' : 'negative'}`}>
                  {comparisonStats.change >= 0 ? '↑' : '↓'} {Math.abs(comparisonStats.changePercent).toFixed(1)}%
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Average</div>
                <div className="stat-value">
                  {comparisonStats.avg.toFixed(2)}{getMetricUnit(selectedMetric)}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="chart-area">
          <svg width="100%" height={chartHeight} className="line-chart">
            {/* Grid lines */}
            {[0, 1, 2, 3, 4].map(i => {
              const y = padding + (chartHeight - 2 * padding) * (i / 4);
              const value = maxValue - (range * (i / 4));
              return (
                <g key={i}>
                  <line
                    x1="5%"
                    y1={y}
                    x2="95%"
                    y2={y}
                    stroke="#e0e0e0"
                    strokeWidth="1"
                  />
                  <text
                    x="3%"
                    y={y + 5}
                    textAnchor="end"
                    fontSize="12"
                    fill="#666"
                  >
                    {value.toFixed(1)}
                  </text>
                </g>
              );
            })}

            {/* Primary line */}
            <g>
              {trendData.primary.map((point, index) => {
                const totalPoints = trendData.primary.length;
                const chartWidth = 85; // percentage
                const chartStart = 8; // start from left
                // For single point, center it. For multiple, spread evenly
                const x = totalPoints === 1 
                  ? chartStart + (chartWidth / 2)
                  : chartStart + (index / (totalPoints - 1)) * chartWidth;
                const y = padding + ((maxValue - point.value) / range) * (chartHeight - 2 * padding);
                const xPercent = `${x}%`;
                
                return (
                  <g key={`primary-${index}`}>
                    {/* Line to next point */}
                    {index < totalPoints - 1 && (() => {
                      const nextPoint = trendData.primary[index + 1];
                      const nextX = chartStart + ((index + 1) / (totalPoints - 1)) * chartWidth;
                      const nextY = padding + ((maxValue - nextPoint.value) / range) * (chartHeight - 2 * padding);
                      return (
                        <line
                          x1={xPercent}
                          y1={y}
                          x2={`${nextX}%`}
                          y2={nextY}
                          stroke="#000000"
                          strokeWidth="2"
                        />
                      );
                    })()}
                    
                    {/* Point */}
                    <circle
                      cx={xPercent}
                      cy={y}
                      r="5"
                      fill="#000000"
                      className="chart-point"
                    >
                      <title>{`${selectedBrand} ${point.week}: ${point.value.toFixed(2)}${getMetricUnit(selectedMetric)}`}</title>
                    </circle>
                    
                    {/* Week label - show all labels for better clarity */}
                    <text
                      x={xPercent}
                      y={chartHeight - 10}
                      textAnchor="middle"
                      fontSize="11"
                      fill="#666"
                    >
                      {point.week}
                    </text>
                  </g>
                );
              })}
            </g>

            {/* Comparison line */}
            <g>
              {trendData.comparison.map((point, index) => {
                const totalPoints = trendData.comparison.length;
                const chartWidth = 85; // percentage
                const chartStart = 8; // start from left
                // For single point, center it. For multiple, spread evenly
                const x = totalPoints === 1 
                  ? chartStart + (chartWidth / 2)
                  : chartStart + (index / (totalPoints - 1)) * chartWidth;
                const y = padding + ((maxValue - point.value) / range) * (chartHeight - 2 * padding);
                const xPercent = `${x}%`;
                
                return (
                  <g key={`comparison-${index}`}>
                    {/* Line to next point */}
                    {index < totalPoints - 1 && (() => {
                      const nextPoint = trendData.comparison[index + 1];
                      const nextX = chartStart + ((index + 1) / (totalPoints - 1)) * chartWidth;
                      const nextY = padding + ((maxValue - nextPoint.value) / range) * (chartHeight - 2 * padding);
                      return (
                        <line
                          x1={xPercent}
                          y1={y}
                          x2={`${nextX}%`}
                          y2={nextY}
                          stroke="#999999"
                          strokeWidth="2"
                          strokeDasharray="5,5"
                        />
                      );
                    })()}
                    
                    {/* Point */}
                    <circle
                      cx={xPercent}
                      cy={y}
                      r="4"
                      fill="#999999"
                      className="chart-point"
                    >
                      <title>{`${point.label} ${point.week}: ${point.value.toFixed(2)}${getMetricUnit(selectedMetric)}`}</title>
                    </circle>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>

        <div className="chart-legend">
          <div className="legend-item">
            <div className="legend-line solid"></div>
            <span>{selectedBrand}</span>
          </div>
          <div className="legend-item">
            <div className="legend-line dashed"></div>
            <span>{compareTo === 'GROUP_AVERAGE' ? 'Group Average' : compareTo}</span>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="trends-view">
        <div className="loading-message">Loading trend data...</div>
      </div>
    );
  }

  if (analyses.length < 2) {
    return (
      <div className="trends-view">
        <div className="empty-state">
          <h2>Not Enough Data</h2>
          <p>Upload at least 2 analyses to see trends over time.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="trends-view">
      <div className="trends-header">
        <h2 className="trends-title">Performance Trends</h2>
        <p className="trends-subtitle">
          Track and compare metrics across {analyses.length} weeks of data
        </p>
      </div>

      <div className="trends-filters">
        <div className="filter-group">
          <label className="filter-label">Brand</label>
          <select
            value={selectedBrand}
            onChange={(e) => setSelectedBrand(e.target.value)}
            className="filter-select"
          >
            {availableBrands.map(brand => (
              <option key={brand} value={brand}>{brand}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">Compare To</label>
          <select
            value={compareTo}
            onChange={(e) => setCompareTo(e.target.value)}
            className="filter-select"
          >
            <option value="GROUP_AVERAGE">Group Average</option>
            {availableBrands.filter(b => b !== selectedBrand).map(brand => (
              <option key={brand} value={brand}>{brand}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">Metric</label>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="filter-select"
          >
            <option value="omzet_index">Omzet Index</option>
            <option value="dvk">Doorverkoop %</option>
            <option value="rent">Rentabiliteit</option>
            <option value="marge">Marge %</option>
            <option value="os">OS (Voorraadrotatie)</option>
          </select>
        </div>
      </div>

      <div className="trends-content">
        <h3 className="chart-title">
          {getMetricLabel(selectedMetric)} Comparison
        </h3>
        {renderChart()}
      </div>
    </div>
  );
}

export default TrendsView;
