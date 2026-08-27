# 13 — Fuentes oficiales y corte 2026-08-27

## Propósito

Este documento es el registro de evidencia primaria de la auditoría SEO.

Regla:

- Google Search Central / Google Help / Search Status Dashboard son autoridad primaria para políticas y funcionalidades de Google;
- Schema.org sirve para vocabulario, pero la Search Gallery de Google define qué tipos tienen features en Google Search;
- herramientas SEO de terceros pueden aportar datos/estimaciones, pero no se usan para afirmar factores internos de ranking;
- blogs/opiniones/estudios de correlación no sustituyen la documentación oficial cuando Google publica una regla explícita.

**Fecha de corte:** 27/08/2026.

---

# 1. Search Essentials

## Google Search Essentials

https://developers.google.com/search/docs/essentials

Uso en este plan:

- people-first content;
- palabras que los usuarios buscan en title/main heading/alt/link text;
- crawlable links;
- technical baseline;
- spam compliance.

Estado: vigente.

---

# 2. Spam policies

## Spam policies for Google Web Search

https://developers.google.com/search/docs/essentials/spam-policies

Versión ES:

https://developers.google.com/search/docs/essentials/spam-policies?hl=es

Uso:

- cloaking;
- doorway abuse;
- expired domain abuse;
- hidden text/links;
- link spam;
- scaled content abuse;
- scraping;
- site reputation abuse;
- misleading functionality;
- generative-AI manipulation.

Observación 2026:

la documentación vigente aclara que spam incluye también intentos de manipular respuestas de IA generativa en Google Search.

Estado: P0 policy authority.

---

# 3. Helpful / people-first content

## Creating helpful, reliable, people-first content

https://developers.google.com/search/docs/fundamentals/creating-helpful-content

Uso:

- original information/reporting/research/analysis;
- complete/substantial description;
- first-hand expertise;
- site purpose/audience;
- Who/How/Why;
- no preferred word count;
- no fake freshness;
- evaluación de contenido tras core updates.

Estado: vigente.

---

# 4. Ranking systems

## A guide to Google Search ranking systems

https://developers.google.com/search/docs/appearance/ranking-systems-guide

Uso:

- ranking uses multiple systems/signals;
- link analysis/PageRank contextualizado;
- freshness systems;
- passage systems;
- neural matching / RankBrain conceptual;
- no single factor roadmap.

Estado: background authority.

---

# 5. SEO Starter Guide

https://developers.google.com/search/docs/fundamentals/seo-starter-guide

Uso:

- crawl/index fundamentals;
- site hierarchy;
- links;
- titles;
- snippets;
- images;
- myths around ranking.

Estado: vigente.

---

# 6. Third-party SEO tools / ranking claims

## Google Search documentation updates — June 2026 third-party SEO tools guidance

https://developers.google.com/search/updates

Uso:

- third-party tools do not have access to Google internal ranking data;
- do not treat external scores/guarantees as Google truth.

Estado: current documentation update log.

---

# 7. Title links

## Control your title links in search results

https://developers.google.com/search/docs/appearance/title-link

Uso:

Google may use signals such as:

- `<title>`;
- visible main title;
- headings;
- `og:title`;
- prominent text;
- anchor text on the page;
- external anchor text.

Implication:

title experiments must review H1/prominent text/anchors too.

---

# 8. Snippets

## Control your snippets in search results

https://developers.google.com/search/docs/appearance/snippet

Uso:

- snippets primarily generated from page content;
- meta description may be used;
- snippets can differ per query;
- `nosnippet`, `max-snippet`, `data-nosnippet` controls.

---

# 9. Sitelinks

## Sitelinks

https://developers.google.com/search/docs/appearance/sitelinks

Uso:

- generated automatically;
- logical site structure;
- informative titles/headings;
- concise/relevant internal anchor text;
- links to important pages.

No markup to force exact sitelinks.

---

# 10. Featured snippets

## Featured snippets and your website

https://support.google.com/websearch/answer/9351707

Search Central references:

https://developers.google.com/search/docs/appearance/featured-snippets

Uso:

- site owners cannot mark a page as a featured snippet;
- Google decides algorithmically;
- snippet controls can opt out/limit.

---

# 11. Site name

## Site names in Google Search

https://developers.google.com/search/docs/appearance/site-names

Uso:

- WebSite structured data on home;
- consistent name;
- alternateName fallback;
- automated generation.

Current preferred identity:

`David Porto Díaz`.

---

# 12. Canonicalization

## How to specify a canonical

https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls

Uso:

- redirects strong signal;
- `rel=canonical` strong signal;
- sitemap weaker canonical signal;
- consistent URLs.

---

# 13. Sitemaps

## Build and submit a sitemap

https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap

## Sitemap protocol best practices / Google guidance

https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview

Uso:

- only canonical URLs;
- `lastmod` meaningful if accurate;
- Google ignores `priority` and `changefreq`;
- sitemap does not guarantee indexing.

---

# 14. Robots meta / noindex

## Robots meta tag and X-Robots-Tag

https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag

Uso:

- `noindex` controls indexing;
- crawler must access page to see noindex;
- max snippet/image/video controls.

---

# 15. Robots.txt

## Introduction to robots.txt

https://developers.google.com/search/docs/crawling-indexing/robots/intro

Uso:

- crawl control, not secrecy;
- do not use as noindex substitute;
- resource accessibility.

---

# 16. Redirects

## Redirects and Google Search

https://developers.google.com/search/docs/crawling-indexing/301-redirects

Uso:

- server-side permanent redirects;
- migration/consolidation;
- avoid irrelevant redirect to home.

---

# 17. HTTP status / network errors

## How HTTP status codes affect Google Search

https://developers.google.com/search/docs/crawling-indexing/http-network-errors

Uso:

- 2xx;
- 3xx;
- 4xx;
- 5xx;
- 404/410 behavior;
- soft 404 diagnostics.

---

# 18. JavaScript SEO

## JavaScript SEO basics

https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics

Uso:

- Google rendering;
- indexable content;
- links;
- canonical/meta;
- error handling.

Project decision:

preserve static/server-first content despite Google JS capability.

---

# 19. Mobile-first indexing

## Mobile-first indexing best practices

https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing

Uso:

- content parity;
- metadata parity;
- structured data parity;
- images/alt;
- crawlability.

---

# 20. Links

## Links best practices for Google

https://developers.google.com/search/docs/crawling-indexing/links-crawlable

Uso:

- crawlable `<a href>`;
- descriptive anchor;
- context;
- internal linking.

---

# 21. Qualifying outbound links

## Qualify outbound links

https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links

Uso:

- `rel=sponsored` for ads/affiliate/paid links;
- `ugc` for user-generated links when applicable;
- nofollow when other values don't apply and qualification is needed.

Current Amazon affiliate links already use `sponsored`.

---

# 22. Core Web Vitals

## Understanding Core Web Vitals and Google Search results

https://developers.google.com/search/docs/appearance/core-web-vitals

## Web Vitals thresholds

https://web.dev/articles/vitals

Reference thresholds:

- LCP <= 2.5s good;
- INP <= 200ms good;
- CLS <= 0.1 good;
- evaluate around 75th percentile.

Google clarification:

good CWV does not guarantee top ranking.

---

# 23. Page experience

## Understanding page experience in Google Search results

https://developers.google.com/search/docs/appearance/page-experience

Uso:

- no single page-experience score;
- CWV + broader experience;
- avoid intrusive interstitials;
- HTTPS/mobile usability.

---

# 24. Image SEO

## Google Images SEO best practices

https://developers.google.com/search/docs/appearance/google-images

Uso:

- HTML images;
- context;
- alt;
- filenames;
- responsive/performance;
- image sitemap when needed.

---

# 25. Image metadata

## Image metadata in Google Images

https://developers.google.com/search/docs/appearance/structured-data/image-license-metadata

Uso:

- licensing/creator/credit only if real;
- structured data/IPTC.

Conditional only.

---

# 26. Discover

## Get on Discover

https://developers.google.com/search/docs/appearance/google-discover

Uso:

- eligibility automatic for indexed policy-compliant pages;
- titles that capture essence, no clickbait;
- timely/unique/story value;
- large relevant images.

2026 image guidance referenced in Google docs:

- >=1200px wide recommended;
- >300,000 total pixels;
- 16:9 useful;
- `max-image-preview:large`.

---

# 27. Google News

## Google News policies / ranking and transparency

https://support.google.com/news/publisher-center/

Search documentation:

https://developers.google.com/search/docs/appearance/google-news

Important operational change:

from late March 2025 Google News publication pages are automatically generated; traditional manual publication setup in Publisher Center is not the inclusion path it once was.

Use:

- transparency;
- dates;
- bylines;
- publisher/contact;
- original news content.

---

# 28. Video

## Video SEO best practices

https://developers.google.com/search/docs/appearance/video

## Video structured data

https://developers.google.com/search/docs/appearance/structured-data/video

Uso:

- indexed watch page;
- thumbnail;
- stable media URLs;
- VideoObject;
- page where video is primary for certain features.

Conditional until real video corpus exists.

---

# 29. Structured data general policies

## General structured data guidelines

https://developers.google.com/search/docs/appearance/structured-data/sd-policies

Uso:

- content must represent visible page;
- accurate/non-misleading;
- rich result not guaranteed;
- violations may cause manual action.

P0 authority for schema compliance.

---

# 30. Search Gallery

https://developers.google.com/search/docs/appearance/structured-data/search-gallery

Use:

defines Google-supported search appearance types, not all schema.org vocabulary.

Current relevant families include:

- Article;
- Breadcrumb;
- Event;
- Image metadata;
- Organization;
- ProfilePage;
- Review snippet;
- SoftwareApplication;
- Video;
- Product under conditions.

---

# 31. Review snippets

## Review snippet structured data

https://developers.google.com/search/docs/appearance/structured-data/review-snippet

Critical policy used in this audit:

> Don't aggregate reviews or ratings from other websites.

Relevant reviewed item types include Book.

Direct consequence:

remove Amazon-derived Review objects from Samuel Book JSON-LD.

---

# 32. Reviews system

## Write high quality reviews

https://developers.google.com/search/docs/specialty/ecommerce/write-high-quality-reviews

Uso:

- evidence of experience;
- original analysis;
- quantitative/comparative context when useful;
- advantages/disadvantages;
- what sets item apart.

Relevant to recommendations pages even outside ecommerce.

---

# 33. ProfilePage

## ProfilePage structured data

https://developers.google.com/search/docs/appearance/structured-data/profile-page

Use:

`autor.html` centered on David Porto Díaz + mainEntity Person.

---

# 34. Event

## Event structured data

https://developers.google.com/search/docs/appearance/structured-data/event

Critical requirement for feature eligibility:

- each event needs a unique URL;
- page focused on a single event.

Used to recommend future `/eventos/<slug>/` pages.

---

# 35. SoftwareApplication

## Software app structured data

https://developers.google.com/search/docs/appearance/structured-data/software-app

Use:

validate tool markup; do not assume every schema.org WebApplication automatically receives a Google feature.

---

# 36. Book / Book actions

## Book structured data / book actions

https://developers.google.com/search/docs/appearance/structured-data/book

Google Books action documentation is aimed at book providers with a broad catalog/feed.

Use:

- don't build provider feed just for two author books without a genuine provider role.

---

# 37. Google Books Partner Program

## Partner Center overview

https://support.google.com/books/partner/answer/3244021

## Introduction to Google Books Partner Program

https://support.google.com/books/partner/answer/3324395

## Add a book

https://support.google.com/books/partner/answer/9261664

Use:

- authors/publishers can submit books;
- preview on Google Books;
- discovery through Book Search;
- Google Play sale when eligible.

Project gate:

rights/editorial approval before submission.

---

# 38. Google Business Profile

## Guidelines for representing your business on Google

https://support.google.com/business/answer/3038177

Eligibility rule used here:

business must have a physical location customers can visit or travel to customers.

Project decision:

no fake GBP based only on author's private residence/online presence.

---

# 39. Preferred Sources

## Guide to Preferred Sources for Web Publishers

https://developers.google.com/search/docs/appearance/preferred-sources

**Last updated:** 2026-08-20 UTC at audit time.

Use:

- globally available in Top Stories where Search available;
- can highlight preferred source in AI Mode/AI Overviews where available;
- domain/subdomain eligibility;
- standard JS button;
- custom JS SDK;
- deeplink.

Important:

this is user preference, not universal ranking boost.

---

# 40. Google Trends

## Trends data FAQ

https://support.google.com/trends/answer/4365533

Use:

- normalized by time/location;
- 0–100 relative interest;
- not absolute search volume.

---

# 41. Google Play Books

## How to sell books on Google Play

https://support.google.com/books/partner/answer/1079107

## Partner Center

https://support.google.com/books/partner/

Use:

- distribution/preview/commercial option;
- not a ranking requirement;
- coordinate rights/publisher.

---

# 42. Knowledge Panel

## About Knowledge Panels

https://support.google.com/knowledgepanel/answer/9163198

## Claim a Knowledge Panel

https://support.google.com/knowledgepanel/answer/7534902

Use:

- panels generated automatically;
- claim only if panel exists and Google offers it;
- verification paths vary;
- suggest factual corrections.

No guarantee a panel can be created on demand.

---

# 43. Disavow

## Disavow links to your site

https://support.google.com/webmasters/answer/2648487

Use only in exceptional circumstances.

Google warns most sites do not need it and incorrect use can harm performance.

---

# 44. Indexing API

## Indexing API usage

https://developers.google.com/search/apis/indexing-api/v3/using-api

Scope:

- JobPosting;
- BroadcastEvent embedded in VideoObject.

Not for:

- books;
- articles;
- tools;
- normal event pages.

---

# 45. Search Status Dashboard

https://status.search.google.com/

Used for:

- ranking updates;
- incidents;
- rollout timing.

At audit close 27/08/2026, the most recent completed ranking event was the August 2026 spam update and no active incident was being asserted from the consulted dashboard snapshot.

---

# 46. Ranking update history relevant to 2026

Official dashboard history at audit time included:

- **August 2026 spam update** — started 2026-08-18; completed 2026-08-21; official duration 2d16h.
- **June 2026 spam update** — June 24; ~2d1h.
- **May 2026 core update** — May 21; ~11d21h.
- **March 2026 core update** — March 27; ~12d4h.
- **March 2026 spam update** — March 24; ~19h30.
- **February 2026 Discover update** — February 5; ~21d17h.

Use exact dashboard values in the versioned updates registry when implemented.

---

# 47. Search documentation update log

https://developers.google.com/search/updates

Important 2026 entries at cut include:

- Aug 20: custom Preferred Sources button;
- July: social/video platform Search Console analysis;
- 2026 AI/Search documentation changes;
- FAQ rich-result retirement changes.

Recommended maintenance:

subscribe to official RSS documented on that page.

---

# 48. Source priority matrix

| Claim | Authority |
|---|---|
| spam policy | Search Central spam policies |
| structured data eligibility | Search Gallery/type docs |
| Search Console behavior | Search Console Help |
| algorithm rollout dates | Search Status Dashboard |
| GBP eligibility | Business Profile Help |
| Google Books | Books Partner Help |
| Trends interpretation | Trends Help |
| schema vocabulary only | Schema.org |
| ranking score | no third-party authority can claim Google internal score |

---

# 49. Evidence labels for future docs

Use:

- `DOCUMENTED` — Google explicitly documents it;
- `CONDITIONAL` — available only with eligibility/case;
- `ROLLOUT` — deployment may differ by user/property;
- `EXPERIMENT` — project hypothesis, not Google claim;
- `HEURISTIC` — internal engineering/content heuristic;
- `DEPRECATED` — former feature/path no longer recommended;
- `N/A` — not applicable to current model.

Never label an inference `DOCUMENTED`.

---

# 50. Refresh policy

This source registry should be rechecked:

- quarterly;
- after a major Google documentation update;
- before implementing a conditional feature;
- after a significant spam/core policy change;
- when Claude encounters a contradiction.

Priority sources to watch:

1. Search documentation updates RSS;
2. Search Status Dashboard;
3. Search Console docs;
4. spam policies;
5. structured data gallery.

---

# 51. Research exclusions

This master plan deliberately does not treat the following as primary evidence:

- SEO Twitter/X threads;
- anonymous leaks;
- ranking-factor lists;
- correlation studies alone;
- vendor score marketing;
- AI-generated SEO summaries;
- outdated tutorials;
- Reddit anecdotes.

They may inspire questions, but every actionable claim with policy/feature implications should be resolved against Google primary docs or our own data.

---

# 52. Definition of freshness

A source in this document is not permanently valid because it was official once.

Examples of features that changed materially:

- FAQ rich results;
- Publisher Center/News;
- mobile usability reports;
- URL Parameters;
- crawl-rate limiter;
- Preferred Sources;
- AI reporting.

Claude must re-open the official source before implementing a feature months later if behavior could have changed.
