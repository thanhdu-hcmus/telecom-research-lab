# MATLAB bridge
Use configured official MCP evaluate_matlab_code or host MATLAB -batch fallback.
Never interpret nonzero shutdown status as success. MATLAB entry functions accept
(seed, output_dir); read scenario parameters from output_dir/params.json with
jsondecode(fileread(...)). matlab_route defaults to mcp; select batch explicitly
in project configuration for the host fallback. Explicit addpath only for reviewed code and +simkit parent;
onCleanup restores the original path. Use save(...,'-v7') or CSV for interoperable
outputs. Pin MATLAB/toolbox versions in manifests. R2021b is installed; avoid
newer syntax without runtime verification. Python and MATLAB streams need not be
bitwise equal; validate shared formulas on fixed input vectors and statistical CIs.
