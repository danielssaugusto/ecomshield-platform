/** Add the confirmed reviewer identity and current completion rule to a received A workbook. */
import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const [inputPath, outputPath, reviewer] = process.argv.slice(2);
if (!inputPath || !outputPath || !reviewer) {
  throw new Error("Uso: node finalize_consumerbr_annotator_a.mjs <entrada.xlsx> <saida.xlsx> <revisor>");
}

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("Anotação");
const first = 7;
const last = 246;

sheet.getRange(`F${first}:F${last}`).values = Array.from({ length: last - first + 1 }, () => [reviewer]);
sheet.getRange(`G${first}`).formulas = [[`=IF(AND(D${first}<>"",F${first}<>"",OR(AND(C${first}<>"",D${first}="não",IF(C${first}="fora_de_escopo",E${first}<>"",TRUE)),AND(D${first}="sim",E${first}<>""))),"Completo","Pendente")`]];
sheet.getRange(`G${first}:G${last}`).fillDown();
workbook.recalculate();

const check = await workbook.inspect({
  kind: "table",
  range: "Anotação!C6:G10",
  include: "values,formulas",
  tableMaxRows: 5,
  tableMaxCols: 5,
  maxChars: 1500,
});
if (!check.ndjson.includes(reviewer)) {
  throw new Error("Identificação do revisor não foi registrada.");
}

if (process.env.ECOMSHIELD_PREVIEW_PATH) {
  const preview = await workbook.render({ sheetName: "Anotação", range: "A1:G12", scale: 1.5, format: "png" });
  await fs.writeFile(process.env.ECOMSHIELD_PREVIEW_PATH, new Uint8Array(await preview.arrayBuffer()));
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Planilha finalizada: 240 linhas atribuídas a ${reviewer}.`);
