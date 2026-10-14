// Server-side wording for emails, in the deployment's default language. Keys are the English text.
import {sr} from './i18n-sr.ts';
import {fr} from './i18n-fr.ts';
import {instance} from './instance.ts';

const DICT: Record<string, Record<string, string>> = {sr, fr};
export function serverTx(key: string, args: string[] = []): string {
  const text = DICT[instance.defaultLang]?.[key] ?? key;
  return text.replace(/\{(\d+)\}/g, (_, i) => args[Number(i)] ?? '');
}
