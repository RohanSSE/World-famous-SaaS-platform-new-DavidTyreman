const DEFAULT_LOCALE = { code: "en-US", currency: "USD" };
function processInput(inputValue) {
  if (inputValue == null || Number.isNaN(inputValue)) return null;
  return Number(inputValue);
}
function fNumber(inputValue, options) {
  const locale = DEFAULT_LOCALE;
  const number = processInput(inputValue);
  if (number === null) return "";
  const fm = new Intl.NumberFormat(locale.code, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
    ...options
  }).format(number);
  return fm;
}
function fCurrency(inputValue, options) {
  const locale = DEFAULT_LOCALE;
  const number = processInput(inputValue);
  if (number === null) return "";
  const fm = new Intl.NumberFormat(locale.code, {
    style: "currency",
    currency: locale.currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
    ...options
  }).format(number);
  return fm;
}
function fPercent(inputValue, options) {
  const locale = DEFAULT_LOCALE;
  const number = processInput(inputValue);
  if (number === null) return "";
  const fm = new Intl.NumberFormat(locale.code, {
    style: "percent",
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
    ...options
  }).format(number / 100);
  return fm;
}
function fShortenNumber(inputValue, options) {
  const locale = DEFAULT_LOCALE;
  const number = processInput(inputValue);
  if (number === null) return "";
  const fm = new Intl.NumberFormat(locale.code, {
    notation: "compact",
    maximumFractionDigits: 2,
    ...options
  }).format(number);
  return fm.replace(/[A-Z]/g, (match) => match.toLowerCase());
}
export {
  fCurrency,
  fNumber,
  fPercent,
  fShortenNumber
};
