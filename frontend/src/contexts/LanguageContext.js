import React, { createContext, useState, useCallback } from 'react';

export const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('tf_language') || 'zh';
  });

  const switchLanguage = useCallback((lang) => {
    setLanguage(lang);
    localStorage.setItem('tf_language', lang);
  }, []);

  const value = {
    language,
    switchLanguage,
    isZh: language === 'zh',
    isEn: language === 'en',
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = React.useContext(LanguageContext);
  if (!ctx) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return ctx;
}
