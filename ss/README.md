# MCC frontend before/after screenshots

- `mcc-dashboard-before.png` — MCC dashboard served from `origin/main` at commit `f7108f7`.
- `mcc-dashboard-after.png` — MCC dashboard served from `Ayann/Issue-178_Improve_MCC_Frontend_test_coverage` at commit `93cd06d`.

Both images were captured by headless Chrome at 1600x1000 after the Vite apps returned HTTP 200. The rendered DOM was checked before capture:

- Before: contains `Live Sessions`.
- After: contains `Sessions`.
- Both pages contain the MCC title, Dashboard, and Login markers.

The PNGs were verified as valid 1600x1000 images and have different SHA-256 hashes, confirming they are separate captures of the two app versions rather than duplicate/random placeholder files.
