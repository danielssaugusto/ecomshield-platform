/** Apply explicitly supplied corrections to Daniel's ConsumerBR annotation workbook. */
import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) {
  throw new Error("Uso: node finalize_consumerbr_annotator_b.mjs <entrada.xlsx> <saida.xlsx>");
}

const reviewer = "Daniel Augusto da Silva";
const twoFactorNote = "Perda do código/chave de autenticação em duas etapas ao trocar de aparelho e impossibilidade de acessar a conta; a taxonomia não contempla especificamente 2FA, segurança de login ou bloqueio por 2FA.";
const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("Anotação");
const first = 7;
const last = 246;

sheet.getRange(`C179:E179`).values = [["", "sim", twoFactorNote]];
sheet.getRange(`C180:E180`).values = [["request_refund", "não", ""]];
sheet.getRange(`C181:E181`).values = [["cancel_order", "não", ""]];
sheet.getRange("C244").values = [["request_invoice"]];
sheet.getRange(`F${first}:F${last}`).values = Array.from({ length: last - first + 1 }, () => [reviewer]);
sheet.getRange(`G${first}`).formulas = [[`=IF(AND(D${first}<>"",F${first}<>"",OR(AND(C${first}<>"",D${first}="não",IF(C${first}="fora_de_escopo",E${first}<>"",TRUE)),AND(D${first}="sim",E${first}<>""))),"Completo","Pendente")`]];
sheet.getRange(`G${first}:G${last}`).fillDown();
workbook.recalculate();

const check = await workbook.inspect({
  kind: "table",
  range: "Anotação!C177:G181",
  include: "values,formulas",
  tableMaxRows: 5,
  tableMaxCols: 5,
  maxChars: 1500,
});
if (!check.ndjson.includes("request_refund") || !check.ndjson.includes(reviewer)) {
  throw new Error("As correções ou a identificação do revisor não foram registradas.");
}
if (process.env.ECOMSHIELD_PREVIEW_PATH) {
  const preview = await workbook.render({ sheetName: "Anotação", range: "A175:G181", scale: 1.5, format: "png" });
  await fs.writeFile(process.env.ECOMSHIELD_PREVIEW_PATH, new Uint8Array(await preview.arrayBuffer()));
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log("Planilha B finalizada com quatro correções humanas e identificação do revisor.");
