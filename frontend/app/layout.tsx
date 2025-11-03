import type { Metadata } from 'next'
import { Open_Sans } from 'next/font/google'
import './globals.css'
import Navigation from './components/Navigation'
import { Toaster } from 'react-hot-toast'
import { UserProvider } from '@/lib/contexts/UserContext'

const openSans = Open_Sans({ 
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'DocuMind-AI | Medical Knowledge Management',
  description: 'Professional Quality Management System for Healthcare - ISO 13485 Compliant',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de">
      <body className={openSans.className}>
        {/* RBAC Phase 4: UserProvider für Navigation-Filtering */}
        <UserProvider>
          {/* Gradient Background on ALL Pages - Dashboard Style */}
          <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-50">
            <Navigation />
            <main>
              {children}
            </main>
            <Toaster 
              position="top-right"
              containerStyle={{
                pointerEvents: 'none',
              }}
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                  pointerEvents: 'auto',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#4ade80',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </div>
          {/* Fix für blockierendes Overlay - DEBOUNCED um Endlosschleife zu vermeiden */}
          <script
            dangerouslySetInnerHTML={{
              __html: `
              (function() {
                let isFixing = false;
                let fixTimeout = null;
                const fixedElements = new WeakSet();
                
                function fixBlockingOverlay() {
                  if (isFixing) return; // Verhindere gleichzeitige Ausführung
                  isFixing = true;
                  
                  try {
                    // Finde alle DIVs mit hohem z-index und fixed position
                    const allDivs = document.querySelectorAll('div');
                    allDivs.forEach(div => {
                      // Skip wenn bereits gefixt
                      if (fixedElements.has(div)) return;
                      
                      const style = window.getComputedStyle(div);
                      const zIndex = parseInt(style.zIndex) || 0;
                      const position = style.position;
                      
                      // Prüfe ob es ein blockierendes Overlay ist
                      if (zIndex >= 9999 && (position === 'fixed' || position === 'absolute')) {
                        // Setze pointer-events: none auf Container - KRITISCH!
                        if (div.style.pointerEvents !== 'none') {
                          div.style.setProperty('pointer-events', 'none', 'important');
                          fixedElements.add(div);
                        }
                        
                        // Setze pointer-events: auto auf direkte Kinder (Toasts)
                        Array.from(div.children).forEach(child => {
                          if (child.style.pointerEvents !== 'auto') {
                            child.style.setProperty('pointer-events', 'auto', 'important');
                          }
                        });
                        
                        // Auch auf alle Nachfahren, die Toasts sein könnten
                        div.querySelectorAll('[role="status"], [role="alert"]').forEach(toast => {
                          toast.style.setProperty('pointer-events', 'auto', 'important');
                        });
                      }
                    });
                  } finally {
                    isFixing = false;
                  }
                }
                
                // Debounced version
                function debouncedFix() {
                  if (fixTimeout) clearTimeout(fixTimeout);
                  fixTimeout = setTimeout(fixBlockingOverlay, 100);
                }
                
                // Sofort ausführen (nur einmal)
                fixBlockingOverlay();
                
                // Nach DOMContentLoaded (nur einmal)
                if (document.readyState === 'loading') {
                  document.addEventListener('DOMContentLoaded', () => {
                    setTimeout(fixBlockingOverlay, 100);
                  }, { once: true });
                }
                
                // MutationObserver mit Debounce (verhindert Endlosschleife)
                const observer = new MutationObserver(() => {
                  debouncedFix(); // DEBOUNCED!
                });
                observer.observe(document.body, {
                  childList: true,
                  subtree: true,
                  attributes: true,
                  attributeFilter: ['style', 'class']
                });
              })();
            `,
            }}
          />
        </UserProvider>
      </body>
    </html>
  )
}
