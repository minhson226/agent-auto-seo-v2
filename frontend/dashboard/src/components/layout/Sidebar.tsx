/**
 * Sidebar navigation component
 */
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  DocumentTextIcon,
  FolderIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  KeyIcon,
  RectangleStackIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Keywords', href: '/keywords', icon: KeyIcon },
  { name: 'Clustering', href: '/clustering', icon: RectangleStackIcon },
  { name: 'Content Plans', href: '/content-plans', icon: FolderIcon },
  { name: 'Articles', href: '/articles', icon: DocumentTextIcon },
  { name: 'Publishing', href: '/publishing', icon: PaperAirplaneIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

export default function Sidebar() {
  const location = useLocation();

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900">
      <div className="flex h-16 shrink-0 items-center px-6">
        <span className="text-xl font-bold text-white">Auto-SEO</span>
      </div>
      <nav className="flex flex-1 flex-col px-3 py-4">
        <ul role="list" className="flex flex-1 flex-col gap-y-1">
          {navigation.map((item) => {
            const isActive =
              location.pathname === item.href ||
              (item.href !== '/' && location.pathname.startsWith(item.href));
            return (
              <li key={item.name}>
                <Link
                  to={item.href}
                  className={classNames(
                    isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-400 hover:bg-gray-800 hover:text-white',
                    'group flex gap-x-3 rounded-md px-3 py-2 text-sm font-medium transition-colors'
                  )}
                >
                  <item.icon
                    className={classNames(
                      isActive
                        ? 'text-white'
                        : 'text-gray-400 group-hover:text-white',
                      'h-5 w-5 shrink-0'
                    )}
                  />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}
