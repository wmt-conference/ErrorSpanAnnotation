const timer = ms => new Promise(res => setTimeout(res, ms))
const range = (start, end) => Array.from({ length: end - start + 1 }, (_, i) => i+start)
const zip = (a, b) => a.map((k, i) => [k, b[i]]);

export { timer, range, zip }