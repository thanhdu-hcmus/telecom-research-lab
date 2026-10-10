# Monte Carlo standards
Target <=1% relative CI halfwidth for averages. Use t intervals across independent
replicates or paired/bootstrap methods matching the sampling design. Outage/BER
needs >=100 observed events at the lowest plotted probability; zero events is
an upper bound, never proof of zero outage. Exact/Wilson binomial intervals.
Record channel/noise/initialization streams, separate training seeds from channel
seeds, and reuse identical channel draws for every method in a figure. Vectorize;
parallelize only independent seeds and record per-configuration runtime.
Save raw data for independent recomputation, constraints, convergence and sensitivities.
