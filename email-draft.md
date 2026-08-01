# Cold email draft — Evan Johnson-Ransom

**Recipient:** Evan Johnson-Ransom, PhD candidate, Integrative Biology, University of Chicago (Sereno Lab)
**Send window:** Tuesday morning

---

**Subject:** CFD screening study of the Spinosaurus mirabilis sagittal crest — feedback welcome

Hi Dr. Johnson-Ransom,

I'm a high school student doing independent CFD work, and your February 2026 Science paper on the scimitar-crested Spinosaurus species made me think you'd be the right person to ask for a quick look at a hobby project I've been building. I'm especially interested in your cranial biomechanics work on theropod skulls.

I put together a small, open-source steady RANS screening study of the S. mirabilis head at 2 m/s in water (k-omega SST, ~1.2M cells), using a publicly available artist reconstruction as an idealized stand-in for the holotype geometry. My specific question: does an edge-on sagittal crest like this act primarily as a lateral loading surface under yaw, rather than as an axial drag source at zero yaw?

The preliminary integrated result from the latest run: at zero yaw and 2 m/s, the solver reports ~271 N streamwise drag and ~149 N vertical force on the head surface, with lateral force under 10 N. That's consistent with the crest being nearly edge-on to the flow (front/back pressure largely cancels; little axial drag added by the blade), while the non-negligible vertical component hints at where loading does concentrate.

I want to be upfront about how much this number is worth — I'm still at the stage where I'm more aware of my errors than my results:

- The pressure residual only reached ~5.9e-3 over 1,000 iterations, so the force integral is approximate, not tightly converged.
- The force monitor was only wired correctly on the latest run (earlier runs had it misconfigured).
- I have no control run (crest-ablated, or a comparison against an S. aegyptiacus head), and no grid-independence check.

I deliberately documented all of these limitations in the repo rather than hiding them — treat the 271 N figure as a preliminary screening estimate that supports the mechanism worth testing (crest edge-on → front/back pressure cancellation, with lateral/yaw loading only appearing under sideslip), not as a measured result.

The repo is here: https://github.com/getanirao/spinosaurus-mirabilis-scaling

I'd welcome any advice on (1) how a student should set up the far-field boundaries and force monitoring properly in SimScale, and (2) whether a yaw sweep and a crest-ablated control would be the right next experiments, or if you'd recommend a different framing entirely. If you'd prefer, I'm also happy to just keep this on my own time — a quick "wrong direction" note would be genuinely useful.

Thanks for your time,

[Your name]
[Your email]
