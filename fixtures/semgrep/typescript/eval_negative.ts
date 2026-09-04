function computeFixedFormula(): unknown {
  const formula: string = process.env.FORMULA as string;
  console.log(`received formula (not executed): ${formula}`);
  return eval("1 + 1");
}

export { computeFixedFormula };
