# localflow-bin

Arch Linux packaging for the prebuilt x86_64 release of
[LocalFlow](https://github.com/radiumcoders/localflow), a native dictation app
with local speech recognition and text cleanup. Maintained by
[Alp on AUR](https://aur.archlinux.org/account/Alp).

## Install

Once published to AUR:

```sh
yay -S localflow-bin
# or: paru -S localflow-bin
```

To build the recipe directly:

```sh
makepkg -si
```

The package extracts the versioned upstream AppImage at build time, installs
`/usr/bin/localflow`, its desktop entry and icon, and upstream licensing
information. Running it needs no FUSE. LocalFlow is proprietary; the upstream
README contains its license terms. This packaging repository is licensed 0BSD.

Open `localflow` to set up the speech and cleanup models, downloaded per user.
Use `wl-clipboard` and `wtype` on Wayland, or `xclip` and `xdotool` on X11, for
pasting. PipeWire users should install `pipewire-alsa`. A Vulkan driver enables
GPU acceleration. These integrations are optional dependencies in the recipe.

Upstream setup creates `~/.local/share/localflow/app/localflow` and a per-user
desktop entry that can override the system entry. That copy is outside pacman's
ownership and can remain at an older version after an AUR upgrade. Bind shortcuts
to `/usr/bin/localflow` (`toggle`, or `start`/`stop`) and launch that path to use
the packaged version. After onboarding, you can remove the generated
`~/.local/share/applications/localflow.desktop` to use the system desktop entry;
setup can recreate it. Removing the package leaves user models, settings and
that upstream-created copy intact.

## Automation

The workflows follow the sibling `ghostex-bin` repository:

1. **Check upstream releases** runs hourly at minute 23, or manually. It accepts
   newer stable `vX.Y.Z` releases with exactly one expected Linux AppImage.
   Drafts, prereleases, downgrades, unexpected versions and download URLs are
   rejected. Incomplete releases fail for retry on the next run.
2. The updater downloads the AppImage, verifies GitHub's SHA-256 asset digest
   when supplied, pins its SHA-256 and the versioned README checksum, and resets
   `pkgrel` to 1. The README is included because it holds the application's
   license terms; third-party licenses are included in the AppImage.
3. A clean Arch Docker container builds, checks and installs the package,
   verifies CLI help/version and shared libraries, reinstalls it, removes it,
   and regenerates `.SRCINFO`. Any namcap error fails validation; warnings are
   retained in `.artifacts/namcap.log`.
4. On success, the workflow opens an update PR and immediately squash-merges it,
   then explicitly dispatches **Publish to AUR**. This matches the sibling's
   automatic publishing policy; no human review precedes release updates.
5. Publishing runs validation again and pushes only `PKGBUILD`, `.SRCINFO` and
   the packaging `LICENSE` to `localflow-bin.git` on AUR. Unchanged recipes and
   superseded main-branch workflows skip publishing. Human PRs run **Check
   package** independently.

`GITHUB_TOKEN` pushes do not start another push workflow, which is why updating
explicitly dispatches publishing after merging. Existing update PRs are left
intact, including closed PRs, so rejected updates are not repeatedly reopened.

## Repository setup

Host this directory in a GitHub repository with default branch `main`.

- Enable Actions and **Allow GitHub Actions to create and approve pull requests**
  in repository Actions settings. Enable squash merging. Branch protections must
  permit the update workflow's immediate merge if automatic updates are wanted.
- Create a GitHub environment named `aur` and add `AUR_SSH_PRIVATE_KEY` containing
  the publishing private key. Register its public key on the AUR maintainer
  account, which must have permission to maintain `localflow-bin`. For a new AUR
  package, the first push creates its repository.
- `.ci/aur-known-hosts` pins the AUR SSH host key inherited from the sibling
  repository. Verify it against [AUR's published fingerprints](https://aur.archlinux.org/)
  when configuring or rotating publishing credentials.
- Push the initial repository to `main`, or run **Publish to AUR** manually.

The packaging repository is hosted at [alp82/localflow-bin](https://github.com/alp82/localflow-bin).
The publishing key is stored in the GitHub environment secret; no private keys
are committed to this repository.

## Maintenance and validation

Requires Python 3, Git and Docker:

```sh
python3 -m unittest discover -s tests
python3 scripts/update.py
bash scripts/check.sh --refresh-srcinfo
```

For an unchanged recipe, `bash scripts/check.sh` additionally checks that the
committed `.SRCINFO` matches `makepkg --printsrcinfo`. On Arch, metadata alone
can be regenerated with `makepkg --printsrcinfo > .SRCINFO`.

Outputs, including an installable package, are in `.artifacts/`:

```sh
sudo pacman -U .artifacts/localflow-bin-*.pkg.tar.zst
```

Automated validation covers packaging and headless CLI behavior. GUI rendering,
microphone recording, downloaded models, GPU operation and desktop pasting need
interactive testing.

`pkgver` follows upstream; increment `pkgrel` for a packaging change to the same
version. Commit `PKGBUILD` and generated `.SRCINFO` together. For a bad update,
revert its commit on `main` to publish the previous recipe; installed users may
need an explicit downgrade (`pacman -U`) because AUR helpers generally do not
select older versions automatically. Watch Actions failures, AUR comments and
out-of-date flags.
