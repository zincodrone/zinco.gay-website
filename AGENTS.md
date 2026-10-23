# Update standards

The user requires the following for every future repository or website update.
Do this automatically; do not wait for the user to request it again.

- Update `README.md` to describe the changes and add the corresponding changelog entry.
- Increment the website version for each coherent update, including fixes, maintenance,
  documentation, and security changes. Use `major.minor.patch.security` for new releases.
  Increment only the security number for security updates, for example `1.3.0.1`
  to `1.3.0.2`. Increment patch for ordinary fixes or small maintenance updates,
  minor for new features, and major for substantial redesigns or breaking changes.
  Reset all numbers to the right of the incremented component to zero: a patch
  after `1.3.0.1` becomes `1.3.1.0`, a minor becomes `1.4.0.0`, and a major
  becomes `2.0.0.0`. For a release with multiple kinds of changes, use the highest
  applicable component. A security release may include related cleanup work.
  Keep historical three-part labels intact; they imply security number zero.
- Keep the README changelog, version history, release timeline, and website version
  consistent with the same release. Preserve recorded historical release dates.
- Update the footer version on every HTML page, including the blog and redirect page.
- Update versioned stylesheet and script URLs to match the new website version.
- Before reporting completion or pushing, verify that all pages use the same current
  version, the README documents it, and the release timeline includes it.
- Treat these release updates as part of the requested work, not an optional follow-up.
  Follow any explicit instructions from the user about when to commit or push.

# Secret protection

- Run `python .github/scripts/install_push_protection.py` once in every new checkout
  before pushing, using Python 3. This installs the checksum-verified scanner outside
  tracked files and enables the repository's local pre-push hook.
- Do not bypass a failed or unavailable pre-push scan, including through an API push.
  Resolve findings or repair the scanner first.
- Keep automatic and manual deployments dependent on a successful BetterLeaks scan
  of the same workflow commit. Do not pass deployment secrets to the scan job.
- After changing inline HTML scripts or styles, regenerate the CSP hashes with
  `python .github/scripts/check_site_security.py --update`, review the policy,
  and verify animations and social-link behavior in a browser.
- Keep recovery archives outside the repository and `public_html`. Never upload
  full account backups, DNS exports, or account settings as public artifacts.
