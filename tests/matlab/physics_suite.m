function physics_suite
s=simkit.streams(312); n=400000;
assert(abs(simkit.dbmToWatt(30)-1)<1e-12);
assert(abs(simkit.wattToDbm(.001))<1e-12);
assert(abs(simkit.noiseWatt(1,0)-simkit.dbmToWatt(-174))<1e-25);
h=simkit.rayleigh(s.channel,[n,1]); g=abs(h).^2;
assert(abs(mean(g)-1)<.01);
z=randn(s.noise,n,1);
for rho=[1,2,4]
 p=.5*erfc(sqrt(rho)); got=mean(1+z/sqrt(2*rho)<0); assert(abs(got-p)<4*sqrt(p*(1-p)/n));
 p=-expm1(-1/rho); got=mean(g*rho<1); assert(abs(got-p)<4*sqrt(p*(1-p)/n));
 v=log2(1+rho*g); theory=exp(1/rho)*expint(1/rho)/log(2); assert(abs(mean(v)-theory)<4*std(v)/sqrt(n));
end
gains=sort(-log(rand(s.channel,n,2)),2);
for rho=[2,10,30]
 [weak,sic,strong]=simkit.nomaSinr(gains(:,1),gains(:,2),rho,.8,0);
 [pw,ps]=simkit.nomaOutage(rho,.8,1,1);
 assert(abs(mean(weak<1)-pw)<4*sqrt(pw*(1-pw)/n));
 assert(abs(mean(sic<1 | strong<1)-ps)<4*sqrt(ps*(1-ps)/n));
end
sizes=[64,128,256,512]; powers=zeros(size(sizes));
for i=1:numel(sizes)
 g=simkit.rayleigh(s.channel,[4000,sizes(i)]); h=simkit.rayleigh(s.channel,[4000,sizes(i)]);
 powers(i)=mean(abs(simkit.risCascade(g,h)).^2);
end
fit=polyfit(log(sizes),log(powers),1);assert(fit(1)>=1.9 && fit(1)<=2.1);
a=simkit.streams(10);b=simkit.streams(10);assert(isequal(simkit.rayleigh(a.channel,[10,1]),simkit.rayleigh(b.channel,[10,1])));
fprintf('MATLAB_PHYSICS_PASS slope=%.6f\n',fit(1));
end
