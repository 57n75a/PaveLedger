const required=['NEXT_PUBLIC_SUPABASE_URL','NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY','SUPABASE_SECRET_KEY','OWNER_EMAIL'];
let failed=false;for(const key of required){const value=process.env[key];const ok=!!value&&!/YOUR_|example\.com/i.test(value);console.log(`${key}: ${ok?'set':'MISSING OR PLACEHOLDER'}`);if(!ok)failed=true;}
const id=process.env.WORKSPACE_ID||'municipality-pilot';if(!/^[a-z0-9-]{3,60}$/.test(id)){console.log('WORKSPACE_ID: use 3–60 lowercase letters, digits and hyphens');failed=true;}
console.log('Values are deliberately not printed. Use node --env-file=.env.local scripts/check-env.mjs for local checking.');process.exitCode=failed?1:0;
