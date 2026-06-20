import { describe, it, expect } from "vitest";
import { sparklinePath, OUTCOME_VALUE } from "@/lib/sparkline";

describe("sparklinePath", () => {
  it("returns empty for fewer than 2 points", () => {
    expect(sparklinePath([])).toBe("");
    expect(sparklinePath([2])).toBe("");
  });

  it("emits one coord per value", () => {
    const out = sparklinePath([0, 1, 2]);
    expect(out.split(" ")).toHaveLength(3);
  });

  it("supports up to 5 points spanning the width", () => {
    const out = sparklinePath([0, 1, 2, 1, 0], 70, 20);
    const coords = out.split(" ");
    expect(coords).toHaveLength(5);
    expect(coords[0].split(",")[0]).toBe("5"); // first x at left pad
    expect(coords[4].split(",")[0]).toBe("65"); // last x at right pad
  });

  it("maps the fixed domain to vertical bounds (W top, L bottom)", () => {
    const out = sparklinePath([2, 0], 70, 20); // W then L
    const ys = out.split(" ").map((c) => Number(c.split(",")[1]));
    expect(ys[0]).toBe(4); // value 2 → top (PAD_Y)
    expect(ys[1]).toBe(16); // value 0 → bottom (h - PAD_Y)
  });

  it("draws a flat line for a constant series", () => {
    const ys = sparklinePath([1, 1, 1]).split(" ").map((c) => Number(c.split(",")[1]));
    expect(new Set(ys).size).toBe(1);
  });

  it("is monotonic: increasing values give decreasing y", () => {
    const ys = sparklinePath([0, 1, 2]).split(" ").map((c) => Number(c.split(",")[1]));
    expect(ys[0]).toBeGreaterThan(ys[1]);
    expect(ys[1]).toBeGreaterThan(ys[2]);
  });

  it("clamps out-of-domain values to the bounds", () => {
    const ys = sparklinePath([5, -5], 70, 20).split(" ").map((c) => Number(c.split(",")[1]));
    expect(ys[0]).toBe(4); // clamped to 2 → top
    expect(ys[1]).toBe(16); // clamped to 0 → bottom
  });

  it("exposes the outcome→value mapping", () => {
    expect(OUTCOME_VALUE).toEqual({ W: 2, D: 1, L: 0 });
  });
});
