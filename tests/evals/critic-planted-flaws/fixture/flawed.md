# Synthetic flawed model
[A1] The optimizer observes exact instantaneous channels; assumptions list mentions only Rayleigh fading and does not declare CSI or estimation.
[SIC] g1<g2; a1=0.2,a2=0.8; weak user1 first decodes stronger user's message, strong user2 never decodes user1.
[NOISE] SINR=P*g/(-94); noise variance is taken directly from -94 dBm.
[CONVEX] maximize x*y on x,y in [0,1] is claimed a convex optimization problem.
[FAIR] Proposed total power=1 W; OMA baseline total power=0.1 W, same bandwidth.
[COST] Dense n-by-n matrix inversion each iteration claimed O(n).
