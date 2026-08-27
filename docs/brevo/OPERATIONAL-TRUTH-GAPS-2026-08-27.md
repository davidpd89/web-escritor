# Brevo — operational truth gaps · 2026-08-27

**Status:** OPEN · evidence-backed follow-up to PR #111  
**Rule:** a planned capability is not `DONE` until account state + repo contract + live behavior agree.

## 1. Why this document exists

PR #111 intentionally separated documentation from live account changes. Subsequent work executed part of that backlog. A transversal audit on 27/08 found three places where a partial result could now be mistaken for a completed implementation.

This file records only facts that can be supported by current repo/account snapshot/API documentation. It must be retired when all P0 items below are closed and their durable contract has moved into tests/code.

## 2. BRV-001 beta list: created, integration not complete

Verified repository history records creation of Brevo list:

- list ID: `6`
- name: `Lectores beta`

The subscriber Worker already has the correct fail-closed routing contract:

```text
SEPARATE_LIST_ENV_KEY["lectores-beta"] = "BREVO_BETA_LIST_ID"
```

but the same implementation explicitly requires the Cloudflare binding to exist.

### Current status

`LIST CREATED` != `BETA JOURNEY LIVE`

Still requires live evidence for:

1. `BREVO_BETA_LIST_ID=6` configured in the relevant Worker environment;
2. deploy of that Worker version;
3. beta-form smoke with a controlled address/test protocol;
4. evidence that a beta signup reaches list 6 and does not leak into the general newsletter unless consented separately;
5. cleanup of the test contact if one is created.

Do not mark BRV beta routing complete solely because ID 6 exists in the account.

## 3. Subscriber counts in the current snapshot are not trustworthy as written

`scripts/brevo/snapshot-brevo.py` previously populated list counts from:

```text
GET /v3/contacts/lists
```

using response field `totalSubscribers`.

Brevo's current API documentation states that support for `totalSubscribers` and `totalBlacklisted` on **Get all the lists** is being dropped and their default will be `0`.

Therefore a row such as:

```text
Lectores web — 0 suscriptores
```

from that collection endpoint is no longer evidence that the list is actually empty.

Brevo still documents subscriber counts on:

```text
GET /v3/contacts/lists/{listId}
```

This PR changes the snapshot collector accordingly:

- collection endpoint = discovery of IDs/names;
- detail endpoint = count authority;
- detail failure/missing count = `unknown`, never inferred zero.

Official references (cut 2026-08-27):

- https://developers.brevo.com/reference/get-lists
- https://developers.brevo.com/reference/get-list

### Required follow-up

After merge, run the corrected snapshot against the real account and regenerate `docs/brevo/SNAPSHOT-LIVE.md`. Do not hand-edit subscriber counts.

## 4. Visitor-facing newsletter promise is ahead of verified backend behavior

Current `index.html` / production newsletter copy says the subscriber will receive:

> `el primer capítulo de Samuel entre mundos gratis`

But `cloudflare-worker-subscribe.js` contains an explicit release gate saying the automation linkage for list 3 has not been verified and, for that reason, the site copy should **not promise chapter delivery** until trigger -> send is confirmed.

These two authorities currently contradict one another.

### Why this matters

This is not a stylistic preference. It is a product/consent contract:

- the visitor takes an action because the page promises a delivery;
- successful Brevo contact creation does not prove an automation email was sent;
- a 2xx from the subscribe Worker can therefore coexist with a broken promised outcome.

### Safe closure options

#### Option A — verify and keep the promise

Preferred if the intended experience really includes the chapter.

1. inspect the live automation trigger in Brevo;
2. prove list 3 / DOI completion is the intended trigger;
3. use a controlled test subscriber;
4. verify DOI email;
5. complete DOI;
6. verify the promised chapter/access email actually arrives;
7. record template/automation IDs and timing without committing PII/secrets;
8. add an operational smoke/check that can detect trigger drift without adding a fake subscriber on every deploy.

Only then may the promise be considered verified.

#### Option B — remove the promise until verified

If the live automation cannot be proved immediately, remove `el primer capítulo ... gratis` from public signup copy. Keep only benefits that the current flow demonstrably provides.

Do **not** solve this by changing the Worker comment. The mismatch is closed only by live evidence or by narrowing the public promise.

## 5. P0 Definition of Done

- [x] snapshot parser no longer trusts deprecated collection counts;
- [x] deterministic regression test covers `collection=0` while list detail has a non-zero count;
- [ ] corrected live snapshot regenerated with real API access;
- [ ] `BREVO_BETA_LIST_ID=6` verified in the correct live Worker environment;
- [ ] beta signup smoke proves list isolation;
- [ ] newsletter `first chapter` promise either proven end-to-end or removed;
- [ ] docs/backlog updated so no task says `DONE` for a partial state;
- [ ] no contact PII or API key enters Git.

## 6. Merge boundary of this PR

This PR is safe to merge without live Brevo writes because it only:

- corrects a read-only snapshot parser;
- adds a deterministic mocked regression test;
- makes the shared Python test workflow run when the snapshot parser changes;
- records the live work still required.

It does **not** configure Cloudflare, mutate Brevo lists, create contacts, change automations or deploy Workers.
