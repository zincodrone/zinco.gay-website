This is my first attempt to create my own website. Let's see how this goes.

# To-Do List

**Legend:** ✅ Completed · 🟨 Planned · \[❓\] Undecided

- ✅ **Blog** — For thought pieces, introspection, and other things that are best written out.
- ✅ **Biography** — Telling new visitors to my website who I am, what I do, and how to contact me.

- \[❓\] **Cool looking layout** — Layout is unlikely to be in any way cool looking as this started as a website to replace my Linktree. I need inspiration anyway to design something cool looking.

- \[❓\] Activity Log — Place to log activities in my daily life, what I've been up to, and maybe linking to my blog (who knows?).

# Deployment

Pushes to `main` automatically update and deploy the website through the cPanel API. Connection details are stored in GitHub Actions secrets (`CPANEL_HOST`, `CPANEL_USERNAME`, `CPANEL_REPOSITORY_ROOT`, and `CPANEL_API_TOKEN`), not in source files. The workflow waits for cPanel to confirm the deployed commit and checks the live homepage version. View [deployment runs](https://github.com/zincodrone/zinco.gay-website/actions/workflows/deploy-cpanel.yml).

## Repository security

GitHub Actions scans pushes and pull requests for exposed secrets with a pinned, checksum-verified Gitleaks release. Scanner findings redact secret values. Local environment files and private-key files are excluded from Git by `.gitignore`; real credentials belong in GitHub Actions secrets. These checks reduce accidental exposure but do not guarantee that every security issue will be detected.

# Changelog

Current version: **1.3.0.1**.

New releases use `major.minor.patch.security`: major for substantial redesigns or changes that break existing behavior, minor for new features, patch for ordinary fixes or small maintenance updates, and security for security updates and related cleanup. Increment the applicable number and reset every number to its right to zero. After `1.3.0.1`, another security update would be `1.3.0.2`, an ordinary patch would be `1.3.1.0`, a new feature would be `1.4.0.0`, and a major release would be `2.0.0.0`. When changes span categories, use the highest applicable component.

Historical three-part versions keep their original labels and imply a security number of zero. October 2026 marks the site's first major release, `1.0.0`.

Every update must update this README and the website version together, including all page footers, versioned stylesheet/script URLs, changelog entries, and the release timeline. These requirements are also recorded in [AGENTS.md](AGENTS.md) for future work.

## Release timeline

Follow the arrows from the earliest release to the latest, snaking across each row. Times are in America/Chicago and reflect when each version was committed, not when it was deployed to the live website. The 2024 entries retain the months recorded in the original changelog; exact release days were not recorded there. Spacing between releases is not to scale.

![Snaking release timeline from version 0.1.0 through 1.3.0.1](images/changelog-timeline-snake.png)

## 1.3.0.1 — October 21, 2026 (security update)

Security and repository maintenance completed October 21, 2026. The four-part version designation and these release notes were added October 22, 2026.

- Moved cPanel connection details into GitHub Actions secrets and removed the deployment document that contained hosting details.
- Removed known hosting identifiers and personal commit email addresses from the branch history, and deleted nine old deployment runs and their logs. Existing clones and cached commits may still retain old history.
- Added a pinned, checksum-verified Gitleaks scan for pushes and pull requests, with secret values redacted from findings.
- Pinned the checkout action to a specific commit and disabled persisted Git credentials.
- Excluded local environment files, private-key files, and Python cache files from Git.
- Added automatic cPanel updates and deployment verification through HTTPS, with redirect blocking and redacted connection details in error messages.
- Removed 17 unused images, including duplicate social graphics, obsolete timeline images, and layout mockups.
- Established the `major.minor.patch.security` version format, updated deployment verification to check the full four-part version, and required synchronized README, timeline, and website versions for future updates.

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
