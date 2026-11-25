/** Add the confirmed adjudicator identity to a completed ConsumerBR workbook. */
import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const [inputPath, outputPath, adjudicator] = process.argv.slice(2);
if (!inputPath || !outputPath || !adjudicator) {
  throw new Error("Uso: node finalize_consumerbr_adjudication.mjs <entrada.xlsx> <saida.xlsx> <adjudicador>");
}

const first = 7;
const last = 173;
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const sheet = workbook.worksheets.getItem("Adjudicação");
sheet.getRange(`K${first}:K${last}`).values = Array.from({ length: last - first + 1 }, () => [adjudicator]);
sheet.getRange(`L${first}`).formulas = [[`=IF(AND(I${first}<>"",J${first}<>"",K${first}<>""),"Completo","Pendente")`]];
sheet.getRange(`L${first}:L${last}`).fillDown();
workbook.recalculate();
const check = await workbook.inspect({ kind: "table", range: "Adjudicação!I6:L9", include: "values,formulas", tableMaxRows: 4, tableMaxCols: 4, maxChars: 1400 });
if (!check.ndjson.includes(adjudicator) || !check.ndjson.includes("Completo")) {
  throw new Error("A adjudicação não foi finalizada corretamente.");
}
if (process.env.ECOMSHIELD_PREVIEW_PATH) {
  const preview = await workbook.render({ sheetName: "Adjudicação", range: "H6:L10", scale: 1.5, format: "png" });
  await fs.writeFile(process.env.ECOMSHIELD_PREVIEW_PATH, new Uint8Array(await preview.arrayBuffer()));
}
await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Adjudicação finalizada: ${last - first + 1} decisões atribuídas a ${adjudicator}.`);
