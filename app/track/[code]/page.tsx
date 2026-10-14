import PublicTrack from '@/components/public-track';

export default async function TrackCode({params}: {params: Promise<{code: string}>}) {
  const {code} = await params;
  return <PublicTrack initialCode={decodeURIComponent(code)}/>;
}
