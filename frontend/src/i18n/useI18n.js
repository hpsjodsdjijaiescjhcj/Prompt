import { useLanguage } from '../contexts/LanguageContext';
import { t as translate } from './translations';

export function useI18n() {
  const { language, switchLanguage, isZh, isEn } = useLanguage();
  const t = (key) => translate(key, language);
  return { language, switchLanguage, isZh, isEn, t };
}
