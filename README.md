# Jingyi (Joy) Zhang - Academic Homepage

A responsive, multi-page academic website built with the existing AcademicPages / Jekyll framework and designed for GitHub Pages. Its structure follows the restrained pattern used by many AcademicPages sites: a shared profile sidebar and separate About, Research, Projects, Awards, and Teaching pages.

## Edit the content

All public-facing text and links live in one file: `_data/profile.yml`.

- **Biography:** edit the `about` paragraphs.
- **Homepage news:** add or edit dated items under `news`; the contact line reuses `links.email_label`.
- **Research:** add or edit entries under `research`.
- **Computational projects:** add or edit entries under `projects`.
- **Honors and awards:** add or edit verified entries under `awards`. A featured item uses `featured`, `url`, and a `media` list containing each image's `preview`, `alt`, `width`, and `height`.
- **Teaching:** add or edit course cards under `teaching` and their term chips under each course's `terms`; Thank-a-Teacher materials live under `thank_a_teacher`, and the compact GRA entry is configured under `gra_experience`.
- **Profile links:** update `links`. Empty links are automatically omitted from the sidebar.

The shared page structure is in `_layouts/academic_home.html`; the visual design is in `assets/css/academic-home.css`. The route files are `index.html`, `research.html`, `projects.html`, `awards.html`, and `teaching.html`.

## Replace the profile photo

Replace the image referenced by `portrait.path` in `_data/profile.yml`, or add a new JPEG under `images/` and update that path. Keep `portrait.alt` accurate, remove camera metadata, and use HTML width and height values matching the image's intrinsic dimensions in `_layouts/academic_home.html`.

## Update Thank-a-Teacher materials

Put public, anonymized certificate and letter images in `images/teaching/`. For each carousel entry under `thank_a_teacher.documents` in `_data/profile.yml`, update the `label`, `attribution`, `preview`, and `alt` fields. Remove student names, email addresses, and other identifying information unless you have permission to publish them; preserve the private originals outside the repository.

## CV

The public homepage intentionally does not display or link a CV. The template's sample CV pages are disabled and can be restored later when a public CV is ready.

## Preview locally

Ruby and Bundler are required. From the repository root:

```bash
bundle config set --local path 'vendor/bundle'
bundle install
bundle exec jekyll serve --livereload
```

Open `http://127.0.0.1:4000/`. To run the same production build used for verification:

```bash
JEKYLL_ENV=production bundle exec jekyll build --strict_front_matter
```

## GitHub Pages deployment

This repository is named `JoyZhang25.github.io`, so GitHub Pages can publish it at `https://JoyZhang25.github.io`. In **Settings -> Pages**, select **Deploy from a branch**, then choose the default branch and the repository root. Each later push to that branch triggers a fresh Jekyll build and deployment.

Before every public push, rebuild the site and run the privacy audit:

```bash
JEKYLL_ENV=production bundle exec jekyll build --strict_front_matter
python3 scripts/prepublish_privacy_audit.py
```

The audit blocks unapproved PDFs, unknown email addresses, common credentials and private keys, local home-directory paths, sensitive filenames, unexpected generated PDFs, and camera/date metadata in public images. It deliberately requires a manual page-by-page review before a new PDF is added to the approved list near the top of the script.

No analytics, tracking scripts, cookies, or contact forms are used. The only client-side JavaScript is the small, dependency-free image-carousel controller used for the award and Thank-a-Teacher displays.
