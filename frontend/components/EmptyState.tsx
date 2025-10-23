"use client";

import React from 'react';

interface EmptyStateProps {
  icon: string;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      <div className="text-6xl mb-4">{icon}</div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 mb-6">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

export function EmptyKanbanColumn({ status }: { status: string }) {
  const getEmptyState = (status: string) => {
    switch (status) {
      case 'draft':
        return {
          icon: '📝',
          title: 'Keine Entwürfe',
          description: 'Sobald Dokumente hochgeladen werden, erscheinen sie hier als Entwürfe.'
        };
      case 'reviewed':
        return {
          icon: '👀',
          title: 'Keine geprüften Dokumente',
          description: 'Dokumente, die von Teamleitern geprüft wurden, erscheinen hier.'
        };
      case 'approved':
        return {
          icon: '✅',
          title: 'Keine freigegebenen Dokumente',
          description: 'Dokumente, die vom QM-Manager freigegeben wurden, erscheinen hier.'
        };
      case 'rejected':
        return {
          icon: '❌',
          title: 'Keine zurückgewiesenen Dokumente',
          description: 'Dokumente, die zurückgewiesen wurden, erscheinen hier zur Überarbeitung.'
        };
      default:
        return {
          icon: '📄',
          title: 'Keine Dokumente',
          description: 'Keine Dokumente in diesem Status gefunden.'
        };
    }
  };

  const emptyState = getEmptyState(status);

  return (
    <div className="text-center py-8 text-gray-500">
      <div className="text-4xl mb-3">{emptyState.icon}</div>
      <p className="text-sm font-medium text-gray-700 mb-1">{emptyState.title}</p>
      <p className="text-xs text-gray-500">{emptyState.description}</p>
    </div>
  );
}

export function EmptyDocumentsList({ onUpload }: { onUpload: () => void }) {
  return (
    <EmptyState
      icon="📭"
      title="Keine Dokumente gefunden"
      description="Laden Sie Ihr erstes Dokument hoch, um mit dem Workflow zu beginnen."
      action={{
        label: "Erstes Dokument hochladen",
        onClick: onUpload
      }}
    />
  );
}
