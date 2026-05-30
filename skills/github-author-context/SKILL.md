---
name: github-author-context
description: "GitHub contributor context: identity, activity, trust, company/team signal, notes."
---

# GitHub Author Context

Build a compact maintainer-facing profile for a PR author or GitHub user. Use this by default during PR review unless the author is Bram (`BramVR` or an obvious Bram-owned account).

## Inputs

Prefer a GitHub login. From a PR:

```bash
gh pr view <n> --json author,url,headRepository,baseRepository -q '{author:.author.login,url:.url,repo:.baseRepository.nameWithOwner}'
```

Skip the profile pass for `BramVR` unless the user explicitly asks.

## Source Order

1. Local contributor notes, if a project has them:

```bash
find ~/Projects -path '*/contributors/*' -type f 2>/dev/null | rg -i "<login>|<name>|<email>"
```

If a contributor file matches, read only:

- `Identity`
- `Signals`
- `Context`
- `Evidence`
- `Notes`

2. Live GitHub public profile:

```bash
gh api "users/<login>" --jq '{login,name,company,location,bio,blog,twitter_username,created_at,followers,following,public_repos}'
```

3. Target-repo activity:

```bash
gh search prs --repo <owner/repo> --author <login> --state merged --limit 20 --json number,title,mergedAt,url
gh search prs --repo <owner/repo> --author <login> --state open --limit 20 --json number,title,updatedAt,url
gh search issues --repo <owner/repo> --author <login> --state open --limit 20 --json number,title,updatedAt,url
gh api "repos/<owner>/<repo>/collaborators/<login>/permission" --jq '{permission,user:.user.login}' 2>/dev/null || true
```

4. Local git evidence when useful:

```bash
git log --all --author="<login>" --since="90 days ago" --oneline --decorate --no-merges | head -40
git shortlog -sne --all | rg -i "<login>|<name>|<email>"
```

## Output

Keep it short. Add this block near the top of a PR review:

```text
Author context: @login
- Who: <name/company/location/role, confidence>
- Activity: <merged/open PRs, issues, reviews/commits if known>
- Signal: <maintainer/candidate/drive-by/vendor/security/unknown>
- Risk: <review-load, broad PRs, low history, company-governance, none obvious>
```

Do not quote private phone/email/contact details unless Bram asks. Separate employer from company-directed work; almost everyone has an employer.

## Contributor Notes

After a merge/rejection/close/review, add a note only if it creates future review value: first good merge, unusually strong work, repeated quality problems, slop, no-repro churn, exceptional responsiveness, lack of follow-through, or identity confirmation.

Keep notes terse, factual, dated, and linked. Do not record ordinary noise. If no contributor-note store is configured, report the suggested note instead of inventing a storage location.
