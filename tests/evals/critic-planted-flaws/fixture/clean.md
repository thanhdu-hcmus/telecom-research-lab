# Synthetic clean control
[A1] Perfect instantaneous CSI explicitly assumed for a theoretical upper bound; estimation overhead ignored and robustness untested, listed as limitations.
[SIC] fixed users g1<g2, a1=0.8,a2=0.2. Weak user decodes own while treating strong as interference; strong decodes weak then own with perfect SIC. Require a1>gamma1*a2.
[NOISE] Noise variance=10**((-94-30)/10) W via tested conversion helper.
[CONVEX] Bilinear xy Hessian has eigenvalues +1,-1; no joint convexity claim. Coordinate heuristic has no global guarantee.
[FAIR] NOMA and OMA total power=1 W, same bandwidth, channels, CSI and channel seeds.
[COST] Dense inversion O(n^3), memory O(n^2). Multiple simulation seeds required.
