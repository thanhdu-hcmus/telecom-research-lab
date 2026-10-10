function h=rician(s,shape,K,los)
assert(K>=0); h=sqrt(K/(K+1))*los+sqrt(1/(K+1))*simkit.rayleigh(s,shape);
end
