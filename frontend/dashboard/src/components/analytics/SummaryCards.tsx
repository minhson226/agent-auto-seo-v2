/**
 * Summary cards component for analytics
 */
import {
  ArrowUpIcon,
  ArrowDownIcon,
  EyeIcon,
  CursorArrowRaysIcon,
  ChartBarIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

interface SummaryCardsProps {
  totalImpressions: number;
  totalClicks: number;
  avgPosition: number;
  articlesRanking?: number;
  previousPeriod?: {
    totalImpressions: number;
    totalClicks: number;
    avgPosition: number;
    articlesRanking: number;
  };
}

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

function getChangeInfo(
  current: number,
  previous?: number,
  isPosition: boolean = false
) {
  if (previous === undefined) return null;

  const change = ((current - previous) / previous) * 100;
  // For position, lower is better
  const isPositive = isPosition ? change < 0 : change > 0;
  const displayChange = Math.abs(change);

  return {
    isPositive,
    value: displayChange,
  };
}

export default function SummaryCards({
  totalImpressions,
  totalClicks,
  avgPosition,
  previousPeriod,
}: SummaryCardsProps) {
  const ctr =
    totalImpressions > 0 ? (totalClicks / totalImpressions) * 100 : 0;
  const previousCtr =
    previousPeriod && previousPeriod.totalImpressions > 0
      ? (previousPeriod.totalClicks / previousPeriod.totalImpressions) * 100
      : undefined;

  const stats = [
    {
      name: 'Total Impressions',
      value: formatNumber(totalImpressions),
      icon: EyeIcon,
      change: getChangeInfo(totalImpressions, previousPeriod?.totalImpressions),
    },
    {
      name: 'Total Clicks',
      value: formatNumber(totalClicks),
      icon: CursorArrowRaysIcon,
      change: getChangeInfo(totalClicks, previousPeriod?.totalClicks),
    },
    {
      name: 'Average Position',
      value: avgPosition.toFixed(1),
      icon: ChartBarIcon,
      change: getChangeInfo(avgPosition, previousPeriod?.avgPosition, true),
    },
    {
      name: 'CTR',
      value: ctr.toFixed(2) + '%',
      icon: DocumentTextIcon,
      change: getChangeInfo(ctr, previousCtr),
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.name}
          className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <stat.icon className="h-6 w-6 text-gray-400" />
            </div>
            <div className="ml-4 flex-1">
              <p className="text-sm font-medium text-gray-500">{stat.name}</p>
              <div className="flex items-baseline">
                <p className="text-2xl font-semibold text-gray-900">
                  {stat.value}
                </p>
                {stat.change && (
                  <span
                    className={`ml-2 flex items-baseline text-sm font-medium ${
                      stat.change.isPositive
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {stat.change.isPositive ? (
                      <ArrowUpIcon className="h-3 w-3 flex-shrink-0 self-center" />
                    ) : (
                      <ArrowDownIcon className="h-3 w-3 flex-shrink-0 self-center" />
                    )}
                    {stat.change.value.toFixed(1)}%
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
