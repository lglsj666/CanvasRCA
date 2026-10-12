import type {Page} from 'playwright';
import path from 'node:path';
import fs from 'node:fs/promises';
// Audit-only measurement after the diagnostic pixels are saved. The interior
// fill of a graph node is the same fixed panel color, not evidence ink. Keep
// its outline, text, all data marks and arrows. Remove HTML backing colors.
export async function cardForegroundAudit(page:Page,out:string){
  await page.addStyleTag({content:'*{background-color:transparent!important;box-shadow:none!important}.panel{border-color:transparent!important}header{visibility:hidden!important}.node rect{fill:none!important}'});
  await page.screenshot({path:path.join(out,'card_foreground.png'),omitBackground:true,animations:'disabled'});
  await fs.writeFile(path.join(out,'card_foreground_contract.json'),JSON.stringify({schema:'CardDiagnosticInkV1',
    alpha_weighted:true,excluded:['HTML backing fills','panel borders','generic header','constant graph node interior fill'],
    retained:['diagnostic text','node outlines','data marks','axes','edge strokes','arrowheads'],
    model_png_unchanged:true})+'\n');
}
