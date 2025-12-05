/**
 * Top bar component
 */
import { Fragment } from 'react';
import { Menu, MenuButton, MenuItem, MenuItems, Transition } from '@headlessui/react';
import {
  BellIcon,
  ChevronDownIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../hooks/useAuth';
import { useWorkspace } from '../../hooks/useWorkspace';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

export default function TopBar() {
  const { me, logout } = useAuth();
  const { workspaces, currentWorkspaceId, setCurrentWorkspace } = useWorkspace();

  const currentWorkspaceName =
    workspaces.data?.find((w) => w.id === currentWorkspaceId)?.name ||
    'Select Workspace';

  return (
    <div className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
      {/* Workspace selector */}
      <Menu as="div" className="relative">
        <MenuButton className="flex items-center gap-x-2 rounded-md bg-gray-100 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200">
          {currentWorkspaceName}
          <ChevronDownIcon className="h-4 w-4 text-gray-500" />
        </MenuButton>
        <Transition
          as={Fragment}
          enter="transition ease-out duration-100"
          enterFrom="transform opacity-0 scale-95"
          enterTo="transform opacity-100 scale-100"
          leave="transition ease-in duration-75"
          leaveFrom="transform opacity-100 scale-100"
          leaveTo="transform opacity-0 scale-95"
        >
          <MenuItems className="absolute left-0 z-10 mt-2 w-56 origin-top-left rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
            <div className="py-1">
              {workspaces.data?.map((workspace) => (
                <MenuItem key={workspace.id}>
                  {({ focus }) => (
                    <button
                      onClick={() => setCurrentWorkspace(workspace.id)}
                      className={classNames(
                        focus ? 'bg-gray-100' : '',
                        workspace.id === currentWorkspaceId
                          ? 'font-semibold text-indigo-600'
                          : 'text-gray-700',
                        'block w-full px-4 py-2 text-left text-sm'
                      )}
                    >
                      {workspace.name}
                    </button>
                  )}
                </MenuItem>
              ))}
            </div>
          </MenuItems>
        </Transition>
      </Menu>

      <div className="flex flex-1 items-center justify-end gap-x-4 lg:gap-x-6">
        {/* Notifications */}
        <button
          type="button"
          className="p-2 text-gray-400 hover:text-gray-500"
        >
          <span className="sr-only">View notifications</span>
          <BellIcon className="h-6 w-6" />
        </button>

        {/* Profile dropdown */}
        <Menu as="div" className="relative">
          <MenuButton className="flex items-center gap-x-2">
            <UserCircleIcon className="h-8 w-8 text-gray-400" />
            <span className="hidden text-sm font-medium text-gray-700 lg:block">
              {me.data?.full_name || me.data?.email || 'User'}
            </span>
            <ChevronDownIcon className="h-4 w-4 text-gray-500" />
          </MenuButton>
          <Transition
            as={Fragment}
            enter="transition ease-out duration-100"
            enterFrom="transform opacity-0 scale-95"
            enterTo="transform opacity-100 scale-100"
            leave="transition ease-in duration-75"
            leaveFrom="transform opacity-100 scale-100"
            leaveTo="transform opacity-0 scale-95"
          >
            <MenuItems className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
              <MenuItem>
                {({ focus }) => (
                  <a
                    href="/settings"
                    className={classNames(
                      focus ? 'bg-gray-100' : '',
                      'block px-4 py-2 text-sm text-gray-700'
                    )}
                  >
                    Settings
                  </a>
                )}
              </MenuItem>
              <MenuItem>
                {({ focus }) => (
                  <button
                    onClick={logout}
                    className={classNames(
                      focus ? 'bg-gray-100' : '',
                      'block w-full px-4 py-2 text-left text-sm text-gray-700'
                    )}
                  >
                    Sign out
                  </button>
                )}
              </MenuItem>
            </MenuItems>
          </Transition>
        </Menu>
      </div>
    </div>
  );
}
