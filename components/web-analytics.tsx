import Script from 'next/script';
// Vercel Web Analytics: page views and visitors, without cookies or personal data.
// It only records once Web Analytics is enabled for the project in Vercel (Analytics tab); until then the script is inert.
export default function WebAnalytics() {
  if (process.env.NODE_ENV !== 'production' || process.env.NEXT_PUBLIC_DISABLE_ANALYTICS === 'true') return null;
  return <>
    <Script id="va-queue" strategy="afterInteractive">{`window.va=window.va||function(){(window.vaq=window.vaq||[]).push(arguments)};`}</Script>
    <Script src="/_vercel/insights/script.js" strategy="afterInteractive"/>
  </>;
}
