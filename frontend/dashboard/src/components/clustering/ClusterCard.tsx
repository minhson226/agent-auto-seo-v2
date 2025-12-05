/**
 * Cluster card component for drag-drop
 */
import { useRef, useEffect } from 'react';
import { useDrop } from 'react-dnd';
import { PencilIcon, TrashIcon } from '@heroicons/react/24/outline';
import type { Keyword } from '../../api/clusters';

interface ClusterCardProps {
  id: string;
  name: string;
  keywords: Keyword[];
  onDrop: (keywordId: string, clusterId: string) => void;
  onEdit: () => void;
  onDelete: () => void;
  onRemoveKeyword: (keywordId: string) => void;
}

export default function ClusterCard({
  id,
  name,
  keywords,
  onDrop,
  onEdit,
  onDelete,
  onRemoveKeyword,
}: ClusterCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [{ isOver }, drop] = useDrop(
    () => ({
      accept: 'keyword',
      drop: (item: { id: string }) => {
        onDrop(item.id, id);
      },
      collect: (monitor) => ({
        isOver: !!monitor.isOver(),
      }),
    }),
    [id, onDrop]
  );

  useEffect(() => {
    if (ref.current) {
      drop(ref.current);
    }
  }, [drop]);

  return (
    <div
      ref={ref}
      className={`rounded-lg border bg-white p-4 transition-all ${
        isOver
          ? 'border-indigo-500 ring-2 ring-indigo-200'
          : 'border-gray-200'
      }`}
    >
      <div className="mb-3 flex items-center justify-between">
        <h4 className="font-medium text-gray-900">{name}</h4>
        <div className="flex gap-1">
          <button
            onClick={onEdit}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
          <button
            onClick={onDelete}
            className="rounded p-1 text-gray-400 hover:bg-red-100 hover:text-red-600"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
      <p className="mb-2 text-xs text-gray-500">
        {keywords.length} keyword{keywords.length !== 1 ? 's' : ''}
      </p>
      <div className="max-h-64 space-y-1 overflow-y-auto">
        {keywords.map((keyword) => (
          <div
            key={keyword.id}
            className="group flex items-center justify-between rounded bg-gray-50 px-2 py-1 text-sm"
          >
            <span className="truncate">{keyword.keyword}</span>
            <button
              onClick={() => onRemoveKeyword(keyword.id)}
              className="hidden text-gray-400 hover:text-red-500 group-hover:block"
            >
              ×
            </button>
          </div>
        ))}
        {keywords.length === 0 && (
          <p className="py-4 text-center text-xs text-gray-400">
            Drop keywords here
          </p>
        )}
      </div>
    </div>
  );
}
