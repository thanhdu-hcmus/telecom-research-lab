# Telecom conventions

Vectors bold lowercase, matrices bold uppercase; Hermitian H, transpose T.
CN(0,1) has real/imaginary variance 1/2. State channel normalizations explicitly.
Parameter powers dBm; computation W. Noise dBm=-174+10 log10(B_Hz)+NF_dB.
Use tested simkit helpers, never inline conversion. Split reference path loss and
small-scale fading. State reference distance, exponent, frequency and geometry.
Rayleigh/Rician K/LoS geometry or other distribution must be explicit. Define RIS
cascade, phase bits, modulus/amplitude coupling, passive/active/STAR, spacing and
aperture. N squared scaling assumes increasing aperture, not fixed physical area.
Declare perfect/imperfect/statistical CSI and estimation overhead; specify error
model and robustness. Define NOMA ordering/pairing, power constraints and residual
SIC. State convexity by block; distinguish relaxation from exact formulation.
AO/SCA/SDR/manifold/DRL guarantees, randomization and complexity need evidence.
