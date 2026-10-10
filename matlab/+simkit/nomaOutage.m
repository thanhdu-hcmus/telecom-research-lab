function [pw,ps]=nomaOutage(rho,a,Rw,Rs)
b=1-a; gw=2^Rw-1; gs=2^Rs-1;
if a<=gw*b, pw=1; ps=1; return; end
tw=gw/(rho*(a-gw*b)); ts=max(tw,gs/(rho*b));
pw=-expm1(-2*tw); ps=(-expm1(-ts))^2;
end
