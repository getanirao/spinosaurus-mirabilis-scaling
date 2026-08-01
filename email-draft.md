# Cold email draft — Evan Johnson-Ransom

**Recipient:** Evan Johnson-Ransom, PhD candidate, Integrative Biology, University of Chicago (Sereno Lab)
**Send window:** Tuesday morning

---

**Subject:** CFD screening study of the Spinosaurus mirabilis sagittal crest — feedback welcome

Hi Dr. Johnson-Ransom,

I'm a high school student doing independent CFD work, and your February 2026 Science paper on the scimitar-crested Spinosaurus species made me think you'd be the right person to ask for a quick look at a hobby project I've been building. I'm especially interested in your cranial biomechanics work on theropod skulls.

I put together a small, open-source steady RANS screening study of the S. mirabilis head at 2 m/s in water (k-omega SST, ~1.2M cells), using a publicly available artist reconstruction as an idealized stand-in for the holotype geometry. My specific question: does an edge-on sagittal crest like this act primarily as a lateral loading surface under yaw, rather than as an axial drag source at zero yaw?

I want to be upfront about the current state — I'm at the stage where I'm more aware of my errors than my results:

- My force-and-moment monitor ended up with zero assigned faces, so I have no integrated drag/lift number at all.
- The pressure residual never converged below ~5.9e-3 over 1,000 iterations.
- I have no control run (crest-ablated, or a comparison against an S. aegyptiacus head), and no grid-independence check.

I deliberately documented all of these limitations in the repo rather than hiding them — the honest read right now is that the study shows a plausible mechanism worth testing (crest edge-on → front/back pressure cancellation, with lateral/yaw loading only appearing under sideslip), not a measured result.

The repo is here: https://github.com/getanirao/spinosaurus-mirabilis-scaling

I'd welcome any advice on (1) how a student should set up the far-field boundaries and force monitoring properly in SimScale, and (2) whether a yaw sweep and a crest-ablated control would be the right next experiments, or if you'd recommend a different framing entirely. If you'd prefer, I'm also happy to just keep this on my own time — a quick "wrong direction" note would be genuinely useful.

Thanks for your time,

[Your name]
[Your email]
