"use client";

export default function DocumentSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-6 w-6 bg-gray-200 rounded"></div>
        </div>
        
        {/* Content */}
        <div className="space-y-2 mb-3">
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          <div className="h-3 bg-gray-200 rounded w-2/3"></div>
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="h-3 bg-gray-200 rounded w-1/4"></div>
          <div className="h-6 bg-gray-200 rounded w-16"></div>
        </div>
      </div>
    </div>
  );
}

export function DocumentSkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, index) => (
        <DocumentSkeleton key={index} />
      ))}
    </div>
  );
}
