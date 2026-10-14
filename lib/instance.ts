// One codebase, one profile per country. The deployment chooses it with NEXT_PUBLIC_INSTANCE (rs or ca).
// Everything that differs between the Serbian and Canadian demos lives here.
export type Lang = 'sr' | 'sr-cyrl' | 'en' | 'fr';
export type InstanceId = 'rs' | 'ca';

export type Instance = {
  id: InstanceId;
  /** Full brand shown in titles and the sign-in screen. */
  brand: string;
  logo: string;
  /** Default sidebar slogan (English source text, translated on display). */
  slogan: string;
  languages: Lang[];
  defaultLang: Lang;
  /** Locale for dates and numbers per language. */
  locales: Record<Lang, string | undefined>;
  currency: string;
  /** Contract address country used as the default in forms. */
  country: 'SRB' | 'CAN';
  /** ISO code used to limit address search to this country. */
  geocodeCountry: 'rs' | 'ca';
  /** Bounding box for address search: west, south, east, north. */
  bbox: [number, number, number, number];
  mapCenter: {lat: number; lng: number};
  /** Examples shown in address and coordinate fields. */
  examples: {address: string; street: string; coords: string};
  /** Demo pack loaded by default. */
  demoPack: 'serbia' | 'canada';
  /** How the concept page talks about the market and pricing. */
  market: {name: string; pricing: 'cad' | 'eur'};
  /** Emergency number shown on the public report form. */
  emergency: string;
  /** Title and description for search engines and the browser tab, per language. */
  meta: Partial<Record<Lang, {title: string; description: string}>>;
};

export const INSTANCES: Record<InstanceId, Instance> = {
  rs: {
    id: 'rs', brand: 'PaveLedger Srbija', logo: '/logo.png', slogan: 'Municipal pilot workspace',
    languages: ['sr', 'sr-cyrl', 'en'], defaultLang: 'sr', locales: {sr: 'sr-Latn-RS', 'sr-cyrl': 'sr-Cyrl-RS', en: 'en-GB', fr: 'fr-FR'},
    currency: 'RSD', country: 'SRB', geocodeCountry: 'rs', bbox: [18.81, 42.23, 23.01, 46.19], mapCenter: {lat: 44.0165, lng: 21.0059},
    examples: {address: 'Knez Mihailova 10, 11000 Beograd', street: 'Knez Mihailova', coords: '44.818700, 20.457300'},
    demoPack: 'serbia', emergency: '192', market: {name: 'Serbian', pricing: 'eur'},
    meta: {
      sr: {title: 'PaveLedger Srbija | Inteligencija puteva', description: 'Prijave za bezbednost puteva i odgovornost za popravke. Privatna demonstracija.'},
      en: {title: 'PaveLedger Serbia | Road intelligence', description: 'Road safety tickets and repair accountability. Private demonstration.'},
    },
  },
  ca: {
    id: 'ca', brand: 'PaveLedger Canada', logo: '/logo-ca.svg', slogan: 'Municipal pilot workspace',
    languages: ['en', 'fr'], defaultLang: 'en', locales: {en: 'en-CA', fr: 'fr-CA', sr: 'sr-Latn-RS', 'sr-cyrl': 'sr-Cyrl-RS'},
    currency: 'CAD', country: 'CAN', geocodeCountry: 'ca', bbox: [-141.01, 41.68, -52.62, 83.11], mapCenter: {lat: 43.4643, lng: -80.5204},
    examples: {address: '200 King Street West, Kitchener, ON N2G 4V6', street: 'King Street West', coords: '43.451600, -80.492500'},
    demoPack: 'canada', emergency: '911', market: {name: 'Canadian', pricing: 'cad'},
    meta: {
      en: {title: 'PaveLedger Canada | Road intelligence', description: 'Road safety tickets and repair accountability. Private demonstration.'},
      fr: {title: 'PaveLedger Canada | Intelligence routière', description: 'Signalements de sécurité routière et responsabilité des réparations. Démonstration privée.'},
    },
  },
};

const chosen = (process.env.NEXT_PUBLIC_INSTANCE || 'rs').trim().toLowerCase();
/** The profile for this deployment. Serbia is the default, so existing deployments keep working unchanged. */
export const instance: Instance = INSTANCES[(chosen === 'ca' ? 'ca' : 'rs') as InstanceId];
