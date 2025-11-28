/**
 * RAG Feedback Button
 * 
 * Button-Komponente zum Abgeben von Feedback für RAG Chat-Antworten.
 * PHASE 4.1: User Feedback System.
 */

"use client";

import { useState, useEffect } from 'react';
import { ThumbsUp, ThumbsDown, MessageSquare, Check, X } from 'lucide-react';
import { submitFeedback, getFeedbackForMessage, FeedbackResponse } from '@/lib/api/rag';
import toast from 'react-hot-toast';

interface RAGFeedbackButtonProps {
  messageId: number;
  onFeedbackSubmitted?: () => void;
}

export default function RAGFeedbackButton({
  messageId,
  onFeedbackSubmitted
}: RAGFeedbackButtonProps) {
  const [currentFeedback, setCurrentFeedback] = useState<FeedbackResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCommentInput, setShowCommentInput] = useState(false);
  const [comment, setComment] = useState('');
  const [selectedRating, setSelectedRating] = useState<'positive' | 'negative' | 'neutral' | null>(null);

  useEffect(() => {
    loadExistingFeedback();
  }, [messageId]);

  const loadExistingFeedback = async () => {
    try {
      const feedback = await getFeedbackForMessage(messageId);
      if (feedback) {
        setCurrentFeedback(feedback);
        setSelectedRating(feedback.rating as 'positive' | 'negative' | 'neutral');
        setComment(feedback.comment || '');
      }
    } catch (error) {
      // Ignoriere Fehler (Feedback existiert möglicherweise nicht)
      console.debug('No existing feedback found');
    }
  };

  const handleRatingClick = async (rating: 'positive' | 'negative' | 'neutral') => {
    if (currentFeedback) {
      // Feedback bereits vorhanden - zeige Info
      toast('Du hast bereits Feedback für diese Nachricht abgegeben', { icon: 'ℹ️' });
      return;
    }

    setSelectedRating(rating);
    
    // NEU v2.10.1: Speichere Feedback sofort ohne Kommentar (optional)
    // User kann später noch einen Kommentar hinzufügen, aber Feedback wird direkt gespeichert
    await submitFeedbackInternal(rating, null);
  };

  const submitFeedbackInternal = async (rating: 'positive' | 'negative' | 'neutral', commentText: string | null) => {
    setLoading(true);
    try {
      const feedback = await submitFeedback({
        chat_message_id: messageId,
        rating: rating,
        comment: commentText
      });

      setCurrentFeedback(feedback);
      setShowCommentInput(false);
      toast.success('✅ Feedback erfolgreich abgegeben!');
      
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }
    } catch (error: any) {
      console.error('Failed to submit feedback:', error);
      toast.error(`❌ Fehler: ${error.message || 'Feedback konnte nicht gespeichert werden'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedRating) return;
    
    await submitFeedbackInternal(selectedRating, comment.trim() || null);
  };

  const handleCancel = () => {
    setShowCommentInput(false);
    setSelectedRating(null);
    setComment('');
  };

  // Wenn Feedback bereits vorhanden, zeige Status und Kommentar
  if (currentFeedback) {
    return (
      <div className="mt-2 space-y-2">
        <div className="flex items-center gap-2 text-xs text-gray-600">
          {currentFeedback.rating === 'positive' && (
            <>
              <ThumbsUp className="w-4 h-4 text-green-600" />
              <span className="text-green-600">Positives Feedback abgegeben</span>
            </>
          )}
          {currentFeedback.rating === 'negative' && (
            <>
              <ThumbsDown className="w-4 h-4 text-red-600" />
              <span className="text-red-600">Negatives Feedback abgegeben</span>
            </>
          )}
          {currentFeedback.rating === 'neutral' && (
            <>
              <MessageSquare className="w-4 h-4 text-gray-600" />
              <span className="text-gray-600">Neutrales Feedback abgegeben</span>
            </>
          )}
        </div>
        {currentFeedback.comment && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-2 text-xs text-gray-700">
            <span className="font-medium">Dein Kommentar:</span> {currentFeedback.comment}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="mt-2">
      {!showCommentInput ? (
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600 mr-1">War diese Antwort hilfreich?</span>
          <button
            onClick={() => handleRatingClick('positive')}
            disabled={loading}
            className="p-1.5 text-green-600 hover:bg-green-50 rounded-md transition-colors disabled:opacity-50"
            title="Positives Feedback"
          >
            <ThumbsUp className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleRatingClick('negative')}
            disabled={loading}
            className="p-1.5 text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50"
            title="Negatives Feedback"
          >
            <ThumbsDown className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleRatingClick('neutral')}
            disabled={loading}
            className="p-1.5 text-gray-600 hover:bg-gray-50 rounded-md transition-colors disabled:opacity-50"
            title="Neutrales Feedback"
          >
            <MessageSquare className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-medium text-gray-700">
              {selectedRating === 'positive' && '✅ Positives Feedback gespeichert! Optional: Kommentar hinzufügen'}
              {selectedRating === 'negative' && '❌ Negatives Feedback gespeichert! Optional: Kommentar hinzufügen'}
              {selectedRating === 'neutral' && '💬 Neutrales Feedback gespeichert! Optional: Kommentar hinzufügen'}
            </span>
          </div>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Optional: Kommentar hinzufügen..."
            className="w-full text-xs border border-gray-300 rounded-md px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            maxLength={2000}
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">
              {comment.length}/2000 Zeichen
            </span>
            <div className="flex items-center gap-2">
              {comment.trim() && (
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-1"
                >
                  <Check className="w-3 h-3" />
                  Kommentar speichern
                </button>
              )}
              <button
                onClick={() => {
                  setShowCommentInput(false);
                  setComment('');
                }}
                disabled={loading}
                className="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
              >
                <X className="w-3 h-3" />
                Schließen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

