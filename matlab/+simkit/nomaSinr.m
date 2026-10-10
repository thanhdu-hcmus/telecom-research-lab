function [weak,sic,strong]=nomaSinr(g1,g2,rho,a,residual)
assert(a>0 && a<1 && rho>0 && residual>=0 && residual<=1); b=1-a;
weak=a*rho*g1./(b*rho*g1+1); sic=a*rho*g2./(b*rho*g2+1); strong=b*rho*g2./(residual*a*rho*g2+1);
end
