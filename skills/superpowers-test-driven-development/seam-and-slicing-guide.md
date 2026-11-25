# Seams, Vertical Slicing, and Boundary Mocking Guide

Selective TDD supplement adapted from `mattpocock/skills` (`skills/engineering/tdd`). Use alongside the Red-Green-Refactor cycle in `SKILL.md`.

When exploring the codebase, read `GLOSSARY.md` (if present) so test names and interface vocabulary match the project's domain language, and respect relevant ADRs.

## 1. Agree on Seams Before Writing Tests

A **seam** is the public boundary where callers and tests observe behavior without reaching into internals.

- Before writing tests for a non-trivial change, propose the candidate seams and confirm them with the user.
- Give each proposed seam a one-line note on **what it catches** and **what it misses** so test effort lands on critical paths instead of internal details.
- When interface shape or seam placement is unclear, consult `mattpocock-codebase-design` for deep-module vocabulary (`module`, `interface`, `depth`, `seam`, `adapter`).

## 2. Avoid Tautological Tests

A **tautological test** recomputes its expected value using the same logic as the implementation, so it passes by construction and can never catch a logic bug.

```typescript
// BAD: Expected value mirrors the implementation
test("calculateTotal sums line items", () => {
  const items = [{ price: 10 }, { price: 5 }];
  const expected = items.reduce((sum, i) => sum + i.price, 0);
  expect(calculateTotal(items)).toBe(expected);
});

// GOOD: Expected value comes from an independent source of truth
test("calculateTotal sums line items", () => {
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
});
```

Expected values must come from an independent source of truth: a known-good literal, a worked example, or the spec.

## 3. Vertical Slicing (Tracer Bullets), Not Horizontal Slicing

- **Horizontal slicing (avoid)**: writing every test for the whole feature up front before any implementation. Bulk upfront tests lock in imagined internal shapes and lose sensitivity to real behavior.
- **Vertical slicing (prefer)**: one seam, one failing test, one minimal implementation, refactor, repeat — each slice acts as a **tracer bullet** that informs the next test.

## 4. Mock Only at System Boundaries — With SDK-Style Interfaces

Mock only true system boundaries (external APIs, time/randomness, and where necessary databases or filesystem). Do not mock your own internal classes or collaborators.

Design boundary dependencies so each external operation is independently mockable:

```typescript
// GOOD: Operation-specific SDK interface — no conditional logic in test mocks
const api = {
  getUser: (id: string) => fetch(`/users/${id}`),
  getOrders: (userId: string) => fetch(`/users/${userId}/orders`),
  createOrder: (data: OrderInput) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Generic fetcher forces branching inside every mock
const api = {
  fetch: (endpoint: string, options?: RequestInit) => fetch(endpoint, options),
};
```
