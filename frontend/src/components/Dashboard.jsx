// Dashboard.jsx
import React from 'react';
import OverviewMetrics from './panels/OverviewMetrics';
import SentimentTrend from './panels/SentimentTrend';
import TopicDistribution from './panels/TopicDistribution';
import NarrativeShift from './panels/NarrativeShift';
import MisinfoAlerts from './panels/MisinfoAlerts';
import LatestArticles from './panels/LatestArticles';
import SourceSentiment from './panels/SourceSentiment';
import TrendingKeywords from './panels/TrendingKeywords';
import TopEntities from './panels/TopEntities';

export default function Dashboard() {
  return (
    <div className="max-w-[1600px] mx-auto p-4 sm:p-6 space-y-6 mt-20 pb-12">
      {/* Grid Layout Container */}
      <div className="grid grid-cols-12 gap-6">
        {/* Row 1 */}
        <OverviewMetrics />

        {/* Row 2 */}
        <SentimentTrend />
        <TopicDistribution />

        {/* Row 3 */}
        <NarrativeShift />
        <MisinfoAlerts />

        {/* Row 4 */}
        <LatestArticles />
        <SourceSentiment />

        {/* Row 5 */}
        <TrendingKeywords />
        <TopEntities />
      </div>
    </div>
  );
}