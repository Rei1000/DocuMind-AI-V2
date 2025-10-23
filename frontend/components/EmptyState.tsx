"use client";

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export default function EmptyState({ 
  icon, 
  title, 
  description, 
  action 
}: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      <div className="text-gray-400 mb-4 text-6xl">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {title}
      </h3>
      <p className="text-sm text-gray-500 mb-6 max-w-sm mx-auto">
        {description}
      </p>
      {action && (
        <div className="flex justify-center">
          {action}
        </div>
      )}
    </div>
  );
}

// Predefined Empty States
export function EmptyDocumentsState() {
  return (
    <EmptyState
      icon="📄"
      title="Keine Dokumente gefunden"
      description="Es wurden keine Dokumente in diesem Status gefunden. Laden Sie ein neues Dokument hoch oder ändern Sie die Filter."
    />
  );
}

export function EmptySearchState() {
  return (
    <EmptyState
      icon="🔍"
      title="Keine Ergebnisse"
      description="Ihre Suche ergab keine Treffer. Versuchen Sie andere Suchbegriffe oder ändern Sie die Filter."
    />
  );
}

export function EmptyWorkflowState() {
  return (
    <EmptyState
      icon="⚡"
      title="Workflow leer"
      description="Alle Dokumente wurden bearbeitet. Neue Dokumente erscheinen hier, sobald sie hochgeladen werden."
    />
  );
}
