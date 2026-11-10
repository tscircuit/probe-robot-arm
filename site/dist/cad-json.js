/** Lossless gzip transport keeps the CAD geometry unchanged. */
export async function loadCadJSON(url, compressed=false) {
  const response=await fetch(url+(compressed?'.gz':''));
  if(!response.ok)throw Error('CAD asset unavailable: '+url);
  if(!compressed)return response.json();
  const bytes=new Uint8Array(await response.arrayBuffer());
  // Also accept hosts that already decoded Content-Encoding: gzip.
  if(bytes[0]===0x1f&&bytes[1]===0x8b)return new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
  return JSON.parse(new TextDecoder().decode(bytes));
}
export const sharedRadialParts=new Set(['R_Structural_mounting_lid','R_Adjustable_six-bearing_base','R_Hollow_triangular_carriage','R_Printed_20_mm_lead_screw_with_integral_shaft_clamp']);
