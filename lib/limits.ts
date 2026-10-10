// Request size limits for the workspace API. Most requests are small JSON; actions that carry an image may be larger.
export const MAX_BODY=32_768;
export const MAX_IMAGE_BODY=1_000_000;
export const IMAGE_ACTIONS=['selfProfile','branding','teamUpdate','contract','contractUpdate'];
export function bodyTooLarge(bytes:number,action:unknown):boolean{return bytes>MAX_IMAGE_BODY||(bytes>MAX_BODY&&!IMAGE_ACTIONS.includes(String(action)))}
