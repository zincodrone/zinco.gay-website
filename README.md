This is my first attempt to create my own website. Let's see how this goes.

# To-Do List

**Legend:** ✅ Completed · 🟨 Planned · \[❓\] Undecided

- ✅ **Blog** — For thought pieces, introspection, and other things that are best written out.
- ✅ **Biography** — Telling new visitors to my website who I am, what I do, and how to contact me.

- \[❓\] **Cool looking layout** — Layout is unlikely to be in any way cool looking as this started as a website to replace my Linktree. I need inspiration anyway to design something cool looking.

- \[❓\] Activity Log — Place to log activities in my daily life, what I've been up to, and maybe linking to my blog (who knows?).

# Changelog

Versions use `major.minor.patch`: major for substantial redesigns or changes that break existing behavior, minor for new features, and patch for fixes or small updates. October 2026 marks the site's first major release, `1.0.0`.

## Release timeline

Follow the arrows from the earliest release to the latest, snaking across each row. Times are in America/Chicago and reflect when each version was committed, not when it was deployed to the live website. The 2024 entries retain the months recorded in the original changelog; exact release days were not recorded there. Spacing between releases is not to scale.

![Snaking release timeline from version 0.1.0 through 1.3.0](images/changelog-timeline-snake.png)

## 1.3.0 — October 21, 2026

- Added staggered entrance fades to Home, the blog listing, and individual blog posts.
- Added paired row fades to social buttons, waiting for the button images to load before animating.
- Limited entrance fades to the first visit to each page in the current tab session; clicking, refreshing, or returning does not replay completed fades.
- Kept the footer version and heart visible without animation and respected reduced-motion preferences.
- Added an immediate black background and preloaded the star GIF to reduce flashes during navigation and refreshes.
- Fixed fade timing so both social buttons in each row appear together.

## 1.2.4 — October 2026

- Reset social-link choices when leaving or returning to the page, including browser Back/Forward navigation.
- Closed the choices before opening the current-tab redirect page.

## 1.2.3 — October 2026

- Made the redirect countdown visibly decrease from five seconds until the profile opens.
- Stopped the countdown when cancelling, continuing immediately, or leaving the page.

## 1.2.2 — October 2026

- Replaced the brief fade with a full slide-open animation beneath the social links.
- Added versioned stylesheet and script URLs so browsers request the current files after updates.
- Preserved the black-and-white panel, cancellation, and reduced-motion support.

## 1.2.1 — October 2026

- Moved social-link choices into a rounded panel below the social buttons so they no longer overlap.
- Added a slide-in animation with support for reduced-motion preferences.
- Kept the panel and buttons black with white text, including hover states.
- Preserved tab choices, cancellation, Escape, and keyboard focus handling.

## 1.2.0 — October 2026

- Added a social-link dialog offering the current tab, a new tab, or cancel.
- Added a redirect page for current-tab choices, showing the destination with a five-second delay, Continue now, and Cancel.
- Kept keyboard shortcuts and direct links working when JavaScript is unavailable.
- Updated deployment to include the redirect page and social-link script.

## 1.1.0 — October 2026

- Added Instagram to the Socials page with a matching button.
- Updated navigation to use clean URLs without `.html` extensions.
- Added redirects from old `.html` addresses to their clean URLs.
- Updated cPanel deployment to include the URL rewrite configuration.
- Standardized the early changelog versions as `0.1.0` and `0.1.1` and removed their checkmarks.

## 1.0.1 — October 2026

- Added the current version to the footer on every page.
- Aligned the version on the left and the heart in the center of the footer, with the version linking to the GitHub repository.
- Kept the footer at the bottom of short pages.

## 1.0.0 — October 2026

- Added a blog section with the first post, **Welcome!**
- Updated the first blog post's body and preview text.
- Added matching Home, Blog, and Socials navigation.
- Moved social links to their own page.
- Added Discord, Twitter/X, YouTube, and Twitch profile links.
- Enlarged the TikTok logo and aligned all social button labels.
- Arranged social links in two columns, with the final link centered at the bottom.
- Updated the homepage biography to link to the blog and socials.

## 0.1.1 — October 2024

- Add favicon
- Added proper social media labels

## 0.1.0 — May 2024

- Merge Socials and Home Page
- Disable Socials Page
- Disable and remove links to other HTML pages
