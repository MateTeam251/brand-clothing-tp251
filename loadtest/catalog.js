// k6 load test: a shopper browsing the catalog (read-only API, no login/checkout,
// so nginx rate limits don't kick in and no data is written).
//
//   k6 run -e PROFILE=smoke  loadtest/catalog.js
//   k6 run -e PROFILE=load   loadtest/catalog.js
//   k6 run -e PROFILE=stress loadtest/catalog.js
//
// BASE_URL defaults to staging. Never point stress at prod.
import http from "k6/http";
import { check, group, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "https://staging.theart-theartist.com";
const PROFILE = __ENV.PROFILE || "smoke";

const profiles = {
  // 1 shopper for 1 min: does the script work?
  smoke: [{ duration: "1m", target: 1 }],
  // ~20 shoppers at once for 5 min: a busy day for a small shop.
  load: [
    { duration: "2m", target: 20 },
    { duration: "5m", target: 20 },
    { duration: "1m", target: 0 },
  ],
  // Step up to 100 to find where it breaks. Stops early if errors pile up.
  stress: [
    { duration: "2m", target: 20 },
    { duration: "2m", target: 50 },
    { duration: "2m", target: 100 },
    { duration: "2m", target: 100 },
    { duration: "1m", target: 0 },
  ],
};

export const options = {
  scenarios: {
    // startVUs 1: with 0, a single 0→1 stage only starts the shopper at its very end.
    browse: { executor: "ramping-vus", startVUs: 1, stages: profiles[PROFILE], gracefulRampDown: "30s" },
  },
  thresholds: {
    http_req_failed: [{ threshold: "rate<0.01", abortOnFail: PROFILE === "stress", delayAbortEval: "30s" }],
    "http_req_duration{page:list}": ["p(95)<800"],
    "http_req_duration{page:detail}": ["p(95)<800"],
  },
  summaryTrendStats: ["avg", "med", "p(90)", "p(95)", "p(99)", "max"],
};

function get(path, page) {
  const res = http.get(`${BASE_URL}${path}`, { tags: { page }, timeout: "30s" });
  check(res, { [`${page} 200`]: (r) => r.status === 200 });
  return res;
}

// Like a person: open the catalog, maybe filter or page, open 1-3 products.
export default function () {
  let ids = [];
  group("catalog", () => {
    const orderings = ["", "&ordering=price", "&ordering=-created_at"];
    const offset = 12 * Math.floor(Math.random() * 3);
    const res = get(`/api/products/?limit=12&offset=${offset}${orderings[Math.floor(Math.random() * 3)]}`, "list");
    try {
      ids = (res.json("results") || []).map((p) => p.id);
    } catch (e) {
      ids = [];
    }
    if (Math.random() < 0.5) get("/api/products/collections/", "collections");
  });
  sleep(1 + Math.random() * 2);

  const views = 1 + Math.floor(Math.random() * 3);
  for (let i = 0; i < views && ids.length; i++) {
    group("product", () => {
      get(`/api/products/${ids[Math.floor(Math.random() * ids.length)]}/`, "detail");
    });
    sleep(2 + Math.random() * 4);
  }
}
