/**
 * Toast Notification Service
 * 
 * Zentrale Toast-Funktionen für Workflow-Notifications
 */

import toast from 'react-hot-toast';

export const WorkflowToast = {
  /**
   * Erfolgreiche Status-Änderung
   */
  statusChanged: (documentName: string, fromStatus: string, toStatus: string) => {
    toast.success(
      `✅ Dokument "${documentName}" von "${fromStatus}" zu "${toStatus}" verschoben`,
      {
        duration: 4000,
        icon: '✅',
      }
    );
  },

  /**
   * Fehler bei Status-Änderung
   */
  statusChangeError: (error: string) => {
    toast.error(
      `❌ Status-Änderung fehlgeschlagen: ${error}`,
      {
        duration: 5000,
        icon: '❌',
      }
    );
  },

  /**
   * Keine Berechtigung
   */
  permissionDenied: (action: string) => {
    toast.error(
      `🚫 Keine Berechtigung für: ${action}`,
      {
        duration: 4000,
        icon: '🚫',
      }
    );
  },

  /**
   * Workflow-Historie aktualisiert
   */
  historyUpdated: () => {
    toast.success(
      'ℹ️ Workflow-Historie aktualisiert',
      {
        duration: 3000,
        icon: 'ℹ️',
      }
    );
  },

  /**
   * Dokument gelöscht
   */
  documentDeleted: (documentName: string) => {
    toast.success(
      `🗑️ Dokument "${documentName}" gelöscht`,
      {
        duration: 3000,
        icon: '🗑️',
      }
    );
  },

  /**
   * Dokument hochgeladen
   */
  documentUploaded: (documentName: string) => {
    toast.success(
      `📤 Dokument "${documentName}" erfolgreich hochgeladen`,
      {
        duration: 3000,
        icon: '📤',
      }
    );
  },

  /**
   * Version-Duplikat-Warning
   */
  versionDuplicate: (version: string, documentType: string) => {
    toast(
      `⚠️ Version "${version}" existiert bereits für "${documentType}"`,
      {
        duration: 6000,
        icon: '⚠️',
        style: {
          background: '#F59E0B',
          color: '#fff',
        },
      }
    );
  },

  /**
   * Loading-Status
   */
  loading: (message: string) => {
    return toast.loading(message, {
      duration: Infinity,
    });
  },

  /**
   * Loading beenden
   */
  dismiss: (toastId: string) => {
    toast.dismiss(toastId);
  },

  /**
   * Generischer Erfolg
   */
  success: (message: string) => {
    toast.success(message, {
      duration: 3000,
    });
  },

  /**
   * Generischer Fehler
   */
  error: (message: string) => {
    toast.error(message, {
      duration: 5000,
    });
  },

  /**
   * Generische Info
   */
  info: (message: string) => {
    toast(message, {
      duration: 4000,
      icon: 'ℹ️',
    });
  }
};
