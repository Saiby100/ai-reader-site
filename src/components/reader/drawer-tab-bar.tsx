'use client';

type DrawerTabBarProps = {
  /** Currently active tab id */
  activeTab: string;
  /** Callback when a tab is selected */
  onTabChange: (tab: string) => void;
};

const TABS = [{ id: 'notes', label: 'Notes' }];

export const DrawerTabBar = ({ activeTab, onTabChange }: DrawerTabBarProps) => {
  return (
    <div className="flex border-b border-gray-200 dark:border-gray-800">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === tab.id
              ? 'border-b-2 border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};