'use client';
import type jsPDF from 'jspdf';
// jsPDF's built-in fonts cannot draw č, ć, đ. Load Liberation Sans (SIL OFL) on demand.
let pdfFontData:Promise<[string,string]>|null=null;
export async function pdfFonts(doc:jsPDF){const b64=async(u:string)=>{const r=await fetch(u);if(!r.ok)throw new Error('font');const bytes=new Uint8Array(await r.arrayBuffer());let s='';for(let i=0;i<bytes.length;i+=0x8000)s+=String.fromCharCode(...bytes.subarray(i,i+0x8000));return btoa(s)};pdfFontData??=Promise.all([b64('/fonts/LiberationSans-Regular.ttf'),b64('/fonts/LiberationSans-Bold.ttf')]);let reg:string,bold:string;try{[reg,bold]=await pdfFontData}catch(e){pdfFontData=null;throw e}doc.addFileToVFS('LiberationSans-Regular.ttf',reg);doc.addFont('LiberationSans-Regular.ttf','LiberationSans','normal');doc.addFileToVFS('LiberationSans-Bold.ttf',bold);doc.addFont('LiberationSans-Bold.ttf','LiberationSans','bold');doc.setFont('LiberationSans','normal')}
