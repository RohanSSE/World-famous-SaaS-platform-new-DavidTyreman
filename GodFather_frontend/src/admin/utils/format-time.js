import dayjs from "dayjs";
import duration from "dayjs/plugin/duration";
import relativeTime from "dayjs/plugin/relativeTime";
dayjs.extend(duration);
dayjs.extend(relativeTime);
const formatPatterns = {
  dateTime: "DD MMM YYYY h:mm a",
  // 17 Apr 2022 12:00 am
  date: "DD MMM YYYY",
  // 17 Apr 2022
  time: "h:mm a",
  // 12:00 am
  split: {
    dateTime: "DD/MM/YYYY h:mm a",
    // 17/04/2022 12:00 am
    date: "DD/MM/YYYY"
    // 17/04/2022
  },
  paramCase: {
    dateTime: "DD-MM-YYYY h:mm a",
    // 17-04-2022 12:00 am
    date: "DD-MM-YYYY"
    // 17-04-2022
  }
};
const isValidDate = (date) => date !== null && date !== void 0 && dayjs(date).isValid();
function fDateTime(date, template) {
  if (!isValidDate(date)) {
    return "Invalid date";
  }
  return dayjs(date).format(template ?? formatPatterns.dateTime);
}
function fDate(date, template) {
  if (!isValidDate(date)) {
    return "Invalid date";
  }
  return dayjs(date).format(template ?? formatPatterns.date);
}
function fToNow(date) {
  if (!isValidDate(date)) {
    return "Invalid date";
  }
  return dayjs(date).toNow(true);
}
export {
  fDate,
  fDateTime,
  fToNow,
  formatPatterns
};
