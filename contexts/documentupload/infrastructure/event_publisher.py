"""
Infrastructure Layer: Event Publisher Implementation.

NEU Phase 5: InMemoryEventPublisher für Event-Driven Architecture.

Implementiert das EventPublisher Protocol und ermöglicht Event-basierte
Kommunikation zwischen Contexts ohne direkte Abhängigkeiten.

WICHTIG: Für Production sollte eine Message Queue verwendet werden
(z.B. RabbitMQ, Redis, Apache Kafka).
"""

from typing import Dict, List, Any, Callable
import asyncio
import logging

logger = logging.getLogger(__name__)


class InMemoryEventPublisher:
    """
    In-Memory Event Publisher Implementation.
    
    Verwaltet Handler-Registrierung und Event-Routing synchron.
    Für asynchrone Verarbeitung kann eine Queue ergänzt werden.
    
    Attributes:
        _handlers: Dictionary von Event-Typ zu Handler-Liste
    """
    
    def __init__(self):
        """Initialisiere Event Publisher."""
        self._handlers: Dict[type, List[Callable]] = {}
    
    def subscribe(self, event_type: type, handler: Callable) -> None:
        """
        Registriere Handler für Event-Typ.
        
        Args:
            event_type: Event-Klasse (z.B. DocumentRejectedEvent)
            handler: Handler-Instanz mit handle(event) Methode
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler {handler.__class__.__name__} für {event_type.__name__} registriert")
    
    async def publish(self, event: Any) -> None:
        """
        Publiziere Event an alle registrierten Handler.
        
        Args:
            event: Domain Event Instanz
        
        WICHTIG: Handler-Fehler werden isoliert. Ein fehlgeschlagener Handler
        blockiert andere Handler nicht.
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"Keine Handler für {event_type.__name__} registriert")
            return
        
        logger.info(f"Publiziere {event_type.__name__} an {len(handlers)} Handler(s)")
        
        # Rufe alle Handler auf (mit Fehler-Isolation)
        for handler in handlers:
            try:
                await handler.handle(event)
                logger.debug(f"Handler {handler.__class__.__name__} erfolgreich ausgeführt")
            except Exception as e:
                # Fehler-Isolation: Ein Handler-Fehler blockiert andere nicht
                logger.error(
                    f"Handler {handler.__class__.__name__} fehlgeschlagen für "
                    f"{event_type.__name__}: {str(e)}",
                    exc_info=True
                )
                # Weitermachen mit anderen Handlern
    
    def unsubscribe(self, event_type: type, handler: Callable) -> None:
        """
        Entferne Handler-Registrierung.
        
        Args:
            event_type: Event-Klasse
            handler: Handler-Instanz
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Handler {handler.__class__.__name__} für {event_type.__name__} entfernt")
            except ValueError:
                logger.warning(f"Handler {handler.__class__.__name__} war nicht registriert")
    
    def get_handler_count(self, event_type: type) -> int:
        """
        Hole Anzahl registrierter Handler für Event-Typ.
        
        Args:
            event_type: Event-Klasse
            
        Returns:
            Anzahl Handler
        """
        return len(self._handlers.get(event_type, []))

