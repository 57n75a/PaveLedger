import {adminClient,workspaceId} from '@/lib/store';
export const runtime='nodejs';export const dynamic='force-dynamic';

// Runs every 5 days (vercel.json) so the free Supabase database never pauses for inactivity.
// One tiny read is enough to count as activity.
export async function GET(req:Request){
 const secret=process.env.CRON_SECRET;
 if(!secret||req.headers.get('authorization')!=='Bearer '+secret)return Response.json({error:'Unauthorized'},{status:401});
 try{
  const {error}=await adminClient().from('workspaces').select('id').eq('id',workspaceId).maybeSingle();
  if(error)return Response.json({ok:false,error:'Database unavailable'},{status:503});
  return Response.json({ok:true,at:new Date().toISOString()},{headers:{'Cache-Control':'no-store'}});
 }catch{return Response.json({ok:false,error:'Database unavailable'},{status:503})}
}
