import { validate } from "./validator.js";
import {
  isMarketOpen,
  currentSession,
} from "./market_guard.js";

console.log(
  validate({
    date: "2026-07-27",
    session: "12:01",
    result: "48",
    setIndex: 1622.04,
    setValue: 43018.36,
  })
);

console.log(isMarketOpen());

console.log(currentSession());