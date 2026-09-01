function computeFromEnv(): unknown {
  const formula: string = process.env.FORMULA as string;
  return eval(formula);
}

export { computeFromEnv };
