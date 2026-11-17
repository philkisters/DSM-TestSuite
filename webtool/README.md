# Nuxt Starter Template

[![Nuxt UI](https://img.shields.io/badge/Made%20with-Nuxt%20UI-00DC82?logo=nuxt&labelColor=020420)](https://ui.nuxt.com)

Use this template to get started with [Nuxt UI](https://ui.nuxt.com) quickly.

- [Live demo](https://starter-template.nuxt.dev/)
- [Documentation](https://ui.nuxt.com/docs/getting-started/installation/nuxt)

<a href="https://starter-template.nuxt.dev/" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://ui.nuxt.com/assets/templates/nuxt/starter-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="https://ui.nuxt.com/assets/templates/nuxt/starter-light.png">
    <img alt="Nuxt Starter Template" src="https://ui.nuxt.com/assets/templates/nuxt/starter-light.png" width="830" height="466">
  </picture>
</a>

> The starter template for Vue is on https://github.com/nuxt-ui-templates/starter-vue.

## Quick Start

```bash [Terminal]
npm create nuxt@latest -- -t ui
```

## Deploy your own

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-name=starter&repository-url=https%3A%2F%2Fgithub.com%2Fnuxt-ui-templates%2Fstarter&demo-image=https%3A%2F%2Fui.nuxt.com%2Fassets%2Ftemplates%2Fnuxt%2Fstarter-dark.png&demo-url=https%3A%2F%2Fstarter-template.nuxt.dev%2F&demo-title=Nuxt%20Starter%20Template&demo-description=A%20minimal%20template%20to%20get%20started%20with%20Nuxt%20UI.)

## Setup

Make sure to install the dependencies:

```bash
pnpm install
```

## Development Server

Start the development server on `http://localhost:3000`:

```bash
pnpm dev
```

## Group challenge overview

The backend group service exposes `getGroupChallengeOverview(groupId)` for
`GET /testsuite/groups/{group_id}/challenge_stats`. It returns camelCase
challenge statistics and first-, second-, and third-place counts for time,
duration, and messages; challenge timestamps are parsed as dates.

## Group selection

The selected group is saved in browser local storage and restored after the
group list loads. If no group is saved, or the saved group is no longer in the
list, the group selector is shown. Clicking the active group in the header
clears the selection and opens the selector again.

## Network fingers

Selecting a peer requests its finger table through the proxy. The network view
shows a blue arrow to each distinct finger destination, including the peer itself
or an unregistered peer. Select another peer or the background to clear the arrows;
select the peer again to refresh its table.

The view also requests the selected peer's image list. Each node shows an image
icon and its last known count, or `?` until a request succeeds. Counts remain
visible when selecting other peers and are refreshed when a peer is selected again.
Peer Details lists the selected peer's last known image IDs and shortened SHA-256
hashes. Use **Load** to fetch image files from that peer; failed images show an
error and can be retried with the same button. Changing peers or refreshing the
image list clears the loaded previews.

Use **Put image** to select a peer, choose a PNG, and preview and send it. The
image ID defaults to the filename and shows its shortened hash; it can be edited.
An acknowledgement means the peer accepted the message; forwarding or storage may
still be in progress.

Enable **Multi upload** to select multiple PNGs. Each filename becomes its image
ID and is shown with a shortened SHA-256 hash, preview, and a randomly assigned
network peer and its shortened hash. Remove individual files with the X button.
Confirm to send the images sequentially and track acknowledgements in the
progress bar. If an upload fails, retry resumes at the failed image.
The selected files appear as a list, and the modal scrolls for large selections.

## Production

Build the application for production:

```bash
pnpm build
```

Locally preview production build:

```bash
pnpm preview
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.

## Renovate integration

Install [Renovate GitHub app](https://github.com/apps/renovate/installations/select_target) on your repository and you are good to go.
